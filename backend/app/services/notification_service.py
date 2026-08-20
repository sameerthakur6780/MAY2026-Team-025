"""Email notification service.

Two primitives, as asked for:
  - send_now(user_id, type_, subject, body): create the row, deliver
    immediately, synchronously, in the caller's thread.
  - schedule(user_id, type_, subject, body, scheduled_at): create the row
    and hand delivery off to the background scheduler for `scheduled_at`.

Everything else here is a set of typed helper methods (notify_*) that build
a consistent subject/body per trigger and call one of the two primitives
above. Trigger call sites (attendance/homework/grading services) use these
instead of hand-rolling message text. notify_fee_due_reminder and
notify_payment_received are fully working today even though nothing calls
them yet -- there's no Fee/Payment model in this codebase. The payments
module can call them directly once it exists; nothing here needs to change.

Both primitives funnel through _deliver(), which claims the notification
(PENDING -> SENDING) with a single atomic UPDATE before actually sending --
see _claim_for_sending(). That's what keeps two worker processes from both
delivering the same notification if init_scheduler()'s startup catch-up
ever re-registers the same pending row in more than one process at once.
"""
import logging
import os
from datetime import datetime, timezone

from app.extensions import db, scheduler
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.student import Student
from app.models.user import User
from app.services.email import get_email_service
from app.services.email_service import EmailSendError
from app.utils.errors import not_found

logger = logging.getLogger(__name__)

_app = None  # set by init_scheduler(); scheduled jobs run outside any request context


def _utcnow():
    return datetime.now(timezone.utc)


def _job_id(notification_id):
    return f"notification-{notification_id}"


def _claim_for_sending(notification_id):
    """Atomically transitions one notification from PENDING to SENDING.

    A single `UPDATE ... WHERE id=? AND status='pending'` -- whichever
    caller's UPDATE actually matches the row wins the claim. Every other
    concurrent caller (another thread, or another worker process that
    re-registered the same job via init_scheduler()'s startup catch-up)
    gets 0 rows affected and backs off without sending anything. This is
    what makes delivery safe even if the same notification ends up
    scheduled in two processes at once; see the single-worker note on
    `scheduler` in extensions.py for what this does and doesn't cover.

    Returns True if this call won the claim, False otherwise.
    """
    affected = Notification.query.filter_by(id=notification_id, status=NotificationStatus.PENDING).update(
        {"status": NotificationStatus.SENDING}, synchronize_session=False
    )
    db.session.commit()
    return affected == 1


def _deliver(notification):
    if not _claim_for_sending(notification.id):
        # Lost the race (or there was never anything to send) -- another
        # caller already has it, or already finished it. Quietly do nothing.
        return notification

    user = User.query.get(notification.user_id)
    if user is None:
        notification.status = NotificationStatus.FAILED
        notification.error_message = "Recipient user no longer exists"
        db.session.commit()
        return notification

    try:
        get_email_service().send(user.email, notification.subject, notification.body)
    except EmailSendError as exc:
        # FAILED is terminal, not retried -- both the pre-check in
        # _run_scheduled_notification and the claim above only ever match
        # PENDING rows, so a FAILED notification is never picked up again.
        # (A bounded-retry state was the other option here; skipped since it
        # would need a new retry-count column and backoff policy this
        # codebase doesn't have anywhere else yet.)
        notification.status = NotificationStatus.FAILED
        notification.error_message = str(exc)
        db.session.commit()
        return notification

    notification.status = NotificationStatus.SENT
    notification.sent_at = _utcnow()
    db.session.commit()
    return notification


def _run_scheduled_notification(notification_id):
    """APScheduler job target. Runs on the scheduler's own thread, with no
    Flask request/app context of its own -- has to push one itself."""
    with _app.app_context():
        notification = Notification.query.get(notification_id)
        if notification is None or notification.status != NotificationStatus.PENDING:
            return  # already delivered, failed, or deleted -- nothing to do
        try:
            _deliver(notification)
        except Exception:
            logger.exception("Unexpected error delivering scheduled notification %s", notification_id)


def _register_job(notification):
    scheduler.add_job(
        func=_run_scheduled_notification,
        trigger="date",
        run_date=notification.scheduled_at,
        args=[notification.id],
        id=_job_id(notification.id),
        replace_existing=True,
        # No grace-time cutoff: if the app was down when scheduled_at passed,
        # fire it as soon as the scheduler comes back up rather than
        # silently dropping it (APScheduler's default is to skip "missed"
        # jobs older than 1 second).
        misfire_grace_time=None,
    )


def init_scheduler(app):
    """Starts the background scheduler and re-registers any notifications
    that were scheduled but never fired (e.g. the process restarted while
    one was pending) -- the in-memory job store forgets jobs across
    restarts, the `notifications` table doesn't."""
    global _app

    if not app.config.get("SCHEDULER_ENABLED", True):
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # Flask's reloader runs a parent watcher process in addition to the
        # real worker; only the worker (which sets this env var) should run
        # jobs, or every scheduled email would be sent twice.
        return

    _app = app
    if not scheduler.running:
        scheduler.start()

    with app.app_context():
        try:
            pending = Notification.query.filter(
                Notification.status == NotificationStatus.PENDING,
                Notification.scheduled_at.isnot(None),
            ).all()
        except Exception:
            # Most likely the `notifications` table doesn't exist yet (e.g.
            # this is `flask db upgrade` creating it for the first time, and
            # `create_app()` runs before that finishes). Nothing to
            # reschedule in that case -- move on rather than crash startup.
            logger.info("Skipping scheduled-notification catch-up: could not query notifications table yet")
            return
        for notification in pending:
            _register_job(notification)


class NotificationService:
    @staticmethod
    def send_now(user_id, type_, subject, body):
        """Creates the Notification row and delivers it immediately,
        synchronously. Use for single-recipient, low-volume triggers where
        blocking the caller for one email round-trip is a non-issue."""
        if User.query.get(user_id) is None:
            raise not_found("User")

        notification = Notification(
            user_id=user_id,
            type=NotificationType(type_),
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING,
            scheduled_at=None,
        )
        db.session.add(notification)
        db.session.commit()
        return _deliver(notification)

    @staticmethod
    def schedule(user_id, type_, subject, body, scheduled_at):
        """Creates the Notification row and hands delivery to the
        background scheduler for `scheduled_at`. Use for future-dated sends
        (reminders) or to get bulk/fan-out sends (e.g. a whole class) off
        the request thread -- pass `scheduled_at=now` for "soon, but not on
        this request"."""
        if User.query.get(user_id) is None:
            raise not_found("User")

        notification = Notification(
            user_id=user_id,
            type=NotificationType(type_),
            subject=subject,
            body=body,
            status=NotificationStatus.PENDING,
            scheduled_at=scheduled_at,
        )
        db.session.add(notification)
        db.session.commit()
        _register_job(notification)
        return notification

    # ------------------------------------------------------------------
    # Typed helpers -- consistent subject/body per trigger. Existing and
    # future call sites use these rather than hand-formatting messages.
    # ------------------------------------------------------------------

    @staticmethod
    def notify_attendance_absent(student, absence_date):
        if student.parent is None:
            return None  # no linked parent account to notify

        grade = student.school_class.grade if student.school_class else "N/A"
        subject = f"{student.user.full_name} was marked absent on {absence_date.isoformat()}"
        body = (
            f"Hi {student.parent.user.full_name},\n\n"
            f"{student.user.full_name} was marked absent in Grade {grade} on {absence_date.isoformat()}.\n\n"
            f"- SmartBatch"
        )
        return NotificationService.send_now(student.parent.user_id, NotificationType.ATTENDANCE_ABSENT, subject, body)

    @staticmethod
    def notify_homework_assigned(homework, student_ids):
        """Scheduled for "now" rather than sent inline: fanning out to a
        whole class of students shouldn't make the create-homework request
        wait on N synchronous SMTP round-trips."""
        subject = f"New homework: {homework.title}"
        body = (
            f"New homework \"{homework.title}\" ({homework.subject.name}) has been assigned "
            f"to Grade {homework.school_class.grade}, due {homework.due_date.isoformat()}.\n\n"
            f"- SmartBatch"
        )
        now = _utcnow()
        notifications = []
        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student is None:
                continue
            notifications.append(
                NotificationService.schedule(student.user_id, NotificationType.HOMEWORK_ASSIGNED, subject, body, now)
            )
        return notifications

    @staticmethod
    def notify_marks_published(student, item_kind, item_title, subject_name, marks):
        """item_kind is just for the message wording, e.g. "homework" or
        "test". Notifies the student and, if linked, their parent."""
        subject = f"Marks published: {item_title}"
        body = (
            f"Marks for the {item_kind} \"{item_title}\" ({subject_name}) have been published: {marks}.\n\n"
            f"- SmartBatch"
        )
        recipient_ids = [student.user_id]
        if student.parent is not None:
            recipient_ids.append(student.parent.user_id)
        return [
            NotificationService.send_now(uid, NotificationType.MARKS_PUBLISHED, subject, body)
            for uid in recipient_ids
        ]

    @staticmethod
    def _fee_due_reminder_content(amount, due_date, cycle_label=None):
        cycle_note = f" ({cycle_label})" if cycle_label else ""
        subject = "Fee payment due soon"
        body = (
            f"A fee payment of Rs. {amount}{cycle_note} is due on {due_date}. "
            f"Please pay before the due date to avoid a late fee.\n\n"
            f"- SmartBatch"
        )
        return subject, body

    @staticmethod
    def notify_fee_due_reminder(parent_user_id, amount, due_date, cycle_label=None):
        """Sends immediately -- call this on the day the reminder should
        actually go out."""
        subject, body = NotificationService._fee_due_reminder_content(amount, due_date, cycle_label)
        return NotificationService.send_now(parent_user_id, NotificationType.FEE_DUE_REMINDER, subject, body)

    @staticmethod
    def schedule_fee_due_reminder(parent_user_id, amount, due_date, scheduled_at, cycle_label=None):
        """Same reminder content as notify_fee_due_reminder, but handed to
        the background scheduler for `scheduled_at` instead of sent right
        away. fee_service calls this at StudentFee-creation time with
        scheduled_at = due_date - 3 days, so the reminder is queued well
        before the due date rather than requiring a second job to notice
        "3 days out" has arrived."""
        subject, body = NotificationService._fee_due_reminder_content(amount, due_date, cycle_label)
        return NotificationService.schedule(
            parent_user_id, NotificationType.FEE_DUE_REMINDER, subject, body, scheduled_at
        )

    @staticmethod
    def notify_payment_received(parent_user_id, amount, receipt_no=None):
        """STUB call site, same as notify_fee_due_reminder -- ready for the
        payments module to call directly from a successful payment
        confirmation/webhook handler."""
        receipt_note = f" (receipt #{receipt_no})" if receipt_no else ""
        subject = "Payment received"
        body = f"We've received your payment of Rs. {amount}{receipt_note}. Thank you!\n\n- SmartBatch"
        return NotificationService.send_now(parent_user_id, NotificationType.PAYMENT_RECEIVED, subject, body)