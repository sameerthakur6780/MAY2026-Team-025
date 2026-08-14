"""Query rewriting and grounded answer generation."""

from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from rag.generation.llm_router import completion_json_with_fallback, completion_with_fallback
from rag.schemas import Citation, RagAnswer


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
    "You are a tuition-centre tutor. Answer ONLY using the provided textbook excerpts. "
    "If the excerpts do not contain enough information, say you could not find it in the "
    "textbook and suggest what chapter to check. Respond with JSON only matching this "
    'schema: {"answer": "...", "citations": [{"book_id": "...", "chapter": "...", '
    '"section": "...", "page_range": "...", "content_type": "explanation", '
    '"excerpt": "short quote"}]}'
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


def generate_answer(
    question: str,
    context_blocks: list[dict],
    *,
    grade: int,
    subject: str,
) -> RagAnswer:
    if not context_blocks:
        return RagAnswer(
            answer=(
                "I couldn't find relevant material in your textbook for that question. "
                "Try rephrasing or specifying the chapter."
            ),
            model_used="none",
        )

    context_text = "\n\n".join(_format_context_block(block) for block in context_blocks)
    user_prompt = (
        f"Grade: {grade}\n"
        f"Subject: {subject}\n"
        f"Question: {question}\n\n"
        f"Textbook excerpts:\n{context_text}"
    )
    messages = [
        {"role": "system", "content": ANSWER_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    try:
        payload, model_used = completion_json_with_fallback(messages, temperature=0.2)
        parsed = GroundedResponse.model_validate(payload)
        return RagAnswer(
            answer=parsed.answer.strip(),
            citations=parsed.citations,
            model_used=model_used,
        )
    except (ValidationError, ValueError, KeyError):
        fallback_text, model_used = completion_with_fallback(messages, temperature=0.2)
        return RagAnswer(answer=fallback_text.strip(), model_used=model_used)
