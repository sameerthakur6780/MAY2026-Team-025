from app.extensions import db
from app.models.homework import SubmissionStatus
from app.models.mixins import TimestampMixin


class Test(db.Model, TimestampMixin):
    __tablename__ = "tests"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)

    school_class = db.relationship("SchoolClass")
    subject = db.relationship("Subject")
    creator = db.relationship("User")
    resource = db.relationship("Resource")
    submissions = db.relationship("TestSubmission", back_populates="test", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.id} {self.title!r} class={self.class_id}>"


class TestSubmission(db.Model, TimestampMixin):
    __tablename__ = "test_submissions"
    __table_args__ = (
        db.UniqueConstraint("test_id", "student_id", name="uq_test_submission_test_student"),
    )

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    file_url = db.Column(db.String(500), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False)
    marks = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    graded_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.Enum(SubmissionStatus), nullable=False, default=SubmissionStatus.PENDING, index=True)

    test = db.relationship("Test", back_populates="submissions")
    student = db.relationship("Student")
    grader = db.relationship("User")

    def __repr__(self):
        return f"<TestSubmission {self.id} test={self.test_id} student={self.student_id} status={self.status.value}>"
