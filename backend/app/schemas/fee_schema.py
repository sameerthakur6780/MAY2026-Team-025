from marshmallow import Schema, fields, validate


class FeePlanCreateSchema(Schema):
    student_id = fields.Integer(required=True, validate=validate.Range(min=1))
    monthly_amount = fields.Integer(required=True, validate=validate.Range(min=1))
    start_date = fields.Date(required=True)
    active = fields.Boolean(load_default=True)


class FeePlanUpdateSchema(Schema):
    monthly_amount = fields.Integer(validate=validate.Range(min=1))
    start_date = fields.Date()
    active = fields.Boolean()