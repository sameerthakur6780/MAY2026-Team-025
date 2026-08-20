from marshmallow import Schema, fields, validate

from app.models.user import RoleEnum
from app.utils.validators import INDIAN_PHONE_ERROR, INDIAN_PHONE_REGEX

CREATABLE_ROLES = [RoleEnum.TEACHER.value, RoleEnum.PARENT.value, RoleEnum.STUDENT.value]


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1))


class SignupSchema(Schema):
    role = fields.String(required=True, validate=validate.OneOf(CREATABLE_ROLES))
    full_name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=6))
    phone = fields.String(required=True, validate=validate.Regexp(INDIAN_PHONE_REGEX, error=INDIAN_PHONE_ERROR))

    # student-only
    admission_no = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=30))
    dob = fields.Date(load_default=None, allow_none=True)
    gender = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=20))
    class_id = fields.Integer(load_default=None, allow_none=True)
    parent_id = fields.Integer(load_default=None, allow_none=True)

    # parent-only
    occupation = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=120))
    address = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=255))
