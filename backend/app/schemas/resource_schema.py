from marshmallow import Schema, fields, validate

from app.models.resource import ResourceType

RESOURCE_TYPES = [t.value for t in ResourceType]


class ResourceUploadSchema(Schema):
    type = fields.String(required=True, validate=validate.OneOf(RESOURCE_TYPES))
    subject_id = fields.Integer(required=True, validate=validate.Range(min=1))
    class_id = fields.Integer(required=True, validate=validate.Range(min=1))
