"""Structure-aware chunking with parent-child linking and deduplication."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from rag.config import get_rag_config
from rag.schemas import ChunkRecord, ContentType, ExtractedBlock

TOKEN_APPROX = 1.3


def _token_count(text: str) -> int:
    return max(1, int(len(re.findall(r"\S+", text)) * TOKEN_APPROX))


def _split_tokens(text: str, max_tokens: int, overlap_ratio: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    max_words = max(1, int(max_tokens / TOKEN_APPROX))
    overlap_words = max(1, int(max_words * overlap_ratio))
    if len(words) <= max_words:
        return [" ".join(words)]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = max(start + 1, end - overlap_words)
    return chunks


def _section_key(block: ExtractedBlock) -> tuple[str, str, str]:
    return (block.chapter or "", block.section or "", block.content_type)


def _dedupe_key(content: str) -> str:
    normalized = re.sub(r"\s+", " ", content.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def chunk_blocks(
    blocks: list[ExtractedBlock],
    book_id: str,
    subject: str,
    grade: int,
) -> list[ChunkRecord]:
    cfg = get_rag_config()
    grouped: dict[tuple[str, str, str], list[ExtractedBlock]] = defaultdict(list)
    for block in sorted(blocks, key=lambda item: (item.page, item.text[:40])):
        if block.content_type == "reference":
            continue
        grouped[_section_key(block)].append(block)

    records: list[ChunkRecord] = []
    seen_hashes: set[str] = set()

    for (_chapter, _section, content_type), section_blocks in grouped.items():
        pages = sorted({block.page for block in section_blocks})
        page_range = f"{pages[0]}-{pages[-1]}" if len(pages) > 1 else str(pages[0])
        parent_text = "\n\n".join(block.text for block in section_blocks)
        typed: ContentType = content_type if content_type != "reference" else "explanation"

        for piece in _split_tokens(
            parent_text,
            cfg.chunk_size_tokens,
            cfg.chunk_overlap_ratio,
        ):
            dedupe = _dedupe_key(piece)
            if dedupe in seen_hashes:
                continue
            seen_hashes.add(dedupe)
            records.append(
                ChunkRecord(
                    content=piece,
                    content_type=typed,
                    book_id=book_id,
                    subject=subject,
                    grade=grade,
                    chapter=_chapter,
                    section=_section,
                    page_range=page_range,
                    parent_text=parent_text,
                    chunk_index=len(records),
                )
            )
    return records
