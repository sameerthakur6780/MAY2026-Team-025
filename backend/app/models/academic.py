from app.extensions import db
from app.models.mixins import TimestampMixin


class SchoolClass(db.Model, TimestampMixin):
    __tablename__ = "classes"
    __table_args__ = (
        db.UniqueConstraint("grade", "section", name="uq_classes_grade_section"),
        db.CheckConstraint("grade >= 1 AND grade <= 12", name="ck_classes_grade_range"),
    )

    id = db.Column(db.Integer, primary_key=True)
    grade = db.Column(db.Integer, nullable=False, index=True)
    section = db.Column(db.String(10), nullable=False)

    students = db.relationship("Student", back_populates="school_class")
    class_subjects = db.relationship(
        "ClassSubjectTeacher", back_populates="school_class", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<SchoolClass grade={self.grade} section={self.section}>"


class Subject(db.Model, TimestampMixin):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True, index=True)

    class_subjects = db.relationship(
        "ClassSubjectTeacher", back_populates="subject", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Subject {self.name}>"


class ClassSubjectTeacher(db.Model, TimestampMixin):
    __tablename__ = "class_subject_teacher"
    __table_args__ = (
        db.UniqueConstraint("class_id", "subject_id", name="uq_cst_class_subject"),
    )

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False, index=True)

    school_class = db.relationship("SchoolClass", back_populates="class_subjects")
    subject = db.relationship("Subject", back_populates="class_subjects")
    teacher = db.relationship("Teacher", back_populates="class_subjects")

    def __repr__(self):
        return f"<ClassSubjectTeacher class={self.class_id} subject={self.subject_id} teacher={self.teacher_id}>"
