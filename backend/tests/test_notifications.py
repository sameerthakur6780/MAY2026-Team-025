"""NotificationService (send_now/schedule) and the trigger points wired
into attendance/homework/grading. fee_due_reminder/payment_received have no
caller yet (no Fee/Payment model exists) -- tested directly to prove
they're fully functional and ready for that module to call."""
import time
from datetime import date, datetime, timedelta, timezone

from conftest import (
    create_admin_user,
    create_class,
    create_parent,
    create_student,
    create_subject,
    create_teacher,
)

import app.services.notification_service as notification_service
from app.extensions import db, mail, scheduler
from app.models.homework import Homework, Submission, SubmissionStatus
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.models.test import Test, TestSubmission
from app.services.email_service import EmailSendError
from app.services.homework_submission_service import grade_submission as grade_homework_submission
from app.services.notification_service import NotificationService, init_scheduler
from app.services.test_submission_service import grade_submission as grade_test_submission
from app.utils.errors import ApiError

# ---------------------------------------------------------------------------
# NotificationService.send_now
# ---------------------------------------------------------------------------


def test_send_now_creates_and_delivers(app):
    with app.app_context():
        user = create_admin_user()

        with mail.record_messages() as outbox:
            notification = NotificationService.send_now(
                user.id, NotificationType.PAYMENT_RECEIVED, "Subject line", "Body text"
            )

        assert notification.status == NotificationStatus.SENT
        assert notification.sent_at is not None
        assert notification.error_message is None
        assert notification.scheduled_at is None

        assert len(outbox) == 1
        assert outbox[0].subject == "Subject line"
        assert outbox[0].body == "Body text"
        assert outbox[0].recipients == [user.email]

        stored = Notification.query.get(notification.id)
        assert stored.user_id == user.id
        assert stored.type == NotificationType.PAYMENT_RECEIVED


def test_send_now_marks_failed_when_email_service_raises(app, monkeypatch):
    with app.app_context():
        user = create_admin_user()

        class _FailingEmailService:
            def send(self, to_email, subject, body):
                raise EmailSendError("smtp connection refused")

        monkeypatch.setattr(
            "app.services.notification_service.get_email_service", lambda: _FailingEmailService()
        )

        notification = NotificationService.send_now(user.id, NotificationType.PAYMENT_RECEIVED, "X", "Y")
        assert notification.status == NotificationStatus.FAILED
        assert notification.sent_at is None
        assert "smtp connection refused" in notification.error_message


def test_send_now_unknown_user_raises_not_found(app):
    with app.app_context():
        try:
            NotificationService.send_now(999999, NotificationType.PAYMENT_RECEIVED, "X", "Y")
            assert False, "expected ApiError"
        except ApiError as exc:
            assert exc.code == "not_found"


# ---------------------------------------------------------------------------
# NotificationService.schedule
# ---------------------------------------------------------------------------


def test_schedule_creates_pending_row_and_registers_job(app):
    with app.app_context():
        user = create_admin_user()
        run_at = datetime.now(timezone.utc) + timedelta(hours=1)

        notification = NotificationService.schedule(
            user.id, NotificationType.FEE_DUE_REMINDER, "Due soon", "Pay up", run_at
        )

        assert notification.status == NotificationStatus.PENDING
        # SQLite drops tzinfo on round-trip (same as TimestampMixin elsewhere
        # in this codebase) -- db.session.commit()'s default expire-on-commit
        # means the attribute read above already went through that round-trip.
        assert notification.scheduled_at == run_at.replace(tzinfo=None)
        assert notification.sent_at is None

        # The scheduler isn't started in this test (SCHEDULER_ENABLED=False),
        # so there's no next_run_time yet -- the trigger's run_date is what
        # add_job() was actually given, checked here instead.
        job = scheduler.get_job(f"notification-{notification.id}")
        assert job is not None
        assert job.trigger.run_date == run_at
        assert job.args == (notification.id,)
        scheduler.remove_job(job.id)  # scheduler is a shared, process-wide singleton -- don't leak jobs


def test_schedule_unknown_user_raises_not_found(app):
    with app.app_context():
        try:
            NotificationService.schedule(
                999999, NotificationType.FEE_DUE_REMINDER, "X", "Y", datetime.now(timezone.utc)
            )
            assert False, "expected ApiError"
        except ApiError as exc:
            assert exc.code == "not_found"


def test_schedule_actually_fires_via_background_scheduler(app):
    """The one true end-to-end test: really starts the scheduler, really
    waits for its background thread to fire the job, confirms the row
    lands on SENT. Everything else tests the pieces in isolation; this
    proves they're wired together correctly."""
    with app.app_context():
        user = create_admin_user()
        app.config["SCHEDULER_ENABLED"] = True
        try:
            init_scheduler(app)
            run_at = datetime.now(timezone.utc) + timedelta(milliseconds=200)

            with mail.record_messages() as outbox:
                notification = NotificationService.schedule(
                    user.id, NotificationType.FEE_DUE_REMINDER, "Due soon", "Pay up", run_at
                )

                terminal = {NotificationStatus.SENT, NotificationStatus.FAILED}
                deadline = time.time() + 5
                while time.time() < deadline and notification.status not in terminal:
                    # Not just "!= PENDING": there's now a brief SENDING
                    # window in between (see _claim_for_sending) that this
                    # loop must not mistake for "done".
                    time.sleep(0.05)
                    db.session.refresh(notification)

            assert notification.status == NotificationStatus.SENT
            assert notification.sent_at is not None
            assert len(outbox) == 1
            assert outbox[0].subject == "Due soon"
        finally:
            scheduler.remove_all_jobs()
            if scheduler.running:
                scheduler.shutdown(wait=False)
            notification_service._app = None
            app.config["SCHEDULER_ENABLED"] = False


# ---------------------------------------------------------------------------
# Trigger: attendance marked absent
# ---------------------------------------------------------------------------


def test_bulk_mark_absent_notifies_linked_parent(admin, app):
    school_class = create_class(1)
    parent_row = create_parent()
    student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)

    with mail.record_messages() as outbox:
        resp = admin.post(
            "/api/attendance/bulk",
            json={
                "class_id": school_class.id,
                "date": "2026-01-15",
                "entries": [{"student_id": student_row.id, "status": "absent"}],
            },
        )
    assert resp.status_code == 201

    with app.app_context():
        notifications = Notification.query.filter_by(
            user_id=parent_row.user_id, type=NotificationType.ATTENDANCE_ABSENT
        ).all()
        assert len(notifications) == 1
        assert notifications[0].status == NotificationStatus.SENT
        assert student_row.user.full_name in notifications[0].subject
    assert len(outbox) == 1
    assert outbox[0].recipients == [parent_row.user.email]


def test_bulk_mark_present_does_not_notify(admin, app):
    school_class = create_class(1)
    parent_row = create_parent()
    student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)

    resp = admin.post(
        "/api/attendance/bulk",
        json={
            "class_id": school_class.id,
            "date": "2026-01-15",
            "entries": [{"student_id": student_row.id, "status": "present"}],
        },
    )
    assert resp.status_code == 201

    with app.app_context():
        assert Notification.query.count() == 0


def test_bulk_mark_absent_without_linked_parent_does_not_crash(admin, app):
    school_class = create_class(1)
    student_row = create_student(class_id=school_class.id)  # no parent_id

    resp = admin.post(
        "/api/attendance/bulk",
        json={
            "class_id": school_class.id,
            "date": "2026-01-15",
            "entries": [{"student_id": student_row.id, "status": "absent"}],
        },
    )
    assert resp.status_code == 201  # marking attendance must succeed regardless

    with app.app_context():
        assert Notification.query.count() == 0


# ---------------------------------------------------------------------------
# Trigger: homework assigned
# ---------------------------------------------------------------------------


def test_create_homework_schedules_notification_for_each_enrolled_student(admin, app):
    school_class = create_class(2)
    subject = create_subject("Science")
    s1 = create_student(class_id=school_class.id)
    s2 = create_student(class_id=school_class.id)
    other_class = create_class(3)
    outside_student = create_student(class_id=other_class.id)

    resp = admin.post(
        "/api/homework",
        json={
            "class_id": school_class.id,
            "subject_id": subject.id,
            "title": "Chapter 4 worksheet",
            "due_date": "2026-02-01",
        },
    )
    assert resp.status_code == 201

    with app.app_context():
        notifications = Notification.query.filter_by(type=NotificationType.HOMEWORK_ASSIGNED).all()
        notified_user_ids = {n.user_id for n in notifications}
        assert notified_user_ids == {s1.user_id, s2.user_id}
        assert outside_student.user_id not in notified_user_ids
        for n in notifications:
            # Scheduled for "now" via the background scheduler (disabled in
            # tests) rather than sent inline -- see notify_homework_assigned.
            assert n.status == NotificationStatus.PENDING
            assert n.scheduled_at is not None
            assert "Chapter 4 worksheet" in n.subject
            job = scheduler.get_job(f"notification-{n.id}")
            assert job is not None
            scheduler.remove_job(job.id)


# ---------------------------------------------------------------------------
# Trigger: marks published (homework + test submissions)
# ---------------------------------------------------------------------------


def test_grade_homework_submission_notifies_student_and_parent(app):
    with app.app_context():
        school_class = create_class(4)
        subject = create_subject("English")
        teacher_row = create_teacher()
        parent_row = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)

        homework = Homework(
            class_id=school_class.id,
            subject_id=subject.id,
            title="Essay",
            due_date=date(2026, 3, 1),
            created_by=teacher_row.user_id,
        )
        db.session.add(homework)
        db.session.commit()

        submission = Submission(
            homework_id=homework.id,
            student_id=student_row.id,
            file_url="submissions/1/essay.pdf",
            submitted_at=datetime.now(timezone.utc),
            status=SubmissionStatus.PENDING,
        )
        db.session.add(submission)
        db.session.commit()

        with mail.record_messages() as outbox:
            grade_homework_submission(submission.id, 85, "Great work", teacher_row.user_id)

        notifications = Notification.query.filter_by(type=NotificationType.MARKS_PUBLISHED).all()
        assert {n.user_id for n in notifications} == {student_row.user_id, parent_row.user_id}
        assert all(n.status == NotificationStatus.SENT for n in notifications)
        assert all("Essay" in n.subject for n in notifications)
        assert len(outbox) == 2


def test_grade_test_submission_notifies_only_student_when_no_parent_linked(app):
    with app.app_context():
        school_class = create_class(5)
        subject = create_subject("Maths")
        teacher_row = create_teacher()
        student_row = create_student(class_id=school_class.id)  # no parent linked

        test_row = Test(
            class_id=school_class.id,
            subject_id=subject.id,
            title="Unit Test 1",
            due_date=date(2026, 3, 5),
            created_by=teacher_row.user_id,
        )
        db.session.add(test_row)
        db.session.commit()

        submission = TestSubmission(
            test_id=test_row.id,
            student_id=student_row.id,
            file_url="test-submissions/1/answers.pdf",
            submitted_at=datetime.now(timezone.utc),
            status=SubmissionStatus.PENDING,
        )
        db.session.add(submission)
        db.session.commit()

        grade_test_submission(submission.id, 42, None, teacher_row.user_id)

        notifications = Notification.query.filter_by(type=NotificationType.MARKS_PUBLISHED).all()
        assert {n.user_id for n in notifications} == {student_row.user_id}


# ---------------------------------------------------------------------------
# Fee/payment stubs -- no Fee/Payment model exists in this codebase yet, so
# nothing calls these today. Tested directly to prove they're fully working
# now, ready for that module to call with no changes needed here.
# ---------------------------------------------------------------------------


def test_notify_fee_due_reminder_is_fully_functional(app):
    with app.app_context():
        parent_row = create_parent()

        with mail.record_messages() as outbox:
            notification = NotificationService.notify_fee_due_reminder(
                parent_row.user_id, 5000, date(2026, 4, 1), cycle_label="Term 2"
            )

        assert notification.status == NotificationStatus.SENT
        assert notification.type == NotificationType.FEE_DUE_REMINDER
        assert "5000" in notification.body
        assert "Term 2" in notification.body
        assert len(outbox) == 1


def test_notify_payment_received_is_fully_functional(app):
    with app.app_context():
        parent_row = create_parent()

        with mail.record_messages() as outbox:
            notification = NotificationService.notify_payment_received(parent_row.user_id, 5000, receipt_no="R-1001")

        assert notification.status == NotificationStatus.SENT
        assert notification.type == NotificationType.PAYMENT_RECEIVED
        assert "R-1001" in notification.body
        assert len(outbox) == 1