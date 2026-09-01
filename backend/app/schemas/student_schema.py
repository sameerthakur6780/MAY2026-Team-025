from marshmallow import Schema, fields, pre_load, validate

from app.utils.validators import INDIAN_PHONE_ERROR, INDIAN_PHONE_REGEX


class StudentCreateSchema(Schema):
    full_name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    phone = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.Regexp(INDIAN_PHONE_REGEX, error=INDIAN_PHONE_ERROR),
    )
    admission_no = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=30))
    dob = fields.Date(load_default=None, allow_none=True)
    gender = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=20))
    class_id = fields.Integer(load_default=None, allow_none=True)
    parent_id = fields.Integer(load_default=None, allow_none=True)

    @pre_load
    def normalize_empty_phone(self, data, **kwargs):
        if isinstance(data, dict) and data.get("phone") == "":
            data = dict(data)
            data["phone"] = None
        return data


class StudentUpdateSchema(Schema):
    # profile_image is deliberately not editable here -- it's only ever set
    # via POST /api/students/<id>/profile-image, which uploads the photo and
    # computes its face embedding in the same step. Allowing a raw string
    # PATCH here would let profile_image and face_embedding drift out of
    # sync with each other.

    admission_no = fields.String(validate=validate.Length(max=30))
    dob = fields.Date(allow_none=True)
    gender = fields.String(allow_none=True, validate=validate.Length(max=20))
    class_id = fields.Integer(allow_none=True)
    parent_id = fields.Integer(allow_none=True)
    status = fields.String(validate=validate.OneOf(["active", "inactive", "withdrawn"]))
