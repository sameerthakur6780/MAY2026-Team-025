from flask_jwt_extended import current_user

from app.models.academic import ClassSubjectTeacher
from app.utils.errors import forbidden


def current_teacher():
    """Teacher row for the logged-in user, or raises 403 if somehow missing
    (shouldn't happen -- signup always creates User+Teacher together)."""
    teacher = current_user.teacher
    if teacher is None:
        raise forbidden("No teacher profile is linked to this account")
    return teacher


def current_parent():
    parent = current_user.parent
    if parent is None:
        raise forbidden("No parent profile is linked to this account")
    return parent


def current_student():
    student = current_user.student
    if student is None:
        raise forbidden("No student profile is linked to this account")
    return student


def teacher_class_ids(teacher):
    """Distinct ids of classes this teacher is assigned to via
    class_subject_teacher."""
    rows = (
        ClassSubjectTeacher.query.with_entities(ClassSubjectTeacher.class_id)
        .filter_by(teacher_id=teacher.id)
        .distinct()
        .all()
    )
    return [row[0] for row in rows]
