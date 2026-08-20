"""FeePlan CRUD, StudentFee listing/payment, and the two recurring jobs
(generate_upcoming_student_fees, mark_overdue_fees). Razorpay order creation
is monkeypatched (no real network calls) but webhook signature verification
is exercised for real: tests compute an actual HMAC-SHA256 over the exact
raw body and confirm the route only accepts a genuinely valid signature --
not just that a `verify` function was called correctly in isolation."""
import calendar
import hashlib
import hmac
import json
from datetime import date, timedelta

from conftest import create_class, create_parent, create_student, login_as

from app.extensions import db, mail, scheduler
from app.models.fee import FeePlan, FeeStatus, StudentFee
from app.models.notification import Notification, NotificationStatus, NotificationType
from app.services.fee_service import generate_upcoming_student_fees, mark_overdue_fees

WEBHOOK_SECRET = "test-webhook-secret"


def _cleanup_fee_reminder_jobs():
    """generate_upcoming_student_fees() schedules a FEE_DUE_REMINDER job on
    the shared, process-wide `scheduler` singleton (see extensions.py) --
    the same one every test app in this suite uses. Notification ids reset
    to 1 in every test's fresh in-memory DB, so an unregistered job here
    would collide with (and shadow) a same-id job a later, unrelated test
    registers -- matching the cleanup test_notifications.py already does
    for its own scheduled-job assertions."""
    for notification in Notification.query.filter_by(type=NotificationType.FEE_DUE_REMINDER).all():
        job_id = f"notification-{notification.id}"
        if scheduler.get_job(job_id) is not None:
            scheduler.remove_job(job_id)


def _make_fee_plan(student, monthly_amount=1000, start_date=None, active=True):
    plan = FeePlan(
        student_id=student.id,
        monthly_amount=monthly_amount,
        start_date=start_date or date(2020, 1, 1),
        active=active,
    )
    db.session.add(plan)
    db.session.commit()
    return plan


def _make_student_fee(plan, student, cycle, due_date, amount=None, status=FeeStatus.PENDING):
    fee = StudentFee(
        fee_plan_id=plan.id,
        student_id=student.id,
        cycle=cycle,
        amount=amount if amount is not None else plan.monthly_amount,
        due_date=due_date,
        status=status,
    )
    db.session.add(fee)
    db.session.commit()
    return fee


def _next_cycle_year_month():
    today = date.today()
    if today.month == 12:
        return today.year + 1, 1
    return today.year, today.month + 1


def _signed_webhook_post(client, payload, secret=WEBHOOK_SECRET):
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return client.post(
        "/api/payments/webhook", data=body, headers={"X-Razorpay-Signature": signature},
        content_type="application/json",
    )


def _payment_captured_payload(order_id, payment_id):
    return {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": payment_id, "order_id": order_id, "status": "captured"}}},
    }


# ---------------------------------------------------------------------------
# FeePlan CRUD (admin)
# ---------------------------------------------------------------------------


def test_admin_can_crud_fee_plan(app, admin):
    with app.app_context():
        school_class = create_class(grade=1)
        student = create_student(class_id=school_class.id)
        student_id = student.id

    create_resp = admin.post(
        "/api/fee-plans", json={"student_id": student_id, "monthly_amount": 1500, "start_date": "2026-01-01"}
    )
    assert create_resp.status_code == 201, create_resp.get_json()
    plan = create_resp.get_json()
    assert plan["monthly_amount"] == 1500
    assert plan["active"] is True
    plan_id = plan["id"]

    get_resp = admin.get(f"/api/fee-plans/{plan_id}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["student_id"] == student_id

    update_resp = admin.patch(f"/api/fee-plans/{plan_id}", json={"monthly_amount": 2000})
    assert update_resp.status_code == 200
    assert update_resp.get_json()["monthly_amount"] == 2000

    list_resp = admin.get(f"/api/fee-plans?student_id={student_id}")
    assert list_resp.status_code == 200
    assert len(list_resp.get_json()["items"]) == 1

    # Creating a plan immediately generates its starting cycle's invoice
    # (see create_fee_plan -- a student shouldn't wait until
    # FEE_GENERATION_DAY_OF_MONTH for their first bill), so it can no longer
    # be hard-deleted -- see test_fee_plan_delete_blocked_once_fees_exist for
    # that path in isolation. Deactivating is the real "remove" affordance
    # once a plan has billing history.
    delete_resp = admin.delete(f"/api/fee-plans/{plan_id}")
    assert delete_resp.status_code == 409

    deactivate_resp = admin.patch(f"/api/fee-plans/{plan_id}", json={"active": False})
    assert deactivate_resp.status_code == 200
    assert deactivate_resp.get_json()["active"] is False


def test_fee_plan_delete_blocked_once_fees_exist(app, admin):
    with app.app_context():
        school_class = create_class(grade=1)
        student = create_student(class_id=school_class.id)
        plan = _make_fee_plan(student)
        _make_student_fee(plan, student, "2026-01", date(2026, 1, 10))
        plan_id = plan.id

    resp = admin.delete(f"/api/fee-plans/{plan_id}")
    assert resp.status_code == 409


def test_fee_plan_crud_requires_admin(parent):
    authed, _ = parent
    resp = authed.post("/api/fee-plans", json={"student_id": 1, "monthly_amount": 1000, "start_date": "2026-01-01"})
    assert resp.status_code == 403


def test_create_fee_plan_generates_starting_cycle_invoice(app, admin):
    """A plan shouldn't sit invisible until FEE_GENERATION_DAY_OF_MONTH --
    creating one bills the student for their starting cycle immediately."""
    with app.app_context():
        school_class = create_class(grade=1)
        student = create_student(class_id=school_class.id)
        student_id = student.id

    create_resp = admin.post(
        "/api/fee-plans", json={"student_id": student_id, "monthly_amount": 1500, "start_date": "2026-03-05"}
    )
    assert create_resp.status_code == 201, create_resp.get_json()

    list_resp = admin.get(f"/api/fees?student_id={student_id}")
    items = list_resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["cycle"] == "2026-03"
    assert items[0]["amount"] == 1500
    assert items[0]["status"] == "pending"
    expected_due_day = min(10, calendar.monthrange(2026, 3)[1])  # FEE_DUE_DAY_OF_MONTH=10 in TestConfig
    assert items[0]["due_date"] == date(2026, 3, expected_due_day).isoformat()

    with app.app_context():
        _cleanup_fee_reminder_jobs()


def test_create_fee_plan_does_not_duplicate_invoice_for_same_cycle(app, admin):
    """generate_initial_fee() is called from inside create_fee_plan(), which
    already committed the plan -- confirms it won't double-create if a
    StudentFee for that cycle somehow already exists."""
    with app.app_context():
        school_class = create_class(grade=1)
        student = create_student(class_id=school_class.id)
        student_id = student.id

    create_resp = admin.post(
        "/api/fee-plans", json={"student_id": student_id, "monthly_amount": 1200, "start_date": "2026-02-01"}
    )
    plan_id = create_resp.get_json()["id"]

    with app.app_context():
        from app.services.fee_service import generate_initial_fee

        plan = FeePlan.query.get(plan_id)
        result = generate_initial_fee(plan)  # calling again directly should no-op
        assert result is None
        assert StudentFee.query.filter_by(fee_plan_id=plan_id).count() == 1
        _cleanup_fee_reminder_jobs()


def test_remind_route_sends_reminder_and_rejects_already_paid(app, admin):
    with app.app_context():
        school_class = create_class(grade=1)
        parent_row = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)
        plan = _make_fee_plan(student_row)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10))
        fee_id = fee.id
        paid_fee = _make_student_fee(plan, student_row, "2025-12", date(2025, 12, 10))
        paid_fee.status = FeeStatus.PAID
        db.session.commit()
        paid_fee_id = paid_fee.id

    with mail.record_messages() as outbox:
        resp = admin.post(f"/api/fees/{fee_id}/remind")
    assert resp.status_code == 200, resp.get_json()
    assert len(outbox) == 1

    with app.app_context():
        notification = Notification.query.filter_by(type=NotificationType.FEE_DUE_REMINDER).one()
        assert notification.status == NotificationStatus.SENT

    already_paid_resp = admin.post(f"/api/fees/{paid_fee_id}/remind")
    assert already_paid_resp.status_code == 409
    assert already_paid_resp.get_json()["error"] == "already_paid"


def test_remind_route_requires_admin(parent):
    authed, _ = parent
    resp = authed.post("/api/fees/1/remind")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/fees
# ---------------------------------------------------------------------------


def test_admin_lists_all_fees_scoped_by_class_and_status(app, admin, make_client):
    with app.app_context():
        class_a = create_class(grade=1)
        class_b = create_class(grade=2)
        student_a = create_student(class_id=class_a.id)
        student_b = create_student(class_id=class_b.id)
        plan_a = _make_fee_plan(student_a)
        plan_b = _make_fee_plan(student_b)
        _make_student_fee(plan_a, student_a, "2026-01", date(2026, 1, 10), status=FeeStatus.PENDING)
        fee_b = _make_student_fee(plan_b, student_b, "2026-01", date(2026, 1, 10), status=FeeStatus.PAID)
        class_a_id = class_a.id
        fee_b_id = fee_b.id

    all_resp = admin.get("/api/fees")
    assert all_resp.status_code == 200
    assert len(all_resp.get_json()["items"]) == 2

    class_resp = admin.get(f"/api/fees?class_id={class_a_id}")
    assert class_resp.status_code == 200
    class_items = class_resp.get_json()["items"]
    assert len(class_items) == 1
    assert class_items[0]["student_id"] != fee_b_id  # sanity: not the other class's fee

    status_resp = admin.get("/api/fees?status=paid")
    assert status_resp.status_code == 200
    status_items = status_resp.get_json()["items"]
    assert len(status_items) == 1
    assert status_items[0]["status"] == "paid"


def test_parent_sees_only_own_childs_fees(app, make_client):
    with app.app_context():
        school_class = create_class(grade=1)
        parent_row = create_parent()
        other_parent_row = create_parent()
        own_child = create_student(class_id=school_class.id, parent_id=parent_row.id)
        other_child = create_student(class_id=school_class.id, parent_id=other_parent_row.id)

        own_plan = _make_fee_plan(own_child)
        other_plan = _make_fee_plan(other_child)
        _make_student_fee(own_plan, own_child, "2026-01", date(2026, 1, 10))
        _make_student_fee(other_plan, other_child, "2026-01", date(2026, 1, 10))

        parent_email = parent_row.user.email
        own_child_id = own_child.id

    parent_client = login_as(make_client(), parent_email)
    resp = parent_client.get("/api/fees")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == own_child_id


def test_fees_list_rejects_teacher_and_student(teacher, student):
    teacher_authed, _ = teacher
    student_authed, _ = student
    assert teacher_authed.get("/api/fees").status_code == 403
    assert student_authed.get("/api/fees").status_code == 403


# ---------------------------------------------------------------------------
# POST /api/fees/<id>/create-order
# ---------------------------------------------------------------------------


def _fake_create_order(monkeypatch, order_id="order_test123"):
    def _fake(amount_rupees, receipt, notes=None):
        return {"id": order_id, "amount": int(amount_rupees * 100), "currency": "INR"}

    monkeypatch.setattr("app.services.fee_service.razorpay_service.create_order", _fake)


def test_create_order_admin_and_parent(app, admin, make_client, monkeypatch):
    _fake_create_order(monkeypatch, order_id="order_abc")
    with app.app_context():
        school_class = create_class(grade=1)
        parent_row = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)
        plan = _make_fee_plan(student_row, monthly_amount=2500)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10), amount=2500)
        fee_id = fee.id
        parent_email = parent_row.user.email

    admin_resp = admin.post(f"/api/fees/{fee_id}/create-order")
    assert admin_resp.status_code == 201, admin_resp.get_json()
    body = admin_resp.get_json()
    assert body["order_id"] == "order_abc"
    assert body["amount"] == 250000  # paise
    assert body["fee_id"] == fee_id

    with app.app_context():
        assert StudentFee.query.get(fee_id).razorpay_order_id == "order_abc"

    parent_client = login_as(make_client(), parent_email)
    parent_resp = parent_client.post(f"/api/fees/{fee_id}/create-order")
    assert parent_resp.status_code == 201


def test_create_order_rejects_other_parent(app, make_client, monkeypatch):
    _fake_create_order(monkeypatch)
    with app.app_context():
        school_class = create_class(grade=1)
        owner_parent = create_parent()
        other_parent = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=owner_parent.id)
        plan = _make_fee_plan(student_row)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10))
        fee_id = fee.id
        other_email = other_parent.user.email

    other_client = login_as(make_client(), other_email)
    resp = other_client.post(f"/api/fees/{fee_id}/create-order")
    assert resp.status_code == 403


def test_create_order_rejects_already_paid_fee(app, admin, monkeypatch):
    _fake_create_order(monkeypatch)
    with app.app_context():
        school_class = create_class(grade=1)
        student_row = create_student(class_id=school_class.id)
        plan = _make_fee_plan(student_row)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10), status=FeeStatus.PAID)
        fee_id = fee.id

    resp = admin.post(f"/api/fees/{fee_id}/create-order")
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/payments/webhook
# ---------------------------------------------------------------------------


def test_webhook_marks_fee_paid_and_sends_notification_with_valid_signature(app, client):
    with app.app_context():
        school_class = create_class(grade=1)
        parent_row = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)
        plan = _make_fee_plan(student_row)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10))
        fee.razorpay_order_id = "order_real123"
        db.session.commit()
        fee_id = fee.id

    with mail.record_messages() as outbox:
        resp = _signed_webhook_post(client, _payment_captured_payload("order_real123", "pay_xyz"))
    assert resp.status_code == 200, resp.get_json()
    assert resp.get_json()["status"] == "ok"
    assert len(outbox) == 1

    with app.app_context():
        stored = StudentFee.query.get(fee_id)
        assert stored.status == FeeStatus.PAID
        assert stored.razorpay_payment_id == "pay_xyz"
        assert stored.transaction_id == "pay_xyz"
        assert stored.paid_at is not None

        notification = Notification.query.filter_by(type=NotificationType.PAYMENT_RECEIVED).one()
        assert notification.status == NotificationStatus.SENT


def test_webhook_rejects_invalid_signature_and_does_not_mark_paid(app, client):
    with app.app_context():
        school_class = create_class(grade=1)
        student_row = create_student(class_id=school_class.id)
        plan = _make_fee_plan(student_row)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10))
        fee.razorpay_order_id = "order_tampered"
        db.session.commit()
        fee_id = fee.id

    body = json.dumps(_payment_captured_payload("order_tampered", "pay_xyz")).encode("utf-8")
    resp = client.post(
        "/api/payments/webhook",
        data=body,
        headers={"X-Razorpay-Signature": "0" * 64},
        content_type="application/json",
    )
    assert resp.status_code == 400

    with app.app_context():
        assert StudentFee.query.get(fee_id).status == FeeStatus.PENDING


def test_webhook_ignores_unhandled_event_and_unknown_order(app, client):
    ignored_resp = _signed_webhook_post(client, {"event": "order.created", "payload": {}})
    assert ignored_resp.status_code == 200
    assert ignored_resp.get_json()["status"] == "ignored"

    unknown_resp = _signed_webhook_post(client, _payment_captured_payload("order_does_not_exist", "pay_1"))
    assert unknown_resp.status_code == 200
    assert unknown_resp.get_json()["status"] == "no_matching_fee"


def test_webhook_duplicate_delivery_is_idempotent(app, client):
    with app.app_context():
        school_class = create_class(grade=1)
        parent_row = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)
        plan = _make_fee_plan(student_row)
        fee = _make_student_fee(plan, student_row, "2026-01", date(2026, 1, 10))
        fee.razorpay_order_id = "order_dup"
        db.session.commit()
        fee_id = fee.id

    payload = _payment_captured_payload("order_dup", "pay_dup")
    with mail.record_messages() as outbox:
        first = _signed_webhook_post(client, payload)
        second = _signed_webhook_post(client, payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert len(outbox) == 1  # not re-sent on the retried delivery

    with app.app_context():
        assert StudentFee.query.get(fee_id).status == FeeStatus.PAID


# ---------------------------------------------------------------------------
# generate_upcoming_student_fees / mark_overdue_fees
# ---------------------------------------------------------------------------


def test_generate_upcoming_student_fees_creates_row_and_schedules_reminder(app):
    with app.app_context():
        school_class = create_class(grade=1)
        parent_row = create_parent()
        student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)
        _make_fee_plan(student_row, monthly_amount=1800, start_date=date(2020, 1, 1))

        created = generate_upcoming_student_fees()
        assert len(created) == 1

        year, month = _next_cycle_year_month()
        expected_cycle = f"{year:04d}-{month:02d}"
        expected_due_day = min(10, calendar.monthrange(year, month)[1])  # FEE_DUE_DAY_OF_MONTH=10 in TestConfig
        expected_due_date = date(year, month, expected_due_day)

        fee = created[0]
        assert fee.cycle == expected_cycle
        assert fee.amount == 1800
        assert fee.due_date == expected_due_date
        assert fee.status == FeeStatus.PENDING

        notification = Notification.query.filter_by(type=NotificationType.FEE_DUE_REMINDER).one()
        assert notification.status == NotificationStatus.PENDING
        assert notification.scheduled_at is not None
        assert notification.scheduled_at.date() == expected_due_date - timedelta(days=3)

        _cleanup_fee_reminder_jobs()


def test_generate_upcoming_student_fees_is_idempotent(app):
    with app.app_context():
        school_class = create_class(grade=1)
        student_row = create_student(class_id=school_class.id)
        _make_fee_plan(student_row, start_date=date(2020, 1, 1))

        first = generate_upcoming_student_fees()
        second = generate_upcoming_student_fees()
        assert len(first) == 1
        assert len(second) == 0  # already generated for that cycle -- no duplicate
        assert StudentFee.query.count() == 1

        _cleanup_fee_reminder_jobs()


def test_generate_upcoming_student_fees_skips_plan_not_yet_started(app):
    with app.app_context():
        school_class = create_class(grade=1)
        student_row = create_student(class_id=school_class.id)
        far_future = date(2099, 1, 1)
        _make_fee_plan(student_row, start_date=far_future)

        created = generate_upcoming_student_fees()
        assert created == []
        assert StudentFee.query.count() == 0


def test_generate_upcoming_student_fees_skips_inactive_plan(app):
    with app.app_context():
        school_class = create_class(grade=1)
        student_row = create_student(class_id=school_class.id)
        _make_fee_plan(student_row, start_date=date(2020, 1, 1), active=False)

        created = generate_upcoming_student_fees()
        assert created == []


def test_mark_overdue_fees_flips_pending_past_due_date_only(app):
    with app.app_context():
        school_class = create_class(grade=1)
        student_row = create_student(class_id=school_class.id)
        plan = _make_fee_plan(student_row)

        overdue_fee = _make_student_fee(plan, student_row, "2025-01", date(2020, 1, 1), status=FeeStatus.PENDING)
        future_fee = _make_student_fee(
            plan, student_row, "2099-01", date(2099, 1, 1), status=FeeStatus.PENDING
        )
        already_paid = _make_student_fee(
            plan, student_row, "2020-06", date(2020, 6, 1), status=FeeStatus.PAID
        )

        affected = mark_overdue_fees()
        assert affected == 1

        assert StudentFee.query.get(overdue_fee.id).status == FeeStatus.OVERDUE
        assert StudentFee.query.get(future_fee.id).status == FeeStatus.PENDING
        assert StudentFee.query.get(already_paid.id).status == FeeStatus.PAID