from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal["explanation", "exercise", "table", "figure_caption", "reference"]


class ExtractedBlock(BaseModel):
    text: str
    content_type: ContentType = "explanation"
    page: int
    chapter: str = ""
    section: str = ""


class ChunkRecord(BaseModel):
    content: str
    content_type: ContentType
    book_id: str
    subject: str
    grade: int
    chapter: str = ""
    section: str = ""
    page_range: str = ""
    parent_text: str = ""
    chunk_index: int = 0


class Citation(BaseModel):
    book_id: str
    chapter: str = ""
    section: str = ""
    page_range: str = ""
    content_type: ContentType = "explanation"
    excerpt: str = ""


class RagAnswer(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    model_used: str = "none"
    cached: bool = False
    rewritten_query: str = ""


class IngestResult(BaseModel):
    book_id: str = ""
    pdf_hash: str = ""
    chunks_indexed: int = 0
    skipped: bool = False
    message: str = ""


class QueryRequest(BaseModel):
    query: str
    grade: int
    subject: str
    chapter: str | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    model_used: str = "none"
    cached: bool = False
    rewritten_query: str = ""
