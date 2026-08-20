import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class NotificationType(str, enum.Enum):
    ATTENDANCE_ABSENT = "attendance_absent"
    HOMEWORK_ASSIGNED = "homework_assigned"
    MARKS_PUBLISHED = "marks_published"
    FEE_DUE_REMINDER = "fee_due_reminder"
    PAYMENT_RECEIVED = "payment_received"
    ANNOUNCEMENT = "announcement"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    # Transient claimed-but-not-yet-delivered state. A row sits here only for
    # the duration of one delivery attempt -- see
    # notification_service._claim_for_sending for why this exists: it's the
    # target of the atomic "claim" UPDATE that keeps two worker processes
    # from both sending the same notification.
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class Notification(db.Model, TimestampMixin):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.Enum(NotificationType), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    # Optional HTML alternative rendered from an app/templates/email/*.html
    # template at creation time (see NotificationService._render_email_html).
    # Stored rather than re-rendered at delivery time so a scheduled
    # notification still has it after a process restart re-registers the job.
    html_body = db.Column(db.Text, nullable=True)
    status = db.Column(db.Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING, index=True)
    # NULL scheduled_at means "send as soon as possible" (send_now()).
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    # Not in the original field list -- added so a FAILED row is debuggable
    # instead of just a dead end. Nullable, never required.
    error_message = db.Column(db.Text, nullable=True)

    user = db.relationship("User")

    def __repr__(self):
        return f"<Notification {self.id} user={self.user_id} type={self.type.value} status={self.status.value}>"