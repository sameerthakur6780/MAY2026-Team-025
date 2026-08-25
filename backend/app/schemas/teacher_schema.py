from marshmallow import Schema, fields, validate

from app.utils.validators import INDIAN_PHONE_ERROR, INDIAN_PHONE_REGEX


class TeacherUpdateSchema(Schema):
    full_name = fields.String(validate=validate.Length(min=1, max=120))
    email = fields.Email()
    phone = fields.String(allow_none=True, validate=validate.Regexp(INDIAN_PHONE_REGEX, error=INDIAN_PHONE_ERROR))
    subject_id = fields.Integer(validate=validate.Range(min=1))
    class_ids = fields.List(fields.Integer(validate=validate.Range(min=1)))
