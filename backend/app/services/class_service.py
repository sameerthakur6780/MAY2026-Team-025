from sqlalchemy import false
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.academic import SchoolClass
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_teacher, teacher_class_ids


def serialize_class(school_class):
    return {
        "id": school_class.id,
        "grade": school_class.grade,
        "student_count": len(school_class.students),
    }


def get_class_or_404(class_id):
    school_class = SchoolClass.query.get(class_id)
    if school_class is None:
        raise not_found("Class")
    return school_class


def scoped_class_query(role):
    query = SchoolClass.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        return query.filter(SchoolClass.id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "parent":
        class_ids = {s.class_id for s in current_parent().students if s.class_id is not None}
        return query.filter(SchoolClass.id.in_(class_ids)) if class_ids else query.filter(false())
    raise forbidden()


def get_class_scoped(class_id, role):
    school_class = get_class_or_404(class_id)
    if role == "admin":
        return school_class
    if role == "teacher":
        if school_class.id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        return school_class
    if role == "parent":
        child_class_ids = {s.class_id for s in current_parent().students}
        if school_class.id not in child_class_ids:
            raise forbidden()
        return school_class
    raise forbidden()


def create_class(data):
    school_class = SchoolClass(grade=data["grade"])
    db.session.add(school_class)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("A class for this grade already exists", "conflict", 409)
    return school_class


def update_class(class_id, data):
    school_class = get_class_or_404(class_id)
    if "grade" in data:
        school_class.grade = data["grade"]
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("A class for this grade already exists", "conflict", 409)
    return school_class


def delete_class(class_id):
    school_class = get_class_or_404(class_id)
    if school_class.students:
        raise ApiError(
            f"Cannot delete: {len(school_class.students)} student(s) are still assigned to this class",
            "conflict",
            409,
        )
    db.session.delete(school_class)
    db.session.commit()
