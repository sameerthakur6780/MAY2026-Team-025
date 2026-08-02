from marshmallow import Schema


class TeacherUpdateSchema(Schema):
    """The teachers table currently holds no editable fields of its own
        (name/email/password live on the linked user account, out of scope
        here; subject/class assignment is managed via class_subject_teacher,
        which isn't one of the resources built in this pass). Kept as an empty
        schema so unknown fields still get rejected with a clear 400 instead of
        silently doing nothing."""
