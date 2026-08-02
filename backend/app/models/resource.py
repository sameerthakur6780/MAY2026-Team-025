import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class ResourceType(str, enum.Enum):
    NOTE = "note"
    PDF = "pdf"
    IMAGE = "image"
    QUESTION_PAPER = "question_paper"
    ANSWER_KEY = "answer_key"


class Resource(db.Model, TimestampMixin):
    __tablename__ = "resources"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(ResourceType), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    storage_path = db.Column(db.String(500), nullable=False, unique=True)
    filename = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)

    subject = db.relationship("Subject")
    school_class = db.relationship("SchoolClass")
    uploader = db.relationship("User")

    def __repr__(self):
        return f"<Resource {self.id} {self.type.value} class={self.class_id}>"
