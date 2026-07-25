from marshmallow import Schema, fields, validate


class StudentUpdateSchema(Schema):

    admission_no = fields.String(validate=validate.Length(max=30))
    dob = fields.Date(allow_none=True)
    gender = fields.String(allow_none=True, validate=validate.Length(max=20))
    class_id = fields.Integer(allow_none=True)
    parent_id = fields.Integer(allow_none=True)
    profile_image = fields.String(allow_none=True, validate=validate.Length(max=255))
    status = fields.String(validate=validate.OneOf(["active", "inactive", "withdrawn"]))
