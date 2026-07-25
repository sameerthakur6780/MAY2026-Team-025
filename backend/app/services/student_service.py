from sqlalchemy import false
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.academic import SchoolClass
from app.models.student import Student
from app.services.auth_service import create_managed_account
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_teacher, teacher_class_ids


def serialize_student(student):
    return {
        "id": student.id,
        "user_id": student.user_id,
        "full_name": student.user.full_name,
        "email": student.user.email,
        "phone": student.user.phone,
        "admission_no": student.admission_no,
        "dob": student.dob.isoformat() if student.dob else None,
        "gender": student.gender,
        "class_id": student.class_id,
        "grade": student.school_class.grade if student.school_class else None,
        "parent_id": student.parent_id,
        "profile_image": student.profile_image,
        "status": student.status,
    }


def _scoped_query(role):
    query = Student.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        if not class_ids:
            return query.filter(false())
        return query.filter(Student.class_id.in_(class_ids))
    if role == "parent":
        return query.filter_by(parent_id=current_parent().id)
    raise forbidden()


def list_students_query(role, class_id=None, grade=None):
    query = _scoped_query(role)
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
    if grade is not None:
        query = query.join(SchoolClass, Student.class_id == SchoolClass.id).filter(SchoolClass.grade == grade)
    return query


def get_student_scoped(student_id, role):
    student = Student.query.get(student_id)
    if student is None:
        raise not_found("Student")

    if role == "admin":
        return student
    if role == "teacher":
        if student.class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        return student
    if role == "parent":
        if student.parent_id != current_parent().id:
            raise forbidden()
        return student
    raise forbidden()


def create_student(data):
    """Creates the account (user + student row) in one shot -- see
    teacher_service.create_teacher for why this delegates to signup's
    account-creation logic rather than reimplementing it."""
    data = dict(data, role="student")
    user = create_managed_account(data)
    return user.student


def update_student(student_id, data):
    student = Student.query.get(student_id)
    if student is None:
        raise not_found("Student")

    for field in ("admission_no", "dob", "gender", "class_id", "parent_id", "profile_image", "status"):
        if field in data:
            setattr(student, field, data[field])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("A record with conflicting unique fields already exists (e.g. admission_no)", "conflict", 409)

    return student


def delete_student(student_id):
    student = Student.query.get(student_id)
    if student is None:
        raise not_found("Student")
    db.session.delete(student.user)
    db.session.commit()
