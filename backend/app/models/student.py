from app.extensions import db
from app.models.mixins import TimestampMixin


class Student(db.Model, TimestampMixin):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    admission_no = db.Column(db.String(30), nullable=False, unique=True, index=True)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id"), index=True)
    profile_image = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="active")
    # 128/2622/512-d (model-dependent) face embedding computed once when the
    # profile photo is uploaded -- see app/services/facial_recognition.
    # Never recomputed on read; only replaced when the photo changes.
    face_embedding = db.Column(db.JSON, nullable=True)

    user = db.relationship("User", back_populates="student")
    school_class = db.relationship("SchoolClass", back_populates="students")
    parent = db.relationship("Parent", back_populates="students")

    def __repr__(self):
        return f"<Student {self.id} admission_no={self.admission_no}>"
