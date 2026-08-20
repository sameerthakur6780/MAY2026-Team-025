"""Analytics endpoints: role-scoped aggregates and [{date, value}] trends
for the dashboard. Attendance/homework/test rows are created directly
against the DB (bypassing the relevant create/mark endpoints) since these
are read-only endpoints and the point here is exercising the aggregation
and scoping logic, not re-testing attendance/grading creation paths."""
from datetime import date, datetime

from conftest import (
    create_assignment,
    create_class,
    create_parent,
    create_student,
    create_subject,
    create_teacher,
    login_as,
)

from app.extensions import db
from app.models.attendance import Attendance, AttendanceMethod, AttendanceStatus
from app.models.homework import Homework, Submission, SubmissionStatus
from app.models.test import Test, TestSubmission


def _mark(student, school_class, marker_user_id, day, status):
    row = Attendance(
        student_id=student.id,
        class_id=school_class.id,
        date=day,
        status=status,
        marked_by=marker_user_id,
        method=AttendanceMethod.MANUAL,
    )
    db.session.add(row)
    db.session.commit()
    return row


def _homework(school_class, subject, teacher_user_id, due_date=None, max_marks=100):
    hw = Homework(
        class_id=school_class.id,
        subject_id=subject.id,
        title="HW",
        due_date=due_date or date(2026, 1, 1),
        created_by=teacher_user_id,
        max_marks=max_marks,
    )
    db.session.add(hw)
    db.session.commit()
    return hw


def _graded_submission(homework, student, marks, submitted_at):
    sub = Submission(
        homework_id=homework.id,
        student_id=student.id,
        file_url="https://fake-storage.test/x.pdf",
        submitted_at=submitted_at,
        marks=marks,
        status=SubmissionStatus.GRADED,
    )
    db.session.add(sub)
    db.session.commit()
    return sub


def _test_row(school_class, subject, teacher_user_id, due_date=None, max_marks=100):
    t = Test(
        class_id=school_class.id,
        subject_id=subject.id,
        title="Test",
        due_date=due_date or date(2026, 1, 1),
        created_by=teacher_user_id,
        max_marks=max_marks,
    )
    db.session.add(t)
    db.session.commit()
    return t


def _graded_test_submission(test, student, marks, submitted_at):
    sub = TestSubmission(
        test_id=test.id,
        student_id=student.id,
        file_url="https://fake-storage.test/x.pdf",
        submitted_at=submitted_at,
        marks=marks,
        status=SubmissionStatus.GRADED,
    )
    db.session.add(sub)
    db.session.commit()
    return sub


# ---------------------------------------------------------------------------
# Admin overview
# ---------------------------------------------------------------------------


def test_admin_overview_ranks_by_marks_once_graded_data_exists(app, admin, make_client):
    with app.app_context():
        class_a = create_class(grade=1)
        class_b = create_class(grade=2)
        subject = create_subject("Maths")
        teacher = create_teacher()
        create_assignment(class_a.id, subject.id, teacher.id)
        create_assignment(class_b.id, subject.id, teacher.id)

        student_a = create_student(class_id=class_a.id)
        student_b = create_student(class_id=class_b.id)

        hw_a = _homework(class_a, subject, teacher.user_id)
        hw_b = _homework(class_b, subject, teacher.user_id)
        _graded_submission(hw_a, student_a, 90, datetime(2026, 1, 5))
        _graded_submission(hw_b, student_b, 40, datetime(2026, 1, 5))

        _mark(student_a, class_a, teacher.user_id, date(2026, 1, 1), AttendanceStatus.PRESENT)
        _mark(student_b, class_b, teacher.user_id, date(2026, 1, 1), AttendanceStatus.ABSENT)

        class_a_id, class_b_id = class_a.id, class_b.id

    resp = admin.get("/api/analytics/overview")
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["total_students"] == 2
    assert body["ranked_by"] == "marks"
    assert body["best_classes"][0]["class_id"] == class_a_id
    assert body["worst_classes"][0]["class_id"] == class_b_id


def test_admin_overview_falls_back_to_attendance_ranking_when_no_marks(app, admin):
    with app.app_context():
        class_a = create_class(grade=1)
        teacher = create_teacher()
        student_a = create_student(class_id=class_a.id)
        _mark(student_a, class_a, teacher.user_id, date(2026, 1, 1), AttendanceStatus.PRESENT)

        class_a_id = class_a.id

    resp = admin.get("/api/analytics/overview")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ranked_by"] == "attendance"
    assert body["best_classes"][0]["class_id"] == class_a_id


def test_admin_overview_requires_admin_role(teacher):
    authed, _ = teacher
    resp = authed.get("/api/analytics/overview")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Class attendance (admin, teacher)
# ---------------------------------------------------------------------------


def test_class_attendance_admin_sees_all_teacher_sees_assigned_only(app, admin, make_client):
    with app.app_context():
        class_a = create_class(grade=1)
        class_b = create_class(grade=2)
        subject = create_subject("Science")
        teacher = create_teacher()
        create_assignment(class_a.id, subject.id, teacher.id)  # only assigned to class_a

        student_a = create_student(class_id=class_a.id)
        student_b = create_student(class_id=class_b.id)
        _mark(student_a, class_a, teacher.user_id, date(2026, 1, 1), AttendanceStatus.PRESENT)
        _mark(student_b, class_b, teacher.user_id, date(2026, 1, 1), AttendanceStatus.ABSENT)

        teacher_email = teacher.user.email
        class_a_id, class_b_id = class_a.id, class_b.id

    admin_resp = admin.get("/api/analytics/class-attendance")
    assert admin_resp.status_code == 200
    admin_ids = {row["class_id"] for row in admin_resp.get_json()}
    assert {class_a_id, class_b_id} <= admin_ids

    teacher_client = login_as(make_client(), teacher_email)
    teacher_resp = teacher_client.get("/api/analytics/class-attendance")
    assert teacher_resp.status_code == 200
    teacher_rows = teacher_resp.get_json()
    assert {row["class_id"] for row in teacher_rows} == {class_a_id}
    assert teacher_rows[0]["attendance_pct"] == 100.0


def test_class_attendance_rejects_parent(parent):
    authed, _ = parent
    resp = authed.get("/api/analytics/class-attendance")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Attendance trend
# ---------------------------------------------------------------------------


def test_attendance_trend_buckets_by_month_and_self_scopes_for_student(app, make_client):
    with app.app_context():
        school_class = create_class(grade=1)
        teacher = create_teacher()
        student_row = create_student(class_id=school_class.id)

        _mark(student_row, school_class, teacher.user_id, date(2026, 1, 5), AttendanceStatus.PRESENT)
        _mark(student_row, school_class, teacher.user_id, date(2026, 1, 6), AttendanceStatus.ABSENT)
        _mark(student_row, school_class, teacher.user_id, date(2026, 2, 5), AttendanceStatus.PRESENT)

        student_email = student_row.user.email

    student_client = login_as(make_client(), student_email)
    resp = student_client.get("/api/analytics/attendance-trend")
    assert resp.status_code == 200
    points = resp.get_json()
    assert points == [
        {"date": "2026-01", "value": 50.0},
        {"date": "2026-02", "value": 100.0},
    ]


def test_attendance_trend_parent_scoped_to_own_child_forbidden_otherwise(app, make_client):
    with app.app_context():
        school_class = create_class(grade=1)
        teacher = create_teacher()
        parent_row = create_parent()
        other_parent_row = create_parent()
        own_child = create_student(class_id=school_class.id, parent_id=parent_row.id)
        other_child = create_student(class_id=school_class.id, parent_id=other_parent_row.id)

        _mark(own_child, school_class, teacher.user_id, date(2026, 1, 1), AttendanceStatus.PRESENT)
        _mark(other_child, school_class, teacher.user_id, date(2026, 1, 1), AttendanceStatus.PRESENT)

        parent_email = parent_row.user.email
        own_child_id, other_child_id = own_child.id, other_child.id

    parent_client = login_as(make_client(), parent_email)

    own_resp = parent_client.get(f"/api/analytics/attendance-trend?student_id={own_child_id}")
    assert own_resp.status_code == 200
    assert own_resp.get_json() == [{"date": "2026-01", "value": 100.0}]

    other_resp = parent_client.get(f"/api/analytics/attendance-trend?student_id={other_child_id}")
    assert other_resp.status_code == 403


def test_attendance_trend_no_data_returns_empty_list(student):
    authed, _ = student
    resp = authed.get("/api/analytics/attendance-trend")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_attendance_trend_invalid_query_param(student):
    authed, _ = student
    resp = authed.get("/api/analytics/attendance-trend?months=not-a-number")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Marks trend
# ---------------------------------------------------------------------------


def test_marks_trend_rejects_teacher(teacher):
    authed, _ = teacher
    resp = authed.get("/api/analytics/marks-trend")
    assert resp.status_code == 403


def test_marks_trend_buckets_by_month_across_homework_and_tests(app, make_client):
    """Homework and the test both use different max_marks (100 and 50) --
    this only passes if get_marks_trend actually normalizes to a percentage
    per submission rather than averaging raw marks."""
    with app.app_context():
        school_class = create_class(grade=1)
        subject = create_subject("English")
        teacher = create_teacher()
        student_row = create_student(class_id=school_class.id)

        hw_jan = _homework(school_class, subject, teacher.user_id, max_marks=100)
        hw_feb = _homework(school_class, subject, teacher.user_id, max_marks=40)
        test_row = _test_row(school_class, subject, teacher.user_id, max_marks=50)

        _graded_submission(hw_jan, student_row, 80, datetime(2026, 1, 10))  # 80%
        _graded_test_submission(test_row, student_row, 30, datetime(2026, 1, 20))  # 60%
        _graded_submission(hw_feb, student_row, 40, datetime(2026, 2, 10))  # 100%

        student_email = student_row.user.email

    student_client = login_as(make_client(), student_email)
    resp = student_client.get("/api/analytics/marks-trend")
    assert resp.status_code == 200
    assert resp.get_json() == [
        {"date": "2026-01", "value": 70.0},  # avg(80%, 60%)
        {"date": "2026-02", "value": 100.0},
    ]


def test_marks_trend_parent_scoped_to_own_child(app, make_client):
    with app.app_context():
        school_class = create_class(grade=1)
        subject = create_subject("History")
        teacher = create_teacher()
        parent_row = create_parent()
        other_parent_row = create_parent()
        own_child = create_student(class_id=school_class.id, parent_id=parent_row.id)
        other_child = create_student(class_id=school_class.id, parent_id=other_parent_row.id)

        hw = _homework(school_class, subject, teacher.user_id)
        _graded_submission(hw, own_child, 50, datetime(2026, 1, 1))
        _graded_submission(hw, other_child, 99, datetime(2026, 1, 1))

        parent_email = parent_row.user.email
        other_child_id = other_child.id

    parent_client = login_as(make_client(), parent_email)

    own_resp = parent_client.get("/api/analytics/marks-trend")
    assert own_resp.status_code == 200
    assert own_resp.get_json() == [{"date": "2026-01", "value": 50.0}]

    other_resp = parent_client.get(f"/api/analytics/marks-trend?student_id={other_child_id}")
    assert other_resp.status_code == 403