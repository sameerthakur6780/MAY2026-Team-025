"""Pinecone serverless storage with dense + sparse hybrid retrieval."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any
from uuid import uuid4

from pinecone import Pinecone, ServerlessSpec

from rag.config import get_rag_config
from rag.schemas import ChunkRecord

NS_CHUNKS = "chunks"
NS_PARENTS = "parents"
NS_BOOKS = "books"

_GROUNDING_FILTER: dict[str, Any] = {"content_type": {"$nin": ["reference", "exercise"]}}
_PARENT_TEXT_MAX_CHARS = 30_000
_UPSERT_BATCH = 100
_DELETE_BATCH = 1000


class RagStoreError(RuntimeError):
    pass


def _require_api_key() -> str:
    api_key = get_rag_config().pinecone_api_key.strip()
    if not api_key:
        raise RagStoreError("PINECONE_API_KEY is not configured")
    return api_key


@lru_cache(maxsize=1)
def _pinecone_client() -> Pinecone:
    return Pinecone(api_key=_require_api_key())


@lru_cache(maxsize=1)
def _dense_index():
    cfg = get_rag_config()
    return _pinecone_client().Index(cfg.pinecone_dense_index)


@lru_cache(maxsize=1)
def _sparse_index():
    cfg = get_rag_config()
    return _pinecone_client().Index(cfg.pinecone_sparse_index)


def _placeholder_vector() -> list[float]:
    """Metadata-only records still need a dense vector; Pinecone rejects all-zero vectors."""
    dim = get_rag_config().embedding_dimensions
    values = [0.0] * dim
    values[0] = 1.0
    return values


def _book_record_id(pdf_hash: str) -> str:
    return f"book#{pdf_hash}"


def _chunk_record_id(book_id: str, chunk_index: int) -> str:
    return f"{book_id}#chunk#{chunk_index}"


def _parent_record_id(book_id: str, parent_index: int) -> str:
    return f"{book_id}#parent#{parent_index}"


def _metadata_filter(*, grade: int, subject: str) -> dict[str, Any]:
    return {
        "grade": {"$eq": grade},
        "subject": {"$eq": subject},
        **_GROUNDING_FILTER,
    }


def _chapter_matches(chapter: str | None, metadata: dict[str, Any]) -> bool:
    if not chapter:
        return True
    needle = chapter.strip().casefold()
    if not needle:
        return True
    haystack = str(metadata.get("chapter") or "").casefold()
    return needle in haystack


def _match_to_hit(match: Any) -> dict[str, Any]:
    metadata = dict(getattr(match, "metadata", None) or {})
    return {
        "chunk_id": getattr(match, "id", ""),
        "content": metadata.get("content", ""),
        "content_type": metadata.get("content_type", "explanation"),
        "chapter": metadata.get("chapter", ""),
        "section": metadata.get("section", ""),
        "page_range": metadata.get("page_range", ""),
        "book_id": metadata.get("book_id", ""),
        "parent_id": metadata.get("parent_id", ""),
        "parent_text": "",
    }


def _search_hit_to_dict(hit: Any) -> dict[str, Any]:
    fields = dict(getattr(hit, "fields", None) or getattr(hit, "metadata", None) or {})
    chunk_id = getattr(hit, "_id", None) or getattr(hit, "id", "")
    return {
        "chunk_id": chunk_id,
        "content": fields.get("content", ""),
        "content_type": fields.get("content_type", "explanation"),
        "chapter": fields.get("chapter", ""),
        "section": fields.get("section", ""),
        "page_range": fields.get("page_range", ""),
        "book_id": fields.get("book_id", ""),
        "parent_id": fields.get("parent_id", ""),
        "parent_text": "",
    }


def _attach_parent_text(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent_ids = sorted({hit["parent_id"] for hit in hits if hit.get("parent_id")})
    if not parent_ids:
        return hits

    fetched = _dense_index().fetch(ids=parent_ids, namespace=NS_PARENTS)
    vectors = getattr(fetched, "vectors", None) or {}
    parent_text_by_id = {
        parent_id: dict(getattr(vector, "metadata", None) or {}).get("full_text", "")
        for parent_id, vector in vectors.items()
    }
    for hit in hits:
        hit["parent_text"] = parent_text_by_id.get(hit.get("parent_id", ""), "")
    return hits


def _rrf_fuse(
    dense_hits: list[dict[str, Any]],
    sparse_hits: list[dict[str, Any]],
    *,
    rrf_k: int,
    limit: int,
) -> list[dict[str, Any]]:
    scores: dict[str, float] = {}
    merged: dict[str, dict[str, Any]] = {}

    for rank, hit in enumerate(dense_hits, start=1):
        chunk_id = hit["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (rrf_k + rank))
        merged.setdefault(chunk_id, hit)

    for rank, hit in enumerate(sparse_hits, start=1):
        chunk_id = hit["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (rrf_k + rank))
        merged.setdefault(chunk_id, hit)

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    results: list[dict[str, Any]] = []
    for chunk_id, score in ordered[:limit]:
        hit = dict(merged[chunk_id])
        hit["rrf_score"] = score
        results.append(hit)
    return results


def _list_ids(*, index, namespace: str, prefix: str) -> list[str]:
    ids: list[str] = []
    for page in index.list(prefix=prefix, namespace=namespace):
        vectors = getattr(page, "vectors", None) or []
        for item in vectors:
            item_id = getattr(item, "id", None)
            if item_id:
                ids.append(item_id)
    return ids


def _delete_ids(*, index, namespace: str, ids: list[str]) -> None:
    for start in range(0, len(ids), _DELETE_BATCH):
        batch = ids[start : start + _DELETE_BATCH]
        if batch:
            index.delete(ids=batch, namespace=namespace)


def ensure_indexes() -> None:
    cfg = get_rag_config()
    _require_api_key()
    pc = _pinecone_client()

    if not pc.has_index(cfg.pinecone_dense_index):
        pc.create_index(
            name=cfg.pinecone_dense_index,
            dimension=cfg.embedding_dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud=cfg.pinecone_cloud, region=cfg.pinecone_region),
        )

    if not pc.has_index(cfg.pinecone_sparse_index):
        pc.create_index_for_model(
            name=cfg.pinecone_sparse_index,
            cloud=cfg.pinecone_cloud,
            region=cfg.pinecone_region,
            embed={
                "model": cfg.pinecone_sparse_model,
                "field_map": {"text": "content"},
            },
        )


def get_book_by_hash(pdf_hash: str) -> dict[str, Any] | None:
    record_id = _book_record_id(pdf_hash)
    fetched = _dense_index().fetch(ids=[record_id], namespace=NS_BOOKS)
    vectors = getattr(fetched, "vectors", None) or {}
    vector = vectors.get(record_id)
    if vector is None:
        return None

    metadata = dict(getattr(vector, "metadata", None) or {})
    return {
        "id": metadata.get("book_id", ""),
        "pdf_hash": metadata.get("pdf_hash", pdf_hash),
        "title": metadata.get("title", ""),
        "subject": metadata.get("subject", ""),
        "grade": metadata.get("grade", 0),
        "resource_id": metadata.get("resource_id"),
        "chunk_count": int(metadata.get("chunk_count") or 0),
    }


def create_book(
    pdf_hash: str,
    title: str,
    subject: str,
    grade: int,
    resource_id: int | None = None,
) -> str:
    book_id = str(uuid4())
    metadata: dict[str, Any] = {
        "book_id": book_id,
        "pdf_hash": pdf_hash,
        "title": title,
        "subject": subject,
        "grade": grade,
        "chunk_count": 0,
    }
    if resource_id is not None:
        metadata["resource_id"] = resource_id

    _dense_index().upsert(
        vectors=[
            {
                "id": _book_record_id(pdf_hash),
                "values": _placeholder_vector(),
                "metadata": metadata,
            }
        ],
        namespace=NS_BOOKS,
    )
    return book_id


def delete_book_chunks(book_id: str) -> None:
    dense = _dense_index()
    sparse = _sparse_index()
    prefix = f"{book_id}#"

    dense_chunk_ids = _list_ids(index=dense, namespace=NS_CHUNKS, prefix=prefix)
    dense_parent_ids = _list_ids(index=dense, namespace=NS_PARENTS, prefix=prefix)
    sparse_chunk_ids = _list_ids(index=sparse, namespace=NS_CHUNKS, prefix=prefix)

    _delete_ids(index=dense, namespace=NS_CHUNKS, ids=dense_chunk_ids)
    _delete_ids(index=dense, namespace=NS_PARENTS, ids=dense_parent_ids)
    _delete_ids(index=sparse, namespace=NS_CHUNKS, ids=sparse_chunk_ids)


def index_chunks(chunks: list[ChunkRecord], embeddings: list[list[float]]) -> int:
    if len(chunks) != len(embeddings):
        raise RagStoreError("Chunk/embedding count mismatch")
    if not chunks:
        return 0

    cfg = get_rag_config()
    dense = _dense_index()
    sparse = _sparse_index()
    book_id = chunks[0].book_id

    parent_map: dict[tuple[str, str, str, str], tuple[str, int]] = {}
    parent_vectors: list[dict[str, Any]] = []
    dense_chunk_vectors: list[dict[str, Any]] = []
    sparse_records: list[dict[str, Any]] = []

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        parent_key = (chunk.book_id, chunk.chapter, chunk.section, chunk.page_range)
        parent_entry = parent_map.get(parent_key)
        if parent_entry is None:
            parent_index = len(parent_map)
            parent_id = _parent_record_id(chunk.book_id, parent_index)
            parent_map[parent_key] = (parent_id, parent_index)
            parent_vectors.append(
                {
                    "id": parent_id,
                    "values": _placeholder_vector(),
                    "metadata": {
                        "book_id": chunk.book_id,
                        "chapter": chunk.chapter,
                        "section": chunk.section,
                        "page_range": chunk.page_range,
                        "content_type": chunk.content_type,
                        "full_text": chunk.parent_text[:_PARENT_TEXT_MAX_CHARS],
                    },
                }
            )
        else:
            parent_id, _parent_index = parent_entry

        chunk_id = _chunk_record_id(chunk.book_id, chunk.chunk_index)
        chunk_metadata = {
            "book_id": chunk.book_id,
            "parent_id": parent_id,
            "content": chunk.content,
            "content_type": chunk.content_type,
            "subject": chunk.subject,
            "grade": chunk.grade,
            "chapter": chunk.chapter,
            "section": chunk.section,
            "page_range": chunk.page_range,
            "chunk_index": chunk.chunk_index,
        }
        dense_chunk_vectors.append(
            {
                "id": chunk_id,
                "values": embedding,
                "metadata": chunk_metadata,
            }
        )
        sparse_records.append(
            {
                "_id": chunk_id,
                "content": chunk.content,
                **chunk_metadata,
            }
        )

    for start in range(0, len(parent_vectors), _UPSERT_BATCH):
        dense.upsert(vectors=parent_vectors[start : start + _UPSERT_BATCH], namespace=NS_PARENTS)

    for start in range(0, len(dense_chunk_vectors), _UPSERT_BATCH):
        dense.upsert(vectors=dense_chunk_vectors[start : start + _UPSERT_BATCH], namespace=NS_CHUNKS)

    for start in range(0, len(sparse_records), _UPSERT_BATCH):
        sparse.upsert_records(
            namespace=NS_CHUNKS,
            records=sparse_records[start : start + _UPSERT_BATCH],
        )

    book_lookup = dense.fetch_by_metadata(
        filter={"book_id": {"$eq": book_id}},
        namespace=NS_BOOKS,
        limit=1,
    )
    book_vectors = getattr(book_lookup, "vectors", None) or {}
    if book_vectors:
        book_record_id = next(iter(book_vectors))
        dense.update(
            id=book_record_id,
            set_metadata={"chunk_count": len(chunks)},
            namespace=NS_BOOKS,
        )

    return len(chunks)


def _dense_search(
    query_embedding: list[float],
    *,
    grade: int,
    subject: str,
    chapter: str | None,
    top_k: int,
) -> list[dict[str, Any]]:
    response = _dense_index().query(
        vector=query_embedding,
        top_k=top_k,
        namespace=NS_CHUNKS,
        filter=_metadata_filter(grade=grade, subject=subject),
        include_metadata=True,
    )
    hits = [_match_to_hit(match) for match in getattr(response, "matches", None) or []]
    if chapter:
        hits = [hit for hit in hits if _chapter_matches(chapter, hit)]
    return hits


def _sparse_search(
    query_text: str,
    *,
    grade: int,
    subject: str,
    chapter: str | None,
    top_k: int,
) -> list[dict[str, Any]]:
    response = _sparse_index().search_records(
        namespace=NS_CHUNKS,
        top_k=top_k,
        inputs={"text": query_text},
        filter=_metadata_filter(grade=grade, subject=subject),
    )
    result = getattr(response, "result", None)
    raw_hits = getattr(result, "hits", None) if result is not None else None
    if raw_hits is None:
        raw_hits = getattr(response, "hits", None) or []
    hits = [_search_hit_to_dict(hit) for hit in raw_hits]
    if chapter:
        hits = [hit for hit in hits if _chapter_matches(chapter, hit)]
    return hits


def hybrid_search(
    query_embedding: list[float],
    query_text: str,
    *,
    grade: int,
    subject: str,
    chapter: str | None = None,
) -> list[dict[str, Any]]:
    cfg = get_rag_config()
    fetch_k = cfg.retrieval_top_k * 4 if chapter else cfg.retrieval_top_k

    with ThreadPoolExecutor(max_workers=2) as executor:
        dense_future = executor.submit(
            _dense_search,
            query_embedding,
            grade=grade,
            subject=subject,
            chapter=chapter,
            top_k=fetch_k,
        )
        sparse_future = executor.submit(
            _sparse_search,
            query_text,
            grade=grade,
            subject=subject,
            chapter=chapter,
            top_k=fetch_k,
        )
        dense_hits = dense_future.result()
        sparse_hits = sparse_future.result()

    fused = _rrf_fuse(
        dense_hits,
        sparse_hits,
        rrf_k=cfg.hybrid_rrf_k,
        limit=cfg.retrieval_top_k,
    )
    return _attach_parent_text(fused)


def keyword_search(
    query_text: str,
    *,
    grade: int,
    subject: str,
    chapter: str | None = None,
) -> list[dict[str, Any]]:
    cfg = get_rag_config()
    fetch_k = cfg.retrieval_top_k * 4 if chapter else cfg.retrieval_top_k
    hits = _sparse_search(
        query_text,
        grade=grade,
        subject=subject,
        chapter=chapter,
        top_k=fetch_k,
    )
    return _attach_parent_text(hits[: cfg.retrieval_top_k])
