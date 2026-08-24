from app.extensions import db
from app.models.homework import SubmissionStatus
from app.models.mixins import TimestampMixin
from app.models.test_evaluation import EvaluationStatus, GradedSource


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
    question_paper_resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)
    answer_key_resource_id = db.Column(db.Integer, db.ForeignKey("resources.id"), nullable=True)
    # Nullable at the DB level (existing rows were backfilled to 100 rather
    # than made non-nullable -- see migration), but the create schema
    # requires it going forward. default=100 only covers rows created by
    # code that bypasses the schema (scripts, direct ORM use).
    max_marks = db.Column(db.Integer, nullable=True, default=100)
    evaluation_status = db.Column(
        db.Enum(EvaluationStatus),
        nullable=False,
        default=EvaluationStatus.NOT_SCHEDULED,
        index=True,
    )
    evaluation_scheduled_at = db.Column(db.DateTime, nullable=True)
    evaluation_started_at = db.Column(db.DateTime, nullable=True)
    evaluation_completed_at = db.Column(db.DateTime, nullable=True)
    evaluation_error = db.Column(db.Text, nullable=True)

    school_class = db.relationship("SchoolClass")
    subject = db.relationship("Subject")
    creator = db.relationship("User")
    resource = db.relationship("Resource", foreign_keys=[resource_id])
    question_paper_resource = db.relationship("Resource", foreign_keys=[question_paper_resource_id])
    answer_key_resource = db.relationship("Resource", foreign_keys=[answer_key_resource_id])
    submissions = db.relationship("TestSubmission", back_populates="test", cascade="all, delete-orphan")
    answer_key_questions = db.relationship(
        "TestAnswerKeyQuestion", back_populates="test", cascade="all, delete-orphan"
    )

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
    ai_marks = db.Column(db.Integer, nullable=True)
    ai_feedback = db.Column(db.Text, nullable=True)
    ai_model_used = db.Column(db.String(200), nullable=True)
    ai_graded_at = db.Column(db.DateTime, nullable=True)
    graded_source = db.Column(db.Enum(GradedSource), nullable=True)

    test = db.relationship("Test", back_populates="submissions")
    student = db.relationship("Student")
    grader = db.relationship("User")
    question_scores = db.relationship(
        "TestQuestionScore", back_populates="submission", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<TestSubmission {self.id} test={self.test_id} student={self.student_id} status={self.status.value}>"
