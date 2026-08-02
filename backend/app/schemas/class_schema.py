from marshmallow import Schema, fields, validate


class ClassSchema(Schema):
    grade = fields.Integer(required=True, validate=validate.Range(min=1, max=12))
