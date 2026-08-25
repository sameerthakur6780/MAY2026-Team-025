from app.extensions import db
from app.models.academic import ClassSubjectTeacher, SchoolClass, Subject
from app.models.teacher import Teacher
from app.models.user import User
from app.services.auth_service import create_managed_account
from app.utils.errors import ApiError, not_found


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


def update_teacher(teacher_id, data):
    teacher = get_teacher_or_404(teacher_id)
    user = teacher.user

    if "full_name" in data:
        user.full_name = data["full_name"].strip()
    if "phone" in data:
        user.phone = data["phone"]
    if "email" in data:
        email = data["email"].strip().lower()
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing is not None:
            raise ApiError("An account with this email already exists", "email_taken", 409)
        user.email = email

    has_subject = "subject_id" in data
    has_classes = "class_ids" in data
    if has_subject != has_classes:
        raise ApiError("subject_id and class_ids must be provided together", "invalid_request", 400)

    if has_subject:
        subject_id = data["subject_id"]
        class_ids = data["class_ids"]

        if Subject.query.get(subject_id) is None:
            raise not_found("Subject")

        for class_id in class_ids:
            if SchoolClass.query.get(class_id) is None:
                raise not_found("Class")

        desired = set(class_ids)
        conflicts: list[str] = []
        for class_id in desired:
            existing = ClassSubjectTeacher.query.filter_by(class_id=class_id, subject_id=subject_id).first()
            if existing is not None and existing.teacher_id != teacher.id:
                school_class = SchoolClass.query.get(class_id)
                grade_label = school_class.grade if school_class else class_id
                conflicts.append(f"Grade {grade_label}")

        if conflicts:
            raise ApiError(
                f"These classes already have this subject assigned to another teacher: {', '.join(sorted(conflicts))}",
                "conflict",
                409,
            )

        current_rows = ClassSubjectTeacher.query.filter_by(teacher_id=teacher.id, subject_id=subject_id).all()
        current_class_ids = {row.class_id for row in current_rows}

        for row in current_rows:
            if row.class_id not in desired:
                db.session.delete(row)

        for class_id in desired - current_class_ids:
            db.session.add(
                ClassSubjectTeacher(class_id=class_id, subject_id=subject_id, teacher_id=teacher.id)
            )

    db.session.commit()
    db.session.refresh(teacher)
    return teacher


def delete_teacher(teacher_id):
    teacher = get_teacher_or_404(teacher_id)
    db.session.delete(teacher.user)
    db.session.commit()
