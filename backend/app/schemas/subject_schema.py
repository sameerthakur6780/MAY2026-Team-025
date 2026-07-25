from marshmallow import Schema, fields, validate


class SubjectSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=80))
