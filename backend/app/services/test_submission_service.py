import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import false
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.student import Student
from app.models.test import Test, TestSubmission
from app.models.homework import SubmissionStatus
from app.services.notification_service import NotificationService
from app.services.storage import get_storage_service
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_student, current_teacher, teacher_class_ids

logger = logging.getLogger(__name__)


def serialize_submission(submission):
    return {
        "id": submission.id,
        "test_id": submission.test_id,
        "student_id": submission.student_id,
        "student_name": submission.student.user.full_name,
        "submitted_at": submission.submitted_at.isoformat(),
        "marks": submission.marks,
        "feedback": submission.feedback,
        "graded_by": submission.graded_by,
        "graded_by_name": submission.grader.full_name if submission.grader else None,
        "status": submission.status.value,
    }


def get_submission_or_404(submission_id):
    submission = TestSubmission.query.get(submission_id)
    if submission is None:
        raise not_found("Test submission")
    return submission


def submit_test(test_id, file_storage, student_id):
    test = Test.query.get(test_id)
    if test is None:
        raise not_found("Test")

    student = Student.query.get(student_id)
    if student is None or student.class_id != test.class_id:
        raise ApiError("You are not enrolled in this test's class", "invalid_student_class", 400)

    if not file_storage or not file_storage.filename:
        raise ApiError("No file was uploaded", "missing_file", 400)

    allowed = current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]
    ext = Path(file_storage.filename).suffix.lstrip(".").lower()
    if ext not in allowed:
        raise ApiError(
            f"File type .{ext or '?'} isn't allowed. Allowed types: {', '.join(sorted(allowed))}",
            "invalid_file_type",
            400,
        )

    file_bytes = file_storage.read()
    if len(file_bytes) == 0:
        raise ApiError("Uploaded file is empty", "empty_file", 400)
    max_size = current_app.config["MAX_UPLOAD_SIZE_BYTES"]
    if len(file_bytes) > max_size:
        raise ApiError(f"File exceeds the {max_size // (1024 * 1024)}MB size limit", "file_too_large", 400)

    safe_filename = secure_filename(file_storage.filename) or "file"
    storage_path = f"test-submissions/{test_id}/{uuid.uuid4()}_{safe_filename}"
    content_type = file_storage.content_type or "application/octet-stream"
    storage = get_storage_service()

    existing = TestSubmission.query.filter_by(test_id=test_id, student_id=student_id).first()
    if existing is not None:
        if existing.status == SubmissionStatus.GRADED:
            raise ApiError(
                "This submission has already been graded and can no longer be replaced",
                "already_graded",
                409,
            )
        old_path = existing.file_url
        storage.upload(storage_path, file_bytes, content_type)
        storage.delete(old_path)
        existing.file_url = storage_path
        existing.submitted_at = datetime.now(timezone.utc)
        db.session.commit()
        return existing

    storage.upload(storage_path, file_bytes, content_type)
    submission = TestSubmission(
        test_id=test_id,
        student_id=student_id,
        file_url=storage_path,
        submitted_at=datetime.now(timezone.utc),
        status=SubmissionStatus.PENDING,
    )
    db.session.add(submission)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("A submission for this test already exists", "conflict", 409)
    return submission


def grade_submission(submission_id, marks, feedback, graded_by):
    submission = get_submission_or_404(submission_id)
    submission.marks = marks
    submission.feedback = feedback
    submission.graded_by = graded_by
    submission.status = SubmissionStatus.GRADED
    db.session.commit()

    try:
        NotificationService.notify_marks_published(
            submission.student, "test", submission.test.title, submission.test.subject.name, marks
        )
    except Exception:
        logger.exception("Failed to send marks_published notification for test submission %s", submission.id)

    return submission


def get_download_url(submission_id, role):
    submission = get_submission_scoped(submission_id, role)
    expires_in = current_app.config["RESOURCE_SIGNED_URL_EXPIRY_SECONDS"]
    url = get_storage_service().get_signed_url(submission.file_url, expires_in)
    return url, expires_in, submission


def _scoped_query(role):
    query = TestSubmission.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        if not class_ids:
            return query.filter(false())
        return query.join(Test, TestSubmission.test_id == Test.id).filter(Test.class_id.in_(class_ids))
    if role == "parent":
        student_ids = {s.id for s in current_parent().students}
        return query.filter(TestSubmission.student_id.in_(student_ids)) if student_ids else query.filter(false())
    if role == "student":
        return query.filter(TestSubmission.student_id == current_student().id)
    raise forbidden()


def list_submissions_query(role, test_id=None, student_id=None, status=None):
    query = _scoped_query(role)
    if test_id is not None:
        query = query.filter(TestSubmission.test_id == test_id)
    if student_id is not None:
        query = query.filter(TestSubmission.student_id == student_id)
    if status is not None:
        query = query.filter(TestSubmission.status == SubmissionStatus(status))
    # serialize_submission touches student.user and grader on every row --
    # eager-load them in one query instead of extra round trips per row.
    query = query.options(
        joinedload(TestSubmission.student).joinedload(Student.user), joinedload(TestSubmission.grader)
    )
    return query.order_by(TestSubmission.submitted_at.desc())


def get_submission_scoped(submission_id, role):
    submission = get_submission_or_404(submission_id)

    if role == "admin":
        return submission
    if role == "teacher":
        if submission.test.class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        return submission
    if role == "parent":
        child_ids = {s.id for s in current_parent().students}
        if submission.student_id not in child_ids:
            raise forbidden()
        return submission
    if role == "student":
        if submission.student_id != current_student().id:
            raise forbidden()
        return submission
    raise forbidden()
