from marshmallow import Schema, fields, validate


class ParentUpdateSchema(Schema):
    occupation = fields.String(allow_none=True, validate=validate.Length(max=120))
    address = fields.String(allow_none=True, validate=validate.Length(max=255))
