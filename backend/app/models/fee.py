import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class FeeStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"


class FeePlan(db.Model, TimestampMixin):
    """A student's recurring monthly fee. StudentFee rows are generated
    from this each cycle (see fee_service.generate_upcoming_student_fees) --
    changing monthly_amount here only affects fees generated after the
    change, not ones already created."""

    __tablename__ = "fee_plans"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    monthly_amount = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    student = db.relationship("Student")
    student_fees = db.relationship("StudentFee", back_populates="fee_plan")

    def __repr__(self):
        return f"<FeePlan {self.id} student={self.student_id} amount={self.monthly_amount}>"


class StudentFee(db.Model, TimestampMixin):
    """One billing cycle's invoice for a student. `amount` is copied from
    the FeePlan at generation time (not a live reference) so a later change
    to the plan's monthly_amount never retroactively alters an already-
    issued invoice."""

    __tablename__ = "student_fees"
    __table_args__ = (
        db.UniqueConstraint("fee_plan_id", "cycle", name="uq_student_fee_plan_cycle"),
    )

    id = db.Column(db.Integer, primary_key=True)
    fee_plan_id = db.Column(db.Integer, db.ForeignKey("fee_plans.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    cycle = db.Column(db.String(7), nullable=False, index=True)  # "YYYY-MM"
    amount = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum(FeeStatus), nullable=False, default=FeeStatus.PENDING, index=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    razorpay_order_id = db.Column(db.String(64), nullable=True, index=True)
    razorpay_payment_id = db.Column(db.String(64), nullable=True)
    transaction_id = db.Column(db.String(64), nullable=True)

    fee_plan = db.relationship("FeePlan", back_populates="student_fees")
    student = db.relationship("Student")

    def __repr__(self):
        return f"<StudentFee {self.id} student={self.student_id} cycle={self.cycle} status={self.status.value}>"