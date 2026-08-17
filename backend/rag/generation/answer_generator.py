"""Query rewriting and grounded answer generation."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, ValidationError

from rag.config import get_rag_config
from rag.generation.json_utils import extract_json_object
from rag.generation.llm_router import completion_json_with_fallback, completion_with_fallback
from rag.schemas import Citation, RagAnswer

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class RewrittenQuery(BaseModel):
    search_query: str


class GroundedResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)


REWRITE_SYSTEM = (
    'You rewrite casual student questions into concise textbook search queries. '
    'Respond with JSON only: {"search_query": "..."}'
)
ANSWER_SYSTEM = (
    "You are a tuition-centre tutor helping a student. Prefer the provided textbook excerpts "
    "when they contain relevant information. Cite them in the citations array when you use them. "
    "If the excerpts are missing or do not contain enough information, answer from general "
    "knowledge for the given grade and subject. When you answer without textbook support, "
    "start with: \"This isn't covered in your textbook, but here's a general explanation:\" "
    "and return an empty citations array. Respond with JSON only matching this schema: "
    '{"answer": "...", "citations": [{"book_id": "...", "chapter": "...", '
    '"section": "...", "page_range": "...", "content_type": "explanation", '
    '"excerpt": "short quote"}]}'
)
GENERAL_KNOWLEDGE_SYSTEM = (
    "You are a tuition-centre tutor helping a student. No textbook excerpts were found for "
    "this question. Answer from general knowledge appropriate for the given grade and subject. "
    "Start with: \"This isn't covered in your textbook, but here's a general explanation:\" "
    "Respond with JSON only: {\"answer\": \"...\", \"citations\": []}"
)


def rewrite_query(raw_query: str) -> tuple[str, str]:
    messages = [
        {"role": "system", "content": REWRITE_SYSTEM},
        {"role": "user", "content": raw_query},
    ]
    try:
        payload, model_used = completion_json_with_fallback(messages, temperature=0.0)
        rewritten = RewrittenQuery.model_validate(payload).search_query.strip()
        if rewritten:
            return rewritten, model_used
    except (ValidationError, ValueError, KeyError):
        pass
    fallback_text, model_used = completion_with_fallback(messages, temperature=0.0)
    return fallback_text.strip() or raw_query, model_used


def _format_context_block(hit: dict) -> str:
    return "\n".join(
        [
            f"[book={hit.get('book_id', '')} chapter={hit.get('chapter', '')} "
            f"section={hit.get('section', '')} pages={hit.get('page_range', '')} "
            f"type={hit.get('content_type', '')}]",
            hit.get("parent_text") or hit.get("content") or "",
        ]
    )


def truncate_excerpt(text: str, limit: int = 500) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    window = cleaned[:limit]
    matches = list(SENTENCE_END.finditer(window))
    if matches:
        return window[: matches[-1].end()].strip()
    last_space = window.rfind(" ")
    if last_space > limit // 2:
        return window[:last_space].strip()
    return window.strip()


def _citation_from_hit(hit: dict) -> Citation:
    excerpt = hit.get("content") or hit.get("parent_text") or ""
    return Citation(
        book_id=hit.get("book_id", ""),
        chapter=hit.get("chapter", ""),
        section=hit.get("section", ""),
        page_range=hit.get("page_range", ""),
        content_type=hit.get("content_type", "explanation"),
        excerpt=truncate_excerpt(excerpt),
    )


def _extractive_answer(context_blocks: list[dict]) -> RagAnswer:
    citations = [_citation_from_hit(block) for block in context_blocks[:3]]
    excerpts = [citation.excerpt.strip() for citation in citations if citation.excerpt.strip()]
    answer = "I found these relevant textbook excerpts:\n\n" + "\n\n".join(
        f"{idx}. {excerpt}" for idx, excerpt in enumerate(excerpts, start=1)
    )
    return RagAnswer(answer=answer, citations=citations, model_used="retrieval-only")


def _no_textbook_message() -> RagAnswer:
    return RagAnswer(
        answer=(
            "I couldn't find relevant material in your textbook for that question. "
            "Try rephrasing or specifying the chapter."
        ),
        model_used="none",
    )


def _parse_grounded_response(raw: str) -> GroundedResponse | None:
    payload = extract_json_object(raw)
    if payload is None:
        return None
    try:
        return GroundedResponse.model_validate(payload)
    except ValidationError:
        return None


def _call_answer_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    context_blocks: list[dict],
) -> RagAnswer:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    model_used = "none"
    try:
        raw, model_used = completion_with_fallback(messages, temperature=0.2)
        parsed = _parse_grounded_response(raw)
        if parsed is not None:
            return RagAnswer(
                answer=parsed.answer.strip(),
                citations=parsed.citations,
                model_used=model_used,
            )
    except Exception:
        pass

    if context_blocks:
        return _extractive_answer(context_blocks)
    return _no_textbook_message()


def generate_answer(
    question: str,
    context_blocks: list[dict],
    *,
    grade: int,
    subject: str,
) -> RagAnswer:
    cfg = get_rag_config()

    if not context_blocks:
        if not cfg.generation_enabled:
            return _no_textbook_message()
        user_prompt = f"Grade: {grade}\nSubject: {subject}\nQuestion: {question}"
        return _call_answer_llm(
            system_prompt=GENERAL_KNOWLEDGE_SYSTEM,
            user_prompt=user_prompt,
            context_blocks=[],
        )

    if not cfg.generation_enabled:
        return _extractive_answer(context_blocks)

    context_text = "\n\n".join(_format_context_block(block) for block in context_blocks)
    user_prompt = (
        f"Grade: {grade}\n"
        f"Subject: {subject}\n"
        f"Question: {question}\n\n"
        f"Textbook excerpts:\n{context_text}"
    )
    return _call_answer_llm(
        system_prompt=ANSWER_SYSTEM,
        user_prompt=user_prompt,
        context_blocks=context_blocks,
    )
