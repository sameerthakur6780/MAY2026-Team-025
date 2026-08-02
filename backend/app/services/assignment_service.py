from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.academic import ClassSubjectTeacher, SchoolClass, Subject
from app.models.teacher import Teacher
from app.utils.errors import ApiError, not_found


def serialize_assignment(assignment):
    return {
        "id": assignment.id,
        "class_id": assignment.class_id,
        "grade": assignment.school_class.grade,
        "subject_id": assignment.subject_id,
        "subject_name": assignment.subject.name,
        "teacher_id": assignment.teacher_id,
        "teacher_name": assignment.teacher.user.full_name,
    }


def list_assignments_query(class_id=None, teacher_id=None):
    query = ClassSubjectTeacher.query
    if class_id is not None:
        query = query.filter_by(class_id=class_id)
    if teacher_id is not None:
        query = query.filter_by(teacher_id=teacher_id)
    return query.order_by(ClassSubjectTeacher.id)


def get_assignment_or_404(assignment_id):
    assignment = ClassSubjectTeacher.query.get(assignment_id)
    if assignment is None:
        raise not_found("Assignment")
    return assignment


def create_assignment(data):
    class_id = data["class_id"]
    subject_id = data["subject_id"]
    teacher_id = data["teacher_id"]

    # SQLite FK enforcement isn't turned on anywhere in this project, so a
    # bogus id would otherwise insert silently instead of erroring.
    if SchoolClass.query.get(class_id) is None:
        raise not_found("Class")
    if Subject.query.get(subject_id) is None:
        raise not_found("Subject")
    if Teacher.query.get(teacher_id) is None:
        raise not_found("Teacher")

    existing = ClassSubjectTeacher.query.filter_by(class_id=class_id, subject_id=subject_id).first()
    if existing is not None:
        raise ApiError(
            "This class/subject combination is already assigned to a teacher",
            "conflict",
            409,
        )

    assignment = ClassSubjectTeacher(class_id=class_id, subject_id=subject_id, teacher_id=teacher_id)
    db.session.add(assignment)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError(
            "This class/subject combination is already assigned to a teacher",
            "conflict",
            409,
        )
    return assignment


def delete_assignment(assignment_id):
    assignment = get_assignment_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
