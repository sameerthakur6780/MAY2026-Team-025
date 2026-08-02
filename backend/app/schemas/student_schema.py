from marshmallow import Schema, fields, validate


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
