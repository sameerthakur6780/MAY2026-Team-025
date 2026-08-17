"""End-to-end PDF ingestion pipeline."""

from __future__ import annotations

from rag.chunking.chunker import chunk_blocks
from rag.embedding.gemini_embedder import embed_texts
from rag.extraction.pdf_extractor import extract_pdf
from rag.schemas import IngestResult
from rag.store.supabase_store import (
    create_book,
    delete_book_chunks,
    get_book_by_hash,
    index_chunks,
)


def ingest_pdf_bytes(
    pdf_bytes: bytes,
    *,
    subject: str,
    grade: int,
    title: str = "Untitled",
    resource_id: int | None = None,
    force: bool = False,
) -> IngestResult:
    extracted = extract_pdf(pdf_bytes, title=title)
    if not extracted.blocks:
        return IngestResult(message="No indexable content extracted")

    existing = get_book_by_hash(extracted.pdf_hash)
    existing_chunk_count = int(existing.get("chunk_count") or 0) if existing else 0
    if existing and not force and existing_chunk_count > 0:
        return IngestResult(
            book_id=existing["id"],
            pdf_hash=extracted.pdf_hash,
            skipped=True,
            message="PDF unchanged; skipped re-indexing",
        )

    if existing:
        delete_book_chunks(existing["id"])
        book_id = existing["id"]
    else:
        book_id = create_book(
            extracted.pdf_hash,
            extracted.title or title,
            subject,
            grade,
            resource_id=resource_id,
        )

    chunks = chunk_blocks(extracted.blocks, book_id, subject, grade)
    if not chunks:
        return IngestResult(
            book_id=book_id,
            pdf_hash=extracted.pdf_hash,
            message="No indexable content extracted",
        )

    embeddings = embed_texts([chunk.content for chunk in chunks])
    indexed = index_chunks(chunks, embeddings)
    return IngestResult(
        book_id=book_id,
        pdf_hash=extracted.pdf_hash,
        chunks_indexed=indexed,
        message=f"Indexed {indexed} chunks",
    )


def ingest_pdf_file(
    path: str,
    *,
    subject: str,
    grade: int,
    title: str = "Untitled",
    resource_id: int | None = None,
    force: bool = False,
) -> IngestResult:
    with open(path, "rb") as handle:
        pdf_bytes = handle.read()
    return ingest_pdf_bytes(
        pdf_bytes,
        subject=subject,
        grade=grade,
        title=title,
        resource_id=resource_id,
        force=force,
    )
