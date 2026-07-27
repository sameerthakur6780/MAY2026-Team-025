import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"


class AttendanceMethod(str, enum.Enum):
    MANUAL = "manual"
    FACIAL = "facial"


class Attendance(db.Model, TimestampMixin):
    __tablename__ = "attendance"
    __table_args__ = (
        db.UniqueConstraint("student_id", "class_id", "date", name="uq_attendance_student_class_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    marked_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    method = db.Column(db.Enum(AttendanceMethod), nullable=False, default=AttendanceMethod.MANUAL)

    student = db.relationship("Student")
    school_class = db.relationship("SchoolClass")
    marker = db.relationship("User")

    def __repr__(self):
        return f"<Attendance student={self.student_id} class={self.class_id} date={self.date} status={self.status.value}>"
