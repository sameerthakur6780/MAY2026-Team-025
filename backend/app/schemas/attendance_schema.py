from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.models.attendance import AttendanceMethod, AttendanceStatus

STATUS_VALUES = [s.value for s in AttendanceStatus]
METHOD_VALUES = [m.value for m in AttendanceMethod]


class AttendanceEntrySchema(Schema):
    student_id = fields.Integer(required=True, validate=validate.Range(min=1))
    status = fields.String(required=True, validate=validate.OneOf(STATUS_VALUES))


class AttendanceBulkSchema(Schema):
    class_id = fields.Integer(required=True, validate=validate.Range(min=1))
    date = fields.Date(required=True)
    method = fields.String(load_default=AttendanceMethod.MANUAL.value, validate=validate.OneOf(METHOD_VALUES))
    entries = fields.List(fields.Nested(AttendanceEntrySchema), required=True, validate=validate.Length(min=1))

    @validates_schema
    def validate_unique_students(self, data, **kwargs):
        entries = data.get("entries") or []
        student_ids = [e["student_id"] for e in entries]
        if len(student_ids) != len(set(student_ids)):
            raise ValidationError("entries contains the same student_id more than once", field_name="entries")


class AttendanceUpdateSchema(Schema):
    status = fields.String(validate=validate.OneOf(STATUS_VALUES))
    method = fields.String(validate=validate.OneOf(METHOD_VALUES))
