from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user, get_jwt
from marshmallow import ValidationError

from app.schemas.resource_schema import ResourceUploadSchema
from app.services.resource_service import (
    create_resource,
    delete_resource,
    get_download_url,
    get_resource_scoped,
    list_resources_query,
    serialize_resource,
)
from app.utils.decorators import role_required
from app.utils.pagination import paginate_query

resources_bp = Blueprint("resources", __name__, url_prefix="/api/resources")

_upload_schema = ResourceUploadSchema()

_ALL_ROLES = ("admin", "teacher", "parent", "student")


def _int_arg(name):
    raw = request.args.get(name)
    if raw is None:
        return None, None
    try:
        return int(raw), None
    except ValueError:
        return None, f"{name} must be an integer"


@resources_bp.get("")
@role_required(*_ALL_ROLES)
def list_resources():
    class_id, err = _int_arg("class_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"class_id": [err]}}), 400
    subject_id, err = _int_arg("subject_id")
    if err:
        return jsonify({"error": "validation_error", "message": {"subject_id": [err]}}), 400

    role = get_jwt()["role"]
    query = list_resources_query(role, class_id=class_id, subject_id=subject_id)
    return jsonify(paginate_query(query, serialize_resource)), 200


@resources_bp.get("/<int:resource_id>")
@role_required(*_ALL_ROLES)
def get_resource(resource_id):
    role = get_jwt()["role"]
    resource = get_resource_scoped(resource_id, role)
    return jsonify(serialize_resource(resource)), 200


@resources_bp.get("/<int:resource_id>/download")
@role_required(*_ALL_ROLES)
def download_resource(resource_id):
    role = get_jwt()["role"]
    url, expires_in, resource = get_download_url(resource_id, role)
    return jsonify({"url": url, "expires_in": expires_in, "filename": resource.filename}), 200


@resources_bp.post("")
@role_required("admin", "teacher")
def upload_resource():
    try:
        data = _upload_schema.load(request.form.to_dict())
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "message": exc.messages}), 400

    file_storage = request.files.get("file")
    resource = create_resource(file_storage, data["type"], data["subject_id"], data["class_id"], current_user.id)
    return jsonify(serialize_resource(resource)), 201


@resources_bp.delete("/<int:resource_id>")
@role_required("admin", "teacher")
def delete_resource_route(resource_id):
    role = get_jwt()["role"]
    delete_resource(resource_id, current_user.id, role)
    return "", 204
