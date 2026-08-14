"""Flask-facing assistant service."""

from __future__ import annotations

import urllib.request

from app.models.academic import SchoolClass, Subject
from app.models.resource import Resource, ResourceType
from app.models.student import Student
from app.services.storage import get_storage_service
from app.utils.errors import ApiError
from rag.pipeline.ingest import ingest_pdf_bytes
from rag.pipeline.query import answer_question
from rag.schemas import IngestResult, QueryRequest, QueryResponse


def _student_context(user_id: int) -> tuple[int, str | None]:
    student = Student.query.filter_by(user_id=user_id).first()
    if not student or not student.class_id:
        raise ApiError("Student profile or class not found", "student_not_found", 404)
    school_class = SchoolClass.query.get(student.class_id)
    if not school_class:
        raise ApiError("Class not found", "class_not_found", 404)
    return school_class.grade, None


def _subject_name(subject: str | None) -> str:
    if subject and subject.strip():
        return subject.strip()
    first = Subject.query.order_by(Subject.name).first()
    if not first:
        raise ApiError("No subjects configured", "no_subjects", 400)
    return first.name


def ask_assistant(user_id: int, query: str, subject: str | None = None, chapter: str | None = None) -> QueryResponse:
    grade, _ = _student_context(user_id)
    resolved_subject = _subject_name(subject)
    return answer_question(
        QueryRequest(
            query=query,
            grade=grade,
            subject=resolved_subject,
            chapter=chapter,
        )
    )


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
