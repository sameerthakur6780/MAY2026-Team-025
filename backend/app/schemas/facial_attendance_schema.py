from marshmallow import Schema, fields, validate


class FacialAttendanceSchema(Schema):
    class_id = fields.Integer(required=True, validate=validate.Range(min=1))
    date = fields.Date(required=True)
