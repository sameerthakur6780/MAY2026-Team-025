"""Layout-aware PDF extraction with header/footer stripping and content tagging."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO

import fitz
import pdfplumber

from rag.schemas import ContentType, ExtractedBlock

FIGURE_PATTERN = re.compile(r"^(figure|fig\.?)\s+\d", re.IGNORECASE)
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
HEADER_FOOTER_BAND = 0.08


@dataclass
class ExtractionResult:
    blocks: list[ExtractedBlock] = field(default_factory=list)
    pdf_hash: str = ""
    title: str = ""


def hash_pdf_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _approx_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.3))


def _detect_repeated_edge_lines(doc: fitz.Document) -> set[str]:
    """Headers/footers repeat at similar y-positions across pages."""
    top_lines: Counter[str] = Counter()
    bottom_lines: Counter[str] = Counter()
    page_count = max(len(doc), 1)
    threshold = max(2, int(page_count * 0.08))

    for page in doc:
        height = page.rect.height
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            text = " ".join(
                span["text"].strip()
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            ).strip()
            if not text:
                continue
            y0 = block["bbox"][1]
            y1 = block["bbox"][3]
            if y0 <= height * HEADER_FOOTER_BAND:
                top_lines[text] += 1
            if y1 >= height * (1 - HEADER_FOOTER_BAND):
                bottom_lines[text] += 1

    noise = set()
    for counter in (top_lines, bottom_lines):
        noise.update(text for text, count in counter.items() if count >= threshold)
    return noise


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
    if FIGURE_PATTERN.match(text.strip()):
        return "figure_caption"
    lowered = text.lower().strip()
    if any(keyword in lowered for keyword in EXERCISE_KEYWORDS):
        return "exercise"
    return "explanation"


def _extract_tables(pdf_bytes: bytes) -> list[ExtractedBlock]:
    blocks: list[ExtractedBlock] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            for table in tables:
                rows = [" | ".join(cell or "" for cell in row) for row in table if row]
                text = "\n".join(rows).strip()
                if text:
                    blocks.append(
                        ExtractedBlock(text=text, content_type="table", page=page_num)
                    )
    return blocks


def _reading_order_blocks(page: fitz.Page, noise_lines: set[str]) -> list[tuple[float, float, str]]:
    """Return (y0, x0, text) tuples sorted for multi-column reading order."""
    items: list[tuple[float, float, str]] = []
    blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)["blocks"]
    for block in blocks:
        if block.get("type") != 0:
            continue
        text = " ".join(
            span["text"].strip()
            for line in block.get("lines", [])
            for span in line.get("spans", [])
        ).strip()
        if not text or text in noise_lines:
            continue
        x0 = block["bbox"][0]
        y0 = block["bbox"][1]
        items.append((y0, x0, text))
    items.sort(key=lambda item: (round(item[0], 1), item[1]))
    return items


def extract_pdf(pdf_bytes: bytes, title: str = "") -> ExtractionResult:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        meta = doc.metadata or {}
        resolved_title = title or meta.get("title") or "Untitled"
        noise_lines = _detect_repeated_edge_lines(doc)

        outline_by_page: dict[int, tuple[str, str]] = {}
        current_chapter = ""
        current_section = ""
        try:
            toc = doc.get_toc(simple=True) or []
            for level, heading, page_num in toc:
                heading = heading.strip()
                if level == 1:
                    current_chapter = heading
                    current_section = ""
                elif level >= 2:
                    current_section = heading
                outline_by_page[page_num] = (current_chapter, current_section)
        except Exception:
            outline_by_page = {}

        blocks: list[ExtractedBlock] = []
        active_section_type: ContentType | None = None
        prev_page = 0

        for page_index, page in enumerate(doc, start=1):
            if page_index in outline_by_page:
                current_chapter, current_section = outline_by_page[page_index]
                active_section_type = _classify_section_heading(current_section or current_chapter)

            ordered = _reading_order_blocks(page, noise_lines)
            for _y0, _x0, text in ordered:
                content_type = _classify_block(text, active_section_type)
                blocks.append(
                    ExtractedBlock(
                        text=text,
                        content_type=content_type,
                        page=page_index,
                        chapter=current_chapter,
                        section=current_section,
                    )
                )
            prev_page = page_index

        blocks.extend(_extract_tables(pdf_bytes))
        blocks.sort(key=lambda block: (block.page, block.text[:40]))
        return ExtractionResult(
            blocks=blocks,
            pdf_hash=hash_pdf_bytes(pdf_bytes),
            title=resolved_title,
        )
    finally:
        doc.close()
