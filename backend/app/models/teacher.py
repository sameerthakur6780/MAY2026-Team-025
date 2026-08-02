from app.extensions import db
from app.models.mixins import TimestampMixin


class Teacher(db.Model, TimestampMixin):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)

    user = db.relationship("User", back_populates="teacher")
    class_subjects = db.relationship(
        "ClassSubjectTeacher", back_populates="teacher", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Teacher {self.id} user_id={self.user_id}>"
