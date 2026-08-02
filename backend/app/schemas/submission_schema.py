from marshmallow import Schema, fields, validate


class GradeSchema(Schema):
    """Shared by both homework-submission and test-submission grading --
    the grading action is identical for both, just applied to a different
    table."""

    marks = fields.Integer(required=True, validate=validate.Range(min=0))
    feedback = fields.String(load_default=None, allow_none=True, validate=validate.Length(max=2000))
