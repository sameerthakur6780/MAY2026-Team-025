import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class EvaluationStatus(str, enum.Enum):
    NOT_SCHEDULED = "not_scheduled"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GradedSource(str, enum.Enum):
    MANUAL = "manual"
    AI = "ai"


class TestAnswerKeyQuestion(db.Model, TimestampMixin):
    __tablename__ = "test_answer_key_questions"
    __table_args__ = (
        db.UniqueConstraint("test_id", "question_no", name="uq_test_answer_key_question_no"),
    )

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("tests.id"), nullable=False, index=True)
    question_no = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    expected_answer = db.Column(db.Text, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)

    test = db.relationship("Test", back_populates="answer_key_questions")
    scores = db.relationship("TestQuestionScore", back_populates="answer_key_question", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestAnswerKeyQuestion {self.id} test={self.test_id} q={self.question_no}>"


class TestQuestionScore(db.Model, TimestampMixin):
    __tablename__ = "test_question_scores"
    __table_args__ = (
        db.UniqueConstraint(
            "submission_id",
            "answer_key_question_id",
            name="uq_test_question_score_submission_question",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("test_submissions.id"), nullable=False, index=True)
    answer_key_question_id = db.Column(
        db.Integer, db.ForeignKey("test_answer_key_questions.id"), nullable=False, index=True
    )
    awarded_marks = db.Column(db.Integer, nullable=False, default=0)
    feedback = db.Column(db.Text)
    student_excerpt = db.Column(db.Text)

    submission = db.relationship("TestSubmission", back_populates="question_scores")
    answer_key_question = db.relationship("TestAnswerKeyQuestion", back_populates="scores")

    def __repr__(self):
        return f"<TestQuestionScore {self.id} submission={self.submission_id} q={self.answer_key_question_id}>"
