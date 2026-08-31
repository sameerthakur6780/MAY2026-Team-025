import logging

from sqlalchemy import false
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.academic import SchoolClass, Subject
from app.models.resource import Resource, ResourceType
from app.models.test import Test
from app.models.test_evaluation import EvaluationStatus
from app.services.storage import get_storage_service
from app.utils.dates import isoformat_utc
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_student, current_teacher, teacher_class_ids

logger = logging.getLogger(__name__)


def serialize_test(test):
    return {
        "id": test.id,
        "class_id": test.class_id,
        "grade": test.school_class.grade,
        "subject_id": test.subject_id,
        "subject_name": test.subject.name,
        "title": test.title,
        "description": test.description,
        "due_date": isoformat_utc(test.due_date),
        "created_by": test.created_by,
        "creator_name": test.creator.full_name,
        "resource_id": test.resource_id,
        "question_paper_resource_id": test.question_paper_resource_id,
        "answer_key_resource_id": test.answer_key_resource_id,
        "max_marks": test.max_marks,
        "evaluation_status": test.evaluation_status.value if test.evaluation_status else "not_scheduled",
        "evaluation_scheduled_at": isoformat_utc(test.evaluation_scheduled_at),
        "evaluation_started_at": isoformat_utc(test.evaluation_started_at),
        "evaluation_completed_at": isoformat_utc(test.evaluation_completed_at),
        "evaluation_error": test.evaluation_error,
        "created_at": isoformat_utc(test.created_at),
        "updated_at": isoformat_utc(test.updated_at),
    }


def get_test_or_404(test_id):
    test = Test.query.get(test_id)
    if test is None:
        raise not_found("Test")
    return test


def _validate_resource_for_class(resource_id, class_id, resource_type=None):
    if resource_id is None:
        return
    resource = Resource.query.get(resource_id)
    if resource is None:
        raise not_found("Resource")
    if resource.class_id != class_id:
        raise ApiError("resource_id does not belong to this class", "invalid_resource_class", 400)
    if resource_type is not None and resource.type != resource_type:
        raise ApiError(f"resource must be of type {resource_type.value}", "invalid_resource_type", 400)


def create_test(data, created_by):
    if SchoolClass.query.get(data["class_id"]) is None:
        raise not_found("Class")
    if Subject.query.get(data["subject_id"]) is None:
        raise not_found("Subject")
    _validate_resource_for_class(data.get("resource_id"), data["class_id"])
    _validate_resource_for_class(
        data.get("question_paper_resource_id"), data["class_id"], ResourceType.QUESTION_PAPER
    )
    _validate_resource_for_class(data.get("answer_key_resource_id"), data["class_id"], ResourceType.ANSWER_KEY)

    test = Test(
        class_id=data["class_id"],
        subject_id=data["subject_id"],
        title=data["title"].strip(),
        description=data.get("description"),
        due_date=data["due_date"],
        created_by=created_by,
        resource_id=data.get("resource_id"),
        question_paper_resource_id=data.get("question_paper_resource_id"),
        answer_key_resource_id=data.get("answer_key_resource_id"),
        max_marks=data["max_marks"],
    )
    db.session.add(test)
    db.session.commit()
    return test


def update_test(test_id, data):
    test = get_test_or_404(test_id)

    if "class_id" in data and SchoolClass.query.get(data["class_id"]) is None:
        raise not_found("Class")
    if "subject_id" in data and Subject.query.get(data["subject_id"]) is None:
        raise not_found("Subject")
    if "resource_id" in data:
        effective_class_id = data.get("class_id", test.class_id)
        _validate_resource_for_class(data["resource_id"], effective_class_id)
    if "question_paper_resource_id" in data:
        effective_class_id = data.get("class_id", test.class_id)
        _validate_resource_for_class(
            data["question_paper_resource_id"], effective_class_id, ResourceType.QUESTION_PAPER
        )
    if "answer_key_resource_id" in data:
        effective_class_id = data.get("class_id", test.class_id)
        _validate_resource_for_class(
            data["answer_key_resource_id"], effective_class_id, ResourceType.ANSWER_KEY
        )

    for field in (
        "class_id",
        "subject_id",
        "title",
        "description",
        "due_date",
        "resource_id",
        "question_paper_resource_id",
        "answer_key_resource_id",
        "max_marks",
    ):
        if field in data:
            value = data[field]
            if field == "title" and value:
                value = value.strip()
            setattr(test, field, value)

    db.session.commit()
    return test


def delete_test(test_id, current_user_id):
    test = get_test_or_404(test_id)
    if test.created_by != current_user_id:
        raise forbidden("Only the creator can delete this test")
    if test.evaluation_status == EvaluationStatus.RUNNING:
        raise ApiError(
            "Cannot delete a test while its evaluation is running",
            "evaluation_running",
            409,
        )

    from app.services.ai_grading_service import _remove_job

    _remove_job(test_id)

    storage = get_storage_service()
    for submission in list(test.submissions):
        try:
            storage.delete(submission.file_url)
        except Exception:
            logger.exception("Failed to delete submission file %s", submission.file_url)

    db.session.delete(test)
    db.session.commit()


def _scoped_query(role):
    query = Test.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        return query.filter(Test.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "parent":
        class_ids = {s.class_id for s in current_parent().students if s.class_id is not None}
        return query.filter(Test.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "student":
        student = current_student()
        if student.class_id is None:
            return query.filter(false())
        return query.filter(Test.class_id == student.class_id)
    raise forbidden()


def list_tests_query(role, class_id=None, subject_id=None):
    query = _scoped_query(role)
    if class_id is not None:
        query = query.filter(Test.class_id == class_id)
    if subject_id is not None:
        query = query.filter(Test.subject_id == subject_id)
    # serialize_test touches school_class/subject/creator on every row --
    # eager-load them in one query instead of 3 extra round trips per row.
    query = query.options(joinedload(Test.school_class), joinedload(Test.subject), joinedload(Test.creator))
    return query.order_by(Test.due_date.desc())


def get_test_scoped(test_id, role):
    test = get_test_or_404(test_id)

    if role == "admin":
        return test
    if role == "teacher":
        if test.class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        return test
    if role == "parent":
        child_class_ids = {s.class_id for s in current_parent().students}
        if test.class_id not in child_class_ids:
            raise forbidden()
        return test
    if role == "student":
        if test.class_id != current_student().class_id:
            raise forbidden()
        return test
    raise forbidden()
