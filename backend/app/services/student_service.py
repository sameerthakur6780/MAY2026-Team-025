import uuid
from pathlib import Path

from flask import current_app
from sqlalchemy import false
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.academic import SchoolClass
from app.models.student import Student
from app.services.auth_service import create_managed_account
from app.services.facial_recognition import FaceDetectionError, compute_profile_embedding
from app.services.storage import get_storage_service
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
        "has_face_embedding": student.face_embedding is not None,
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
    # serialize_student touches user/school_class on every row -- eager-load
    # them in one query instead of 2 extra round trips per row.
    query = query.options(joinedload(Student.user), joinedload(Student.school_class))
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

    for field in ("admission_no", "dob", "gender", "class_id", "parent_id", "status"):
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


def upload_profile_image(student_id, file_storage):
    student = Student.query.get(student_id)
    if student is None:
        raise not_found("Student")

    if not file_storage or not file_storage.filename:
        raise ApiError("No file was uploaded", "missing_file", 400)

    allowed = current_app.config["FACE_IMAGE_ALLOWED_EXTENSIONS"]
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

    # Compute the embedding BEFORE touching storage/DB -- a bad photo (no
    # face, multiple faces) should fail cleanly with nothing changed, rather
    # than leaving an orphaned upload or a photo/embedding mismatch.
    try:
        embedding = compute_profile_embedding(file_bytes)
    except FaceDetectionError as exc:
        raise ApiError(str(exc), exc.code, 400)

    safe_filename = secure_filename(file_storage.filename) or "file"
    storage_path = f"profile-images/{student_id}/{uuid.uuid4()}_{safe_filename}"
    storage = get_storage_service()
    storage.upload(storage_path, file_bytes, file_storage.content_type or "application/octet-stream")

    old_path = student.profile_image
    student.profile_image = storage_path
    student.face_embedding = embedding
    db.session.commit()

    if old_path:
        storage.delete(old_path)

    return student
