"""Layout-aware PDF extraction via pymupdf4llm with content tagging."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from io import BytesIO

import fitz
import pdfplumber
import pymupdf4llm
from pdfplumber.utils.exceptions import PdfminerException

from rag.schemas import ContentType, ExtractedBlock

FIGURE_PATTERN = re.compile(r"^(figure|fig\.?)\s+\d", re.IGNORECASE)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
NUMBERED_LIST_LINE = re.compile(r"^\d+\.\s+\S")
REFERENCE_KEYWORDS = (
    "table of contents",
    "contents",
    "index",
    "glossary",
    "bibliography",
    "references",
)
EXERCISE_KEYWORDS = (
    "exercise",
    "exercises",
    "practice problems",
    "review questions",
    "fill in the blank",
    "match the following",
    "short answer",
    "objective questions",
)


@dataclass
class ExtractionResult:
    blocks: list[ExtractedBlock] = field(default_factory=list)
    pdf_hash: str = ""
    title: str = ""


def hash_pdf_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collapse_repeated_tokens(text: str, *, min_run: int = 3) -> str:
    """Collapse decorative repeated tokens such as 'TOMS TOMS TOMS'."""
    tokens = text.split()
    if not tokens:
        return text

    collapsed: list[str] = []
    index = 0
    while index < len(tokens):
        end = index + 1
        while end < len(tokens) and tokens[end].casefold() == tokens[index].casefold():
            end += 1
        run_length = end - index
        collapsed.append(tokens[index])
        index = end if run_length >= min_run else index + 1
    return " ".join(collapsed)


def is_numbered_list(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    numbered = sum(1 for line in lines if NUMBERED_LIST_LINE.match(line))
    return numbered / len(lines) >= 0.6


def is_gfm_table(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    pipe_lines = sum(1 for line in lines if line.count("|") >= 2)
    return pipe_lines >= 2


def _classify_section_heading(text: str) -> ContentType | None:
    lowered = text.lower().strip()
    if any(keyword in lowered for keyword in REFERENCE_KEYWORDS):
        return "reference"
    if any(keyword in lowered for keyword in EXERCISE_KEYWORDS):
        return "exercise"
    return None


def _classify_block(text: str, section_type: ContentType | None) -> ContentType:
    if section_type == "reference":
        return "reference"
    if is_gfm_table(text):
        return "table"
    if is_numbered_list(text):
        return "exercise"
    if FIGURE_PATTERN.match(text.strip()):
        return "figure_caption"
    lowered = text.lower().strip()
    if any(keyword in lowered for keyword in EXERCISE_KEYWORDS):
        return "exercise"
    return "explanation"


def _normalize_block_text(text: str) -> str:
    cleaned = re.sub(r"\n{3,}", "\n\n", text.strip())
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return collapse_repeated_tokens(cleaned)


def _split_markdown_paragraphs(markdown: str) -> list[str]:
    parts: list[str] = []
    buffer: list[str] = []
    for line in markdown.splitlines():
        if not line.strip():
            if buffer:
                parts.append("\n".join(buffer).strip())
                buffer = []
            continue
        buffer.append(line.rstrip())
    if buffer:
        parts.append("\n".join(buffer).strip())
    return [part for part in parts if part]


def _extract_tables_fallback(
    pdf_bytes: bytes,
    *,
    chapter: str,
    section: str,
) -> list[ExtractedBlock]:
    blocks: list[ExtractedBlock] = []
    try:
        pdf = pdfplumber.open(BytesIO(pdf_bytes))
    except PdfminerException:
        return blocks

    with pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                tables = page.extract_tables() or []
            except PdfminerException:
                continue
            for table in tables:
                rows = [" | ".join(cell or "" for cell in row) for row in table if row]
                text = _normalize_block_text("\n".join(rows))
                if text:
                    blocks.append(
                        ExtractedBlock(
                            text=text,
                            content_type="table",
                            page=page_num,
                            chapter=chapter,
                            section=section,
                        )
                    )
    return blocks


def _page_number_from_chunk(chunk: dict, fallback: int) -> int:
    metadata = chunk.get("metadata") or {}
    for key in ("page", "page_number"):
        value = chunk.get(key, metadata.get(key))
        if isinstance(value, int):
            return value + 1 if key == "page" and value >= 0 else value
    return fallback


def _header_info(doc: fitz.Document):
    try:
        if hasattr(pymupdf4llm, "TocHeaders"):
            return pymupdf4llm.TocHeaders(doc)
    except Exception:
        pass
    try:
        if hasattr(pymupdf4llm, "IdentifyHeaders"):
            return pymupdf4llm.IdentifyHeaders(doc)
    except Exception:
        pass
    return None


def _markdown_page_chunks(doc: fitz.Document) -> list[dict]:
    if getattr(pymupdf4llm, "_use_layout", False):
        return pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            header=False,
            footer=False,
        )

    kwargs: dict = {
        "page_chunks": True,
        "table_strategy": "lines_strict",
    }
    hdr_info = _header_info(doc)
    if hdr_info is not None:
        kwargs["hdr_info"] = hdr_info
    return pymupdf4llm.to_markdown(doc, **kwargs)


def _blocks_from_markdown_pages(page_chunks: list[dict]) -> list[ExtractedBlock]:
    blocks: list[ExtractedBlock] = []
    current_chapter = ""
    current_section = ""
    active_section_type: ContentType | None = None

    for page_index, chunk in enumerate(page_chunks, start=1):
        page_num = _page_number_from_chunk(chunk, page_index)
        markdown = chunk.get("text") or chunk.get("markdown") or ""
        for part in _split_markdown_paragraphs(markdown):
            heading_match = HEADING_PATTERN.match(part)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                if level == 1:
                    current_chapter = heading_text
                    current_section = ""
                elif level >= 2:
                    current_section = heading_text
                active_section_type = _classify_section_heading(current_section or current_chapter)
                continue

            text = _normalize_block_text(part)
            if not text:
                continue
            blocks.append(
                ExtractedBlock(
                    text=text,
                    content_type=_classify_block(text, active_section_type),
                    page=page_num,
                    chapter=current_chapter,
                    section=current_section,
                )
            )
    return blocks


def extract_pdf(pdf_bytes: bytes, title: str = "") -> ExtractionResult:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        meta = doc.metadata or {}
        resolved_title = title or meta.get("title") or "Untitled"
        page_chunks = _markdown_page_chunks(doc)
        blocks = _blocks_from_markdown_pages(page_chunks)

        last_chapter = blocks[-1].chapter if blocks else ""
        last_section = blocks[-1].section if blocks else ""
        fallback_tables = _extract_tables_fallback(
            pdf_bytes,
            chapter=last_chapter,
            section=last_section,
        )
        existing_table_keys = {
            re.sub(r"\s+", " ", block.text.strip().lower()) for block in blocks if block.content_type == "table"
        }
        for table_block in fallback_tables:
            key = re.sub(r"\s+", " ", table_block.text.strip().lower())
            if key not in existing_table_keys:
                blocks.append(table_block)

        return ExtractionResult(
            blocks=blocks,
            pdf_hash=hash_pdf_bytes(pdf_bytes),
            title=resolved_title,
        )
    finally:
        doc.close()
