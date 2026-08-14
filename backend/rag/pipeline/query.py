"""Student query pipeline: rewrite → retrieve → generate."""

from __future__ import annotations

from rag.cache.redis_cache import get_cached_answer, set_cached_answer
from rag.config import get_rag_config
from rag.embedding.gemini_embedder import embed_query
from rag.generation.answer_generator import generate_answer, rewrite_query
from rag.schemas import QueryRequest, QueryResponse, RagAnswer
from rag.store.supabase_store import RagStoreError, hybrid_search


def answer_question(request: QueryRequest) -> QueryResponse:
    cfg = get_rag_config()
    if not cfg.database_url:
        return QueryResponse(
            answer=(
                "The textbook assistant is not fully configured yet. Please ask your "
                "teacher to index course PDFs first."
            ),
            model_used="none",
        )

    cached = get_cached_answer(request.query, grade=request.grade, subject=request.subject)
    if cached:
        return QueryResponse(
            answer=cached.answer,
            citations=cached.citations,
            model_used=cached.model_used,
            cached=True,
            rewritten_query=cached.rewritten_query,
        )

    try:
        rewritten, rewrite_model = rewrite_query(request.query)
        query_embedding = embed_query(rewritten)
        hits = hybrid_search(
            query_embedding,
            rewritten,
            grade=request.grade,
            subject=request.subject,
            chapter=request.chapter,
        )
        rag_answer = generate_answer(
            request.query,
            hits,
            grade=request.grade,
            subject=request.subject,
        )
        rag_answer.rewritten_query = rewritten
        if rag_answer.model_used == "none":
            rag_answer.model_used = rewrite_model
        set_cached_answer(request.query, rag_answer, grade=request.grade, subject=request.subject)
        return QueryResponse(
            answer=rag_answer.answer,
            citations=rag_answer.citations,
            model_used=rag_answer.model_used,
            cached=False,
            rewritten_query=rewritten,
        )
    except RagStoreError as exc:
        return QueryResponse(answer=str(exc), model_used="none")
