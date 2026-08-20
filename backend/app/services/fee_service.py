"""FeePlan CRUD, StudentFee listing/payment, and the two recurring jobs that
keep fee records current without an admin manually creating them:

  - generate_upcoming_student_fees(): creates next month's StudentFee for
    every active FeePlan, a few days before that month starts (see
    init_fee_scheduler's CronTrigger). Idempotent -- safe to call more than
    once for the same cycle (the fee_plan_id+cycle unique constraint is the
    real guard; the pre-check here just avoids relying on catching an
    IntegrityError for the common case).
  - mark_overdue_fees(): daily sweep, PENDING -> OVERDUE for anything past
    its due_date.

Both run on the same shared `scheduler` singleton notification_service.py
uses -- see init_fee_scheduler for the reloader-guard/single-worker
reasoning, which applies identically here.
"""
import calendar
import logging
import os
from datetime import date, datetime, time, timedelta, timezone

from apscheduler.triggers.cron import CronTrigger
from flask import current_app
from sqlalchemy import false

from app.extensions import db, scheduler
from app.models.fee import FeePlan, FeeStatus, StudentFee
from app.models.student import Student
from app.services import razorpay_service
from app.services.notification_service import NotificationService
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent

logger = logging.getLogger(__name__)

_app = None  # set by init_fee_scheduler(); cron jobs run outside any request context


def _utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def serialize_fee_plan(plan):
    return {
        "id": plan.id,
        "student_id": plan.student_id,
        "student_name": plan.student.user.full_name,
        "monthly_amount": plan.monthly_amount,
        "start_date": plan.start_date.isoformat(),
        "active": plan.active,
        "created_at": plan.created_at.isoformat(),
        "updated_at": plan.updated_at.isoformat(),
    }


def serialize_student_fee(fee):
    return {
        "id": fee.id,
        "fee_plan_id": fee.fee_plan_id,
        "student_id": fee.student_id,
        "student_name": fee.student.user.full_name,
        "cycle": fee.cycle,
        "amount": fee.amount,
        "due_date": fee.due_date.isoformat(),
        "status": fee.status.value,
        "paid_at": fee.paid_at.isoformat() if fee.paid_at else None,
        "razorpay_order_id": fee.razorpay_order_id,
        "razorpay_payment_id": fee.razorpay_payment_id,
        "transaction_id": fee.transaction_id,
        "created_at": fee.created_at.isoformat(),
        "updated_at": fee.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# FeePlan CRUD (admin)
# ---------------------------------------------------------------------------


def get_fee_plan_or_404(plan_id):
    plan = FeePlan.query.get(plan_id)
    if plan is None:
        raise not_found("FeePlan")
    return plan


def list_fee_plans_query(student_id=None):
    query = FeePlan.query
    if student_id is not None:
        query = query.filter_by(student_id=student_id)
    return query.order_by(FeePlan.created_at.desc())


def create_fee_plan(data):
    if Student.query.get(data["student_id"]) is None:
        raise not_found("Student")

    plan = FeePlan(
        student_id=data["student_id"],
        monthly_amount=data["monthly_amount"],
        start_date=data["start_date"],
        active=data.get("active", True),
    )
    db.session.add(plan)
    db.session.commit()

    # generate_upcoming_student_fees() (the recurring job) only ever creates
    # *next* month's cycle -- without this, a plan created today wouldn't
    # produce a payable invoice until FEE_GENERATION_DAY_OF_MONTH next runs.
    # A student a plan is created for today should be billed for their
    # starting cycle today.
    generate_initial_fee(plan)
    return plan


def generate_initial_fee(plan):
    """Creates the StudentFee for `plan`'s own starting cycle if one doesn't
    already exist. Safe to call more than once for the same plan (the
    fee_plan_id+cycle unique constraint plus the pre-check guard the same
    way generate_upcoming_student_fees() does)."""
    cycle = f"{plan.start_date.year:04d}-{plan.start_date.month:02d}"
    if StudentFee.query.filter_by(fee_plan_id=plan.id, cycle=cycle).first() is not None:
        return None

    fee = StudentFee(
        fee_plan_id=plan.id,
        student_id=plan.student_id,
        cycle=cycle,
        amount=plan.monthly_amount,
        due_date=_due_date_for(plan.start_date.year, plan.start_date.month),
        status=FeeStatus.PENDING,
    )
    db.session.add(fee)
    db.session.commit()
    _schedule_fee_reminder(fee)
    return fee


def update_fee_plan(plan_id, data):
    plan = get_fee_plan_or_404(plan_id)
    for field in ("monthly_amount", "start_date", "active"):
        if field in data:
            setattr(plan, field, data[field])
    db.session.commit()
    return plan


def delete_fee_plan(plan_id):
    plan = get_fee_plan_or_404(plan_id)
    if plan.student_fees:
        raise ApiError(
            f"Cannot delete: {len(plan.student_fees)} fee record(s) already exist for this plan "
            "-- deactivate it instead",
            "conflict",
            409,
        )
    db.session.delete(plan)
    db.session.commit()


# ---------------------------------------------------------------------------
# StudentFee listing + scoping (admin, parent)
# ---------------------------------------------------------------------------


def get_fee_or_404(fee_id):
    fee = StudentFee.query.get(fee_id)
    if fee is None:
        raise not_found("StudentFee")
    return fee


def get_fee_scoped(fee_id, role):
    fee = get_fee_or_404(fee_id)
    if role == "admin":
        return fee
    if role == "parent":
        child_ids = {s.id for s in current_parent().students}
        if fee.student_id not in child_ids:
            raise forbidden()
        return fee
    raise forbidden()


def _scoped_fee_query(role):
    query = StudentFee.query
    if role == "admin":
        return query
    if role == "parent":
        student_ids = {s.id for s in current_parent().students}
        return query.filter(StudentFee.student_id.in_(student_ids)) if student_ids else query.filter(false())
    raise forbidden()


def list_fees_query(role, class_id=None, status=None):
    query = _scoped_fee_query(role)
    if class_id is not None:
        query = query.join(Student, StudentFee.student_id == Student.id).filter(Student.class_id == class_id)
    if status is not None:
        query = query.filter(StudentFee.status == FeeStatus(status))
    return query.order_by(StudentFee.due_date.desc())


def send_fee_reminder(fee_id):
    """Admin-triggered, immediate version of the same reminder
    _schedule_fee_reminder() queues automatically 3 days before the due
    date -- lets an admin nudge a parent on demand instead of waiting."""
    fee = get_fee_or_404(fee_id)
    if fee.status == FeeStatus.PAID:
        raise ApiError("This fee has already been paid", "already_paid", 409)

    student = Student.query.get(fee.student_id)
    if student is None or student.parent is None:
        raise ApiError("This student has no linked parent account to notify", "no_parent", 409)

    NotificationService.notify_fee_due_reminder(student.parent.user_id, fee.amount, fee.due_date, cycle_label=fee.cycle)
    return fee


# ---------------------------------------------------------------------------
# Payment order creation (admin, parent) + webhook confirmation
# ---------------------------------------------------------------------------


def create_payment_order(fee_id, role):
    fee = get_fee_scoped(fee_id, role)
    if fee.status == FeeStatus.PAID:
        raise ApiError("This fee has already been paid", "already_paid", 409)

    try:
        order = razorpay_service.create_order(
            fee.amount, receipt=f"studentfee-{fee.id}", notes={"student_fee_id": str(fee.id)}
        )
    except razorpay_service.RazorpayError as exc:
        raise ApiError("Could not create payment order", "payment_gateway_error", 502) from exc

    fee.razorpay_order_id = order["id"]
    db.session.commit()

    return {
        "fee_id": fee.id,
        "order_id": order["id"],
        "amount": order["amount"],  # paise -- what Razorpay's checkout widget expects
        "currency": order.get("currency", "INR"),
        "key_id": current_app.config["RAZORPAY_KEY_ID"],
    }


def mark_fee_paid_from_webhook(razorpay_order_id, razorpay_payment_id):
    """Called only after the webhook route has verified the request's HMAC
    signature -- this function trusts its arguments. Returns None if no
    StudentFee matches the order id (route still responds 2xx so Razorpay
    doesn't retry; there's genuinely nothing to reconcile)."""
    fee = StudentFee.query.filter_by(razorpay_order_id=razorpay_order_id).first()
    if fee is None:
        logger.warning("Razorpay webhook for unknown order_id=%s", razorpay_order_id)
        return None

    if fee.status == FeeStatus.PAID:
        # Razorpay retries webhook delivery until it gets a 2xx -- a repeat
        # delivery for an already-settled fee is a no-op, not a resend of
        # the payment-received email.
        return fee

    fee.status = FeeStatus.PAID
    fee.paid_at = _utcnow()
    fee.razorpay_payment_id = razorpay_payment_id
    fee.transaction_id = razorpay_payment_id
    db.session.commit()

    try:
        student = Student.query.get(fee.student_id)
        if student is not None and student.parent is not None:
            NotificationService.notify_payment_received(
                student.parent.user_id, fee.amount, receipt_no=fee.transaction_id
            )
    except Exception:
        logger.exception("Failed to send payment_received notification for StudentFee %s", fee.id)

    return fee


# ---------------------------------------------------------------------------
# Recurring jobs
# ---------------------------------------------------------------------------


def _next_cycle_year_month():
    today = date.today()
    if today.month == 12:
        return today.year + 1, 1
    return today.year, today.month + 1


def _due_date_for(year, month):
    due_day = min(current_app.config["FEE_DUE_DAY_OF_MONTH"], calendar.monthrange(year, month)[1])
    return date(year, month, due_day)


def _schedule_fee_reminder(fee):
    student = Student.query.get(fee.student_id)
    if student is None or student.parent is None:
        return None
    reminder_at = datetime.combine(fee.due_date - timedelta(days=3), time(hour=9), tzinfo=timezone.utc)
    try:
        return NotificationService.schedule_fee_due_reminder(
            student.parent.user_id, fee.amount, fee.due_date, reminder_at, cycle_label=fee.cycle
        )
    except Exception:
        logger.exception("Failed to schedule fee_due_reminder for StudentFee %s", fee.id)
        return None


def generate_upcoming_student_fees():
    """Creates next month's StudentFee for every active FeePlan that
    doesn't already have one for that cycle, and schedules each one's
    due-date reminder. Plans that haven't started yet as of that cycle
    (start_date in a later month) are skipped."""
    year, month = _next_cycle_year_month()
    cycle = f"{year:04d}-{month:02d}"
    due_date = _due_date_for(year, month)

    created = []
    for plan in FeePlan.query.filter_by(active=True).all():
        if (year, month) < (plan.start_date.year, plan.start_date.month):
            continue
        if StudentFee.query.filter_by(fee_plan_id=plan.id, cycle=cycle).first() is not None:
            continue

        fee = StudentFee(
            fee_plan_id=plan.id,
            student_id=plan.student_id,
            cycle=cycle,
            amount=plan.monthly_amount,
            due_date=due_date,
            status=FeeStatus.PENDING,
        )
        db.session.add(fee)
        db.session.commit()
        _schedule_fee_reminder(fee)
        created.append(fee)

    return created


def mark_overdue_fees():
    today = date.today()
    affected = StudentFee.query.filter(
        StudentFee.due_date < today, StudentFee.status == FeeStatus.PENDING
    ).update({"status": FeeStatus.OVERDUE}, synchronize_session=False)
    db.session.commit()
    return affected


def _run_generate_upcoming_student_fees():
    with _app.app_context():
        try:
            generate_upcoming_student_fees()
        except Exception:
            logger.exception("Scheduled fee-generation job failed")


def _run_mark_overdue_fees():
    with _app.app_context():
        try:
            mark_overdue_fees()
        except Exception:
            logger.exception("Scheduled overdue-fee sweep failed")


def init_fee_scheduler(app):
    """Registers the two recurring fee jobs on the shared scheduler.
    Same reloader-guard and single-worker reasoning as
    notification_service.init_scheduler() -- see that function and the
    single-worker note on `scheduler` in extensions.py."""
    global _app

    if not app.config.get("SCHEDULER_ENABLED", True):
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    _app = app
    if not scheduler.running:
        scheduler.start()

    scheduler.add_job(
        func=_run_generate_upcoming_student_fees,
        trigger=CronTrigger(
            day=app.config["FEE_GENERATION_DAY_OF_MONTH"], hour=2, minute=0, timezone=timezone.utc
        ),
        id="fee-generate-upcoming",
        replace_existing=True,
    )
    scheduler.add_job(
        func=_run_mark_overdue_fees,
        trigger=CronTrigger(hour=3, minute=0, timezone=timezone.utc),
        id="fee-mark-overdue",
        replace_existing=True,
    )