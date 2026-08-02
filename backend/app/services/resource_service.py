import uuid
from pathlib import Path

from flask import current_app
from sqlalchemy import false
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.academic import SchoolClass, Subject
from app.models.homework import Homework
from app.models.resource import Resource, ResourceType
from app.models.test import Test
from app.services.storage import get_storage_service
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_student, current_teacher, teacher_class_ids


def serialize_resource(resource):
    return {
        "id": resource.id,
        "type": resource.type.value,
        "subject_id": resource.subject_id,
        "subject_name": resource.subject.name,
        "class_id": resource.class_id,
        "grade": resource.school_class.grade,
        "uploaded_by": resource.uploaded_by,
        "uploader_name": resource.uploader.full_name,
        "filename": resource.filename,
        "size": resource.size,
        "created_at": resource.created_at.isoformat(),
    }


def _extension(filename):
    return Path(filename).suffix.lstrip(".").lower()


def create_resource(file_storage, resource_type, subject_id, class_id, uploaded_by):
    if not file_storage or not file_storage.filename:
        raise ApiError("No file was uploaded", "missing_file", 400)

    allowed = current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]
    ext = _extension(file_storage.filename)
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

    if SchoolClass.query.get(class_id) is None:
        raise not_found("Class")
    if Subject.query.get(subject_id) is None:
        raise not_found("Subject")

    safe_filename = secure_filename(file_storage.filename) or "file"
    storage_path = f"{resource_type}/{class_id}/{uuid.uuid4()}_{safe_filename}"

    storage = get_storage_service()
    storage.upload(storage_path, file_bytes, file_storage.content_type or "application/octet-stream")

    resource = Resource(
        type=ResourceType(resource_type),
        subject_id=subject_id,
        class_id=class_id,
        uploaded_by=uploaded_by,
        storage_path=storage_path,
        filename=safe_filename,
        size=len(file_bytes),
    )
    db.session.add(resource)
    db.session.commit()
    return resource


def _scoped_query(role):
    query = Resource.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        return query.filter(Resource.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "parent":
        class_ids = {s.class_id for s in current_parent().students if s.class_id is not None}
        return query.filter(Resource.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "student":
        student = current_student()
        if student.class_id is None:
            return query.filter(false())
        return query.filter(Resource.class_id == student.class_id)
    raise forbidden()


def list_resources_query(role, class_id=None, subject_id=None):
    query = _scoped_query(role)
    if class_id is not None:
        query = query.filter(Resource.class_id == class_id)
    if subject_id is not None:
        query = query.filter(Resource.subject_id == subject_id)
    return query.order_by(Resource.created_at.desc())


def get_resource_scoped(resource_id, role):
    resource = Resource.query.get(resource_id)
    if resource is None:
        raise not_found("Resource")

    if role == "admin":
        return resource
    if role == "teacher":
        if resource.class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        return resource
    if role == "parent":
        child_class_ids = {s.class_id for s in current_parent().students}
        if resource.class_id not in child_class_ids:
            raise forbidden()
        return resource
    if role == "student":
        if resource.class_id != current_student().class_id:
            raise forbidden()
        return resource
    raise forbidden()


def get_download_url(resource_id, role):
    resource = get_resource_scoped(resource_id, role)
    expires_in = current_app.config["RESOURCE_SIGNED_URL_EXPIRY_SECONDS"]
    url = get_storage_service().get_signed_url(resource.storage_path, expires_in)
    return url, expires_in, resource


def delete_resource(resource_id, current_user_id, role):
    resource = Resource.query.get(resource_id)
    if resource is None:
        raise not_found("Resource")
    if role != "admin" and resource.uploaded_by != current_user_id:
        raise forbidden("Only the uploader or an admin can delete this resource")

    homework_count = Homework.query.filter_by(resource_id=resource_id).count()
    test_count = Test.query.filter_by(resource_id=resource_id).count()
    if homework_count or test_count:
        raise ApiError(
            f"Cannot delete: referenced by {homework_count} homework and {test_count} test record(s)",
            "conflict",
            409,
        )

    get_storage_service().delete(resource.storage_path)
    db.session.delete(resource)
    db.session.commit()
