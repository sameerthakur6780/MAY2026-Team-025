from marshmallow import Schema, fields, validate


class AssignmentSchema(Schema):
    class_id = fields.Integer(required=True, validate=validate.Range(min=1))
    subject_id = fields.Integer(required=True, validate=validate.Range(min=1))
    teacher_id = fields.Integer(required=True, validate=validate.Range(min=1))
