import logging

from sqlalchemy import false
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.academic import SchoolClass, Subject
from app.models.homework import Homework
from app.models.resource import Resource
from app.models.student import Student
from app.services.notification_service import NotificationService
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_student, current_teacher, teacher_class_ids

logger = logging.getLogger(__name__)


def serialize_homework(homework):
    return {
        "id": homework.id,
        "class_id": homework.class_id,
        "grade": homework.school_class.grade,
        "subject_id": homework.subject_id,
        "subject_name": homework.subject.name,
        "title": homework.title,
        "description": homework.description,
        "due_date": homework.due_date.isoformat(),
        "created_by": homework.created_by,
        "creator_name": homework.creator.full_name,
        "resource_id": homework.resource_id,
        "max_marks": homework.max_marks,
        "created_at": homework.created_at.isoformat(),
        "updated_at": homework.updated_at.isoformat(),
    }


def get_homework_or_404(homework_id):
    homework = Homework.query.get(homework_id)
    if homework is None:
        raise not_found("Homework")
    return homework


def _validate_resource_for_class(resource_id, class_id):
    if resource_id is None:
        return
    resource = Resource.query.get(resource_id)
    if resource is None:
        raise not_found("Resource")
    if resource.class_id != class_id:
        raise ApiError("resource_id does not belong to this class", "invalid_resource_class", 400)


def create_homework(data, created_by):
    if SchoolClass.query.get(data["class_id"]) is None:
        raise not_found("Class")
    if Subject.query.get(data["subject_id"]) is None:
        raise not_found("Subject")
    _validate_resource_for_class(data.get("resource_id"), data["class_id"])

    homework = Homework(
        class_id=data["class_id"],
        subject_id=data["subject_id"],
        title=data["title"].strip(),
        description=data.get("description"),
        due_date=data["due_date"],
        created_by=created_by,
        resource_id=data.get("resource_id"),
        max_marks=data["max_marks"],
    )
    db.session.add(homework)
    db.session.commit()

    try:
        student_ids = [
            row[0] for row in Student.query.with_entities(Student.id).filter_by(class_id=homework.class_id).all()
        ]
        NotificationService.notify_homework_assigned(homework, student_ids)
    except Exception:
        # Best-effort -- homework creation already succeeded and committed;
        # a notification problem must not surface as a failed creation.
        logger.exception("Failed to schedule homework_assigned notifications for homework %s", homework.id)

    return homework


def update_homework(homework_id, data):
    homework = get_homework_or_404(homework_id)

    if "class_id" in data and SchoolClass.query.get(data["class_id"]) is None:
        raise not_found("Class")
    if "subject_id" in data and Subject.query.get(data["subject_id"]) is None:
        raise not_found("Subject")
    if "resource_id" in data:
        effective_class_id = data.get("class_id", homework.class_id)
        _validate_resource_for_class(data["resource_id"], effective_class_id)

    for field in ("class_id", "subject_id", "title", "description", "due_date", "resource_id", "max_marks"):
        if field in data:
            value = data[field]
            if field == "title" and value:
                value = value.strip()
            setattr(homework, field, value)

    db.session.commit()
    return homework


def _scoped_query(role):
    query = Homework.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        return query.filter(Homework.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "parent":
        class_ids = {s.class_id for s in current_parent().students if s.class_id is not None}
        return query.filter(Homework.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "student":
        student = current_student()
        if student.class_id is None:
            return query.filter(false())
        return query.filter(Homework.class_id == student.class_id)
    raise forbidden()


def list_homework_query(role, class_id=None, subject_id=None):
    query = _scoped_query(role)
    if class_id is not None:
        query = query.filter(Homework.class_id == class_id)
    if subject_id is not None:
        query = query.filter(Homework.subject_id == subject_id)
    # serialize_homework touches school_class/subject/creator on every row --
    # eager-load them in one query instead of 3 extra round trips per row.
    query = query.options(
        joinedload(Homework.school_class), joinedload(Homework.subject), joinedload(Homework.creator)
    )
    return query.order_by(Homework.due_date.desc())


def get_homework_scoped(homework_id, role):
    homework = get_homework_or_404(homework_id)

    if role == "admin":
        return homework
    if role == "teacher":
        if homework.class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        return homework
    if role == "parent":
        child_class_ids = {s.class_id for s in current_parent().students}
        if homework.class_id not in child_class_ids:
            raise forbidden()
        return homework
    if role == "student":
        if homework.class_id != current_student().class_id:
            raise forbidden()
        return homework
    raise forbidden()
