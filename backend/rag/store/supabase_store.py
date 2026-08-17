"""Supabase Postgres + pgvector storage and hybrid retrieval."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

import psycopg2
from psycopg2 import extras

from rag.config import get_rag_config
from rag.schemas import ChunkRecord


class RagStoreError(RuntimeError):
    pass


_GROUNDING_CONTENT_FILTER = "c.content_type NOT IN ('reference', 'exercise')"


def _connection_error_message(database_url: str, exc: Exception) -> str:
    host = urlparse(database_url).hostname or "configured host"
    message = f"Could not connect to RAG database host '{host}': {exc}"
    if host.startswith("db.") and host.endswith(".supabase.co"):
        message += (
            " Supabase direct database hosts are IPv6-only for many projects. "
            "Use the Supabase pooler URI from Project Settings > Database > "
            "Connection string for RAG_DATABASE_URL instead."
        )
    return message


@contextmanager
def _connection():
    cfg = get_rag_config()
    if not cfg.database_url:
        raise RagStoreError("RAG_DATABASE_URL is not configured")
    try:
        conn = psycopg2.connect(cfg.database_url)
    except psycopg2.OperationalError as exc:
        raise RagStoreError(_connection_error_message(cfg.database_url, exc)) from exc
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def get_book_by_hash(pdf_hash: str) -> dict[str, Any] | None:
    with _connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    b.id::text AS id,
                    b.pdf_hash,
                    b.title,
                    b.subject,
                    b.grade,
                    b.resource_id,
                    COUNT(c.id) AS chunk_count
                FROM rag_books b
                LEFT JOIN rag_chunks c ON c.book_id = b.id
                WHERE b.pdf_hash = %s
                GROUP BY b.id
                """,
                (pdf_hash,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None


def create_book(
    pdf_hash: str,
    title: str,
    subject: str,
    grade: int,
    resource_id: int | None = None,
) -> str:
    book_id = str(uuid4())
    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rag_books (id, pdf_hash, title, subject, grade, resource_id)
                VALUES (%s::uuid, %s, %s, %s, %s, %s)
                """,
                (book_id, pdf_hash, title, subject, grade, resource_id),
            )
    return book_id


def delete_book_chunks(book_id: str) -> None:
    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM rag_parent_sections WHERE book_id = %s::uuid", (book_id,))
            cursor.execute("DELETE FROM rag_chunks WHERE book_id = %s::uuid", (book_id,))


def index_chunks(chunks: list[ChunkRecord], embeddings: list[list[float]]) -> int:
    if len(chunks) != len(embeddings):
        raise RagStoreError("Chunk/embedding count mismatch")

    parent_map: dict[tuple[str, str, str, str], str] = {}
    indexed = 0

    with _connection() as conn:
        with conn.cursor() as cursor:
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                parent_key = (
                    chunk.book_id,
                    chunk.chapter,
                    chunk.section,
                    chunk.page_range,
                )
                parent_id = parent_map.get(parent_key)
                if parent_id is None:
                    parent_id = str(uuid4())
                    parent_map[parent_key] = parent_id
                    cursor.execute(
                        """
                        INSERT INTO rag_parent_sections
                            (id, book_id, chapter, section, page_range, full_text, content_type)
                        VALUES (%s::uuid, %s::uuid, %s, %s, %s, %s, %s)
                        """,
                        (
                            parent_id,
                            chunk.book_id,
                            chunk.chapter,
                            chunk.section,
                            chunk.page_range,
                            chunk.parent_text,
                            chunk.content_type,
                        ),
                    )

                chunk_id = str(uuid4())
                vector_literal = _vector_literal(embedding)
                cursor.execute(
                    """
                    INSERT INTO rag_chunks (
                        id, book_id, parent_section_id, chunk_index, content, embedding,
                        content_type, subject, grade, chapter, section, page_range, search_vector
                    ) VALUES (
                        %s::uuid, %s::uuid, %s::uuid, %s, %s, %s::vector, %s, %s, %s, %s, %s, %s,
                        to_tsvector('english', %s)
                    )
                    """,
                    (
                        chunk_id,
                        chunk.book_id,
                        parent_id,
                        chunk.chunk_index,
                        chunk.content,
                        vector_literal,
                        chunk.content_type,
                        chunk.subject,
                        chunk.grade,
                        chunk.chapter,
                        chunk.section,
                        chunk.page_range,
                        chunk.content,
                    ),
                )
                indexed += 1
    return indexed


def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    *,
    grade: int,
    subject: str,
    chapter: str | None = None,
) -> list[dict[str, Any]]:
    cfg = get_rag_config()
    filter_sql = f"c.grade = %s AND c.subject = %s AND {_GROUNDING_CONTENT_FILTER}"
    filter_params: list[Any] = [grade, subject]
    if chapter:
        filter_sql += " AND c.chapter ILIKE %s"
        filter_params.append(f"%{chapter.strip()}%")

    vector_literal = _vector_literal(query_embedding)
    limit = cfg.retrieval_top_k
    rrf_k = cfg.hybrid_rrf_k

    sql = f"""
    WITH vector_hits AS (
        SELECT
            c.id::text AS chunk_id,
            c.content,
            c.content_type,
            c.chapter,
            c.section,
            c.page_range,
            c.book_id::text AS book_id,
            p.full_text AS parent_text,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector) AS vector_rank
        FROM rag_chunks c
        JOIN rag_parent_sections p ON p.id = c.parent_section_id
        WHERE {filter_sql}
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
    ),
    keyword_hits AS (
        SELECT
            c.id::text AS chunk_id,
            c.content,
            c.content_type,
            c.chapter,
            c.section,
            c.page_range,
            c.book_id::text AS book_id,
            p.full_text AS parent_text,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(c.search_vector, plainto_tsquery('english', %s)) DESC
            ) AS keyword_rank
        FROM rag_chunks c
        JOIN rag_parent_sections p ON p.id = c.parent_section_id
        WHERE {filter_sql}
          AND c.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank_cd(c.search_vector, plainto_tsquery('english', %s)) DESC
        LIMIT %s
    ),
    fused AS (
        SELECT
            COALESCE(v.chunk_id, k.chunk_id) AS chunk_id,
            COALESCE(v.content, k.content) AS content,
            COALESCE(v.content_type, k.content_type) AS content_type,
            COALESCE(v.chapter, k.chapter) AS chapter,
            COALESCE(v.section, k.section) AS section,
            COALESCE(v.page_range, k.page_range) AS page_range,
            COALESCE(v.book_id, k.book_id) AS book_id,
            COALESCE(v.parent_text, k.parent_text) AS parent_text,
            COALESCE(1.0 / ({rrf_k} + v.vector_rank), 0) +
            COALESCE(1.0 / ({rrf_k} + k.keyword_rank), 0) AS rrf_score
        FROM vector_hits v
        FULL OUTER JOIN keyword_hits k USING (chunk_id)
    )
    SELECT * FROM fused ORDER BY rrf_score DESC LIMIT %s
    """

    params = [
        vector_literal,
        *filter_params,
        vector_literal,
        limit,
        query_text,
        *filter_params,
        query_text,
        query_text,
        limit,
        limit,
    ]

    with _connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


def keyword_search(
    query_text: str,
    *,
    grade: int,
    subject: str,
    chapter: str | None = None,
) -> list[dict[str, Any]]:
    cfg = get_rag_config()
    filter_sql = f"c.grade = %s AND c.subject = %s AND {_GROUNDING_CONTENT_FILTER}"
    filter_params: list[Any] = [grade, subject]
    if chapter:
        filter_sql += " AND c.chapter ILIKE %s"
        filter_params.append(f"%{chapter.strip()}%")

    sql = f"""
    SELECT
        c.id::text AS chunk_id,
        c.content,
        c.content_type,
        c.chapter,
        c.section,
        c.page_range,
        c.book_id::text AS book_id,
        p.full_text AS parent_text,
        ts_rank_cd(c.search_vector, plainto_tsquery('english', %s)) AS keyword_score
    FROM rag_chunks c
    JOIN rag_parent_sections p ON p.id = c.parent_section_id
    WHERE {filter_sql}
      AND c.search_vector @@ plainto_tsquery('english', %s)
    ORDER BY keyword_score DESC
    LIMIT %s
    """

    params = [
        query_text,
        *filter_params,
        query_text,
        cfg.retrieval_top_k,
    ]

    with _connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
