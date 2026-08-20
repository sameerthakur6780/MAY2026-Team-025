from marshmallow import Schema, fields, validate


class HomeworkCreateSchema(Schema):
    class_id = fields.Integer(required=True, validate=validate.Range(min=1))
    subject_id = fields.Integer(required=True, validate=validate.Range(min=1))
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    description = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=5000))
    due_date = fields.Date(required=True)
    resource_id = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=1))
    max_marks = fields.Integer(required=True, validate=validate.Range(min=1))


class HomeworkUpdateSchema(Schema):
    class_id = fields.Integer(validate=validate.Range(min=1))
    subject_id = fields.Integer(validate=validate.Range(min=1))
    title = fields.String(validate=validate.Length(min=1, max=200))
    description = fields.String(allow_none=True, validate=validate.Length(max=5000))
    due_date = fields.Date()
    resource_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    max_marks = fields.Integer(validate=validate.Range(min=1))
