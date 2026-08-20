from marshmallow import Schema, fields, validate


class BroadcastSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=255))
    message = fields.String(load_default="", allow_none=True)
    class_id = fields.Integer(load_default=None, allow_none=True)
    priority = fields.String(load_default="medium", validate=validate.OneOf(["high", "medium", "low"]))
