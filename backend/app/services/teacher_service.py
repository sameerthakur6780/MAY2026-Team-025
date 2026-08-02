from app.extensions import db
from app.models.teacher import Teacher
from app.services.auth_service import create_managed_account
from app.utils.errors import not_found


def serialize_teacher(teacher):
    return {
        "id": teacher.id,
        "user_id": teacher.user_id,
        "full_name": teacher.user.full_name,
        "email": teacher.user.email,
        "phone": teacher.user.phone,
        "assigned_class_ids": sorted({cst.class_id for cst in teacher.class_subjects}),
    }


def get_teacher_or_404(teacher_id):
    teacher = Teacher.query.get(teacher_id)
    if teacher is None:
        raise not_found("Teacher")
    return teacher


def create_teacher(data):
    """Creates the account (user + teacher row) in one shot, same path as
    /api/auth/signup -- kept as a single source of truth for account
    creation rather than a second, divergent implementation."""
    data = dict(data, role="teacher")
    user = create_managed_account(data)
    return user.teacher


def delete_teacher(teacher_id):
    teacher = get_teacher_or_404(teacher_id)
    db.session.delete(teacher.user)
    db.session.commit()
