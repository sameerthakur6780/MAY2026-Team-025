import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    GRADED = "graded"


class Homework(db.Model, TimestampMixin):
    __tablename__ = "homework"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)
    # Nullable at the DB level (existing rows were backfilled to 100 rather
    # than made non-nullable -- see migration), but the create schema
    # requires it going forward. default=100 only covers rows created by
    # code that bypasses the schema (scripts, direct ORM use).
    max_marks = db.Column(db.Integer, nullable=True, default=100)

    school_class = db.relationship("SchoolClass")
    subject = db.relationship("Subject")
    creator = db.relationship("User")
    resource = db.relationship("Resource")
    submissions = db.relationship("Submission", back_populates="homework", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Homework {self.id} {self.title!r} class={self.class_id}>"


class Submission(db.Model, TimestampMixin):
    __tablename__ = "submissions"
    __table_args__ = (
        db.UniqueConstraint("homework_id", "student_id", name="uq_submission_homework_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    homework_id = db.Column(db.Integer, db.ForeignKey("homework.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    file_url = db.Column(db.String(500), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    marks = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    graded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.PENDING, index=True)

    homework = db.relationship("Homework", back_populates="submissions")
    student = db.relationship("Student")
    grader = db.relationship("User")

    def __repr__(self):
        return f"<Submission {self.id} homework={self.homework_id} student={self.student_id} status={self.status.value}>"
