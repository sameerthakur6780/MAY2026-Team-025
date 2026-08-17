"""Flask-facing assistant service."""

from __future__ import annotations

import re
import urllib.request

from app.models.academic import SchoolClass, Subject
from app.models.resource import Resource, ResourceType
from app.models.student import Student
from app.services.storage import get_storage_service
from app.utils.errors import ApiError
from rag.pipeline.ingest import ingest_pdf_bytes
from rag.pipeline.query import answer_question
from rag.schemas import IngestResult, QueryRequest, QueryResponse

GRADE_QUESTION_PATTERN = re.compile(
    r"\b(?:(?:which|what)\s+(?:grade|class)\b.*?\b(?:am i|i'?m|i am)\b(?:\s+in\b)?\??"
    r"|my\s+(?:grade|class)\b"
    r"|what\s+grade\s+(?:am i|do i belong)\b(?:\s+in\b)?\??)",
    flags=re.IGNORECASE,
)


def _student_context(user_id: int) -> tuple[int, str]:
    student = Student.query.filter_by(user_id=user_id).first()
    if not student or not student.class_id:
        raise ApiError("Student profile or class not found", "student_not_found", 404)
    school_class = SchoolClass.query.get(student.class_id)
    if not school_class:
        raise ApiError("Class not found", "class_not_found", 404)
    return school_class.grade, f"Grade {school_class.grade}"


def _infer_subject_from_query(query: str) -> str | None:
    query_lower = query.lower()
    for subject in Subject.query.order_by(Subject.name).all():
        if subject.name.lower() in query_lower:
            return subject.name
    return None


def _infer_chapter_from_query(query: str) -> str | None:
    match = re.search(r"\bchapter\s+([0-9]+[a-z]?)\b", query, flags=re.IGNORECASE)
    if not match:
        return None
    return f"Chapter {match.group(1)}"


def _subject_name(subject: str | None, query: str) -> str:
    if subject and subject.strip():
        return subject.strip()
    inferred = _infer_subject_from_query(query)
    if inferred:
        return inferred
    first = Subject.query.order_by(Subject.name).first()
    if not first:
        raise ApiError("No subjects configured", "no_subjects", 400)
    return first.name


def _split_grade_question(query: str) -> tuple[bool, str]:
    match = GRADE_QUESTION_PATTERN.search(query)
    if not match:
        return False, query
    remainder = (query[: match.start()] + " " + query[match.end() :]).strip(" ,?.;")
    remainder = re.sub(r"\band\b$", "", remainder, flags=re.IGNORECASE).strip(" ,?.;")
    return True, remainder


def _profile_grade_answer(grade_label: str) -> str:
    return f"You are in {grade_label}."


def ask_assistant(user_id: int, query: str, subject: str | None = None, chapter: str | None = None) -> QueryResponse:
    grade, grade_label = _student_context(user_id)
    asks_grade, remainder = _split_grade_question(query)

    if asks_grade and not remainder:
        return QueryResponse(answer=_profile_grade_answer(grade_label), model_used="profile")

    textbook_query = remainder if asks_grade and remainder else query
    resolved_subject = _subject_name(subject, textbook_query)
    resolved_chapter = chapter or _infer_chapter_from_query(textbook_query)
    result = answer_question(
        QueryRequest(
            query=textbook_query,
            grade=grade,
            subject=resolved_subject,
            chapter=resolved_chapter,
        )
    )
    if asks_grade and remainder:
        result.answer = f"{_profile_grade_answer(grade_label)}\n\n{result.answer}"
    return result


def ingest_resource_pdf(resource_id: int, *, force: bool = False) -> IngestResult:
    resource = Resource.query.get(resource_id)
    if not resource:
        raise ApiError("Resource not found", "not_found", 404)
    if resource.type not in (ResourceType.PDF, ResourceType.NOTE):
        raise ApiError("Only PDF/note resources can be indexed", "invalid_resource_type", 400)
    if not resource.subject or not resource.school_class:
        raise ApiError("Resource metadata incomplete", "invalid_resource", 400)

    storage = get_storage_service()
    signed = storage.get_signed_url(resource.storage_path, expires_in=300)
    with urllib.request.urlopen(signed) as response:
        pdf_bytes = response.read()

    title = resource.filename or "Untitled"
    return ingest_pdf_bytes(
        pdf_bytes,
        subject=resource.subject.name,
        grade=resource.school_class.grade,
        title=title,
        resource_id=resource.id,
        force=force,
    )
