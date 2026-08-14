"""Read-only aggregate/trend queries for dashboards. Nothing here writes
anything -- every function takes the requester's role (and, for
admin/teacher, optional class_id/student_id filters) and returns numbers
already shaped for the frontend to hand straight to recharts.

Time-series responses are always `[{"date": "YYYY-MM", "value": ...}]`,
sorted chronologically, one point per calendar month that has data. Months
with no data simply don't appear (there's no fixed date range to pad
against). Grouping happens in Python rather than a DB date-truncation
function (`strftime` on SQLite, `date_trunc` on Postgres) so this doesn't
silently break if DATABASE_URL is ever pointed at a different engine (see
config.py) -- rows scanned per request are small at this project's scale.

get_marks_trend() normalizes each submission to marks/max_marks*100 before
averaging, so it's comparable across assignments graded out of different
totals. _average_marks_by_class() (admin overview's best/worst-class
ranking) still averages raw `marks` -- fine as a ranking signal within a
single overview snapshot, but not a claim of comparable point totals across
classes if their assignments use different max_marks.
"""
from collections import defaultdict
from datetime import date, datetime, time

from sqlalchemy import false

from app.extensions import db
from app.models.academic import SchoolClass
from app.models.attendance import Attendance, AttendanceStatus
from app.models.homework import Homework, Submission, SubmissionStatus
from app.models.student import Student
from app.models.test import Test, TestSubmission
from app.utils.errors import forbidden, not_found
from app.utils.scoping import current_parent, current_student, current_teacher, teacher_class_ids

_ATTENDED = (AttendanceStatus.PRESENT, AttendanceStatus.LATE)


def _months_ago(n):
    """First day of the month `n` months before today."""
    today = date.today()
    month_index = today.month - 1 - n
    year = today.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _pct(numerator, denominator):
    return round(numerator / denominator * 100, 1) if denominator else 0.0


def _group_by_month_attendance(rows):
    """rows: iterable of (date, AttendanceStatus). -> [{date, value}],
    value = % of records that were present/late that month."""
    buckets = defaultdict(lambda: {"marked": 0, "attended": 0})
    for record_date, status in rows:
        bucket = buckets[record_date.strftime("%Y-%m")]
        bucket["marked"] += 1
        if status in _ATTENDED:
            bucket["attended"] += 1
    return [
        {"date": key, "value": _pct(bucket["attended"], bucket["marked"])}
        for key, bucket in sorted(buckets.items())
    ]


def _group_by_month_marks(rows):
    """rows: iterable of (date, value) where value is whatever the caller
    wants averaged per month (get_marks_trend passes percentages). ->
    [{date, value}], value = the average of that column that month."""
    buckets = defaultdict(list)
    for record_date, value in rows:
        buckets[record_date.strftime("%Y-%m")].append(value)
    return [
        {"date": key, "value": round(sum(values) / len(values), 1)}
        for key, values in sorted(buckets.items())
    ]


# ---------------------------------------------------------------------------
# Admin overview
# ---------------------------------------------------------------------------


def _attendance_stats_by_class(class_ids=None):
    """{class_id: {"present_count", "total_marked", "attendance_pct"}} for
    every class with at least one attendance record (optionally restricted
    to `class_ids`)."""
    query = db.session.query(Attendance.class_id, Attendance.status)
    if class_ids is not None:
        if not class_ids:
            return {}
        query = query.filter(Attendance.class_id.in_(class_ids))

    buckets = defaultdict(lambda: {"marked": 0, "attended": 0})
    for class_id, status in query.all():
        bucket = buckets[class_id]
        bucket["marked"] += 1
        if status in _ATTENDED:
            bucket["attended"] += 1

    return {
        class_id: {
            "present_count": bucket["attended"],
            "total_marked": bucket["marked"],
            "attendance_pct": _pct(bucket["attended"], bucket["marked"]),
        }
        for class_id, bucket in buckets.items()
    }


def _average_marks_by_class():
    """{class_id: {"average_marks", "graded_count"}} for every class with
    at least one graded homework or test submission."""
    marks_by_class = defaultdict(list)

    hw_rows = (
        db.session.query(Homework.class_id, Submission.marks)
        .join(Submission, Submission.homework_id == Homework.id)
        .filter(Submission.status == SubmissionStatus.GRADED, Submission.marks.isnot(None))
        .all()
    )
    test_rows = (
        db.session.query(Test.class_id, TestSubmission.marks)
        .join(TestSubmission, TestSubmission.test_id == Test.id)
        .filter(TestSubmission.status == SubmissionStatus.GRADED, TestSubmission.marks.isnot(None))
        .all()
    )
    for class_id, marks in (*hw_rows, *test_rows):
        marks_by_class[class_id].append(marks)

    return {
        class_id: {"average_marks": round(sum(values) / len(values), 1), "graded_count": len(values)}
        for class_id, values in marks_by_class.items()
    }


def get_admin_overview(limit=3):
    total_students = Student.query.count()

    total_marked = Attendance.query.count()
    attended = Attendance.query.filter(Attendance.status.in_(_ATTENDED)).count()
    overall_attendance_pct = _pct(attended, total_marked)

    marks_by_class = _average_marks_by_class()
    attendance_by_class = _attendance_stats_by_class()

    # Rank by marks once grading data exists; fall back to attendance for a
    # freshly-seeded system that has none yet.
    if marks_by_class:
        ranked_by = "marks"
        ranking_source = {class_id: info["average_marks"] for class_id, info in marks_by_class.items()}
    else:
        ranked_by = "attendance"
        ranking_source = {class_id: info["attendance_pct"] for class_id, info in attendance_by_class.items()}

    ranked_class_ids = sorted(ranking_source, key=lambda class_id: ranking_source[class_id], reverse=True)

    def _entry(class_id):
        school_class = SchoolClass.query.get(class_id)
        attendance_info = attendance_by_class.get(class_id, {})
        entry = {
            "class_id": class_id,
            "grade": school_class.grade if school_class else None,
            "average_attendance_pct": attendance_info.get("attendance_pct", 0.0),
        }
        marks_info = marks_by_class.get(class_id)
        if marks_info:
            entry["average_marks"] = marks_info["average_marks"]
            entry["graded_count"] = marks_info["graded_count"]
        return entry

    return {
        "total_students": total_students,
        "overall_attendance_pct": overall_attendance_pct,
        "ranked_by": ranked_by,
        "best_classes": [_entry(cid) for cid in ranked_class_ids[:limit]],
        "worst_classes": [_entry(cid) for cid in list(reversed(ranked_class_ids))[:limit]],
    }


# ---------------------------------------------------------------------------
# Teacher (+ admin): class-wise average attendance
# ---------------------------------------------------------------------------


def get_class_attendance(role):
    if role == "admin":
        classes = SchoolClass.query.order_by(SchoolClass.grade).all()
    elif role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        classes = (
            SchoolClass.query.filter(SchoolClass.id.in_(class_ids)).order_by(SchoolClass.grade).all()
            if class_ids
            else []
        )
    else:
        raise forbidden()

    stats = _attendance_stats_by_class(class_ids=[c.id for c in classes])
    return [
        {
            "class_id": c.id,
            "grade": c.grade,
            "attendance_pct": stats.get(c.id, {}).get("attendance_pct", 0.0),
            "present_count": stats.get(c.id, {}).get("present_count", 0),
            "total_marked": stats.get(c.id, {}).get("total_marked", 0),
        }
        for c in classes
    ]


# ---------------------------------------------------------------------------
# Attendance trend (admin, teacher, parent, student)
# ---------------------------------------------------------------------------


def _base_attendance_query(role):
    query = Attendance.query
    if role == "admin":
        return query
    if role == "teacher":
        class_ids = teacher_class_ids(current_teacher())
        return query.filter(Attendance.class_id.in_(class_ids)) if class_ids else query.filter(false())
    if role == "parent":
        student_ids = {s.id for s in current_parent().students}
        return query.filter(Attendance.student_id.in_(student_ids)) if student_ids else query.filter(false())
    if role == "student":
        return query.filter(Attendance.student_id == current_student().id)
    raise forbidden()


def get_attendance_trend(role, student_id=None, class_id=None, months=None):
    query = _base_attendance_query(role)

    if role in ("admin", "teacher") and class_id is not None:
        if role == "teacher" and class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        query = query.filter(Attendance.class_id == class_id)

    if role in ("admin", "teacher", "parent") and student_id is not None:
        student = Student.query.get(student_id)
        if student is None:
            raise not_found("Student")
        if role == "teacher" and student.class_id not in teacher_class_ids(current_teacher()):
            raise forbidden()
        if role == "parent" and student.parent_id != current_parent().id:
            raise forbidden()
        query = query.filter(Attendance.student_id == student_id)
    # role == "student": always self-scoped by _base_attendance_query above;
    # student_id/class_id are simply ignored rather than erroring.

    if months is not None:
        query = query.filter(Attendance.date >= _months_ago(months))

    rows = query.with_entities(Attendance.date, Attendance.status).all()
    return _group_by_month_attendance(rows)


# ---------------------------------------------------------------------------
# Marks trend (admin, parent, student -- not teacher)
# ---------------------------------------------------------------------------


def _own_student_ids(role):
    """None means "no restriction" (admin sees everyone); otherwise the set
    of student_ids this role may see marks for."""
    if role == "admin":
        return None
    if role == "parent":
        return {s.id for s in current_parent().students}
    if role == "student":
        return {current_student().id}
    raise forbidden()


def get_marks_trend(role, student_id=None, months=None):
    allowed_ids = _own_student_ids(role)

    if role != "student" and student_id is not None:
        if Student.query.get(student_id) is None:
            raise not_found("Student")
        if allowed_ids is not None and student_id not in allowed_ids:
            raise forbidden()
        scoped_ids = {student_id}
    else:
        scoped_ids = allowed_ids  # None for admin; the role's own set otherwise

    if scoped_ids is not None and not scoped_ids:
        return []

    # Joined to Homework/Test for max_marks so each submission can be
    # converted to a percentage before averaging -- a straight average of
    # raw `marks` would be meaningless once assignments have different
    # max_marks. Rows with no max_marks (shouldn't exist post-backfill, but
    # the column stays nullable at the DB level) are excluded rather than
    # guessed at.
    hw_query = (
        db.session.query(Submission.submitted_at, Submission.marks, Homework.max_marks)
        .join(Homework, Submission.homework_id == Homework.id)
        .filter(
            Submission.status == SubmissionStatus.GRADED,
            Submission.marks.isnot(None),
            Homework.max_marks.isnot(None),
        )
    )
    test_query = (
        db.session.query(TestSubmission.submitted_at, TestSubmission.marks, Test.max_marks)
        .join(Test, TestSubmission.test_id == Test.id)
        .filter(
            TestSubmission.status == SubmissionStatus.GRADED,
            TestSubmission.marks.isnot(None),
            Test.max_marks.isnot(None),
        )
    )
    if scoped_ids is not None:
        hw_query = hw_query.filter(Submission.student_id.in_(scoped_ids))
        test_query = test_query.filter(TestSubmission.student_id.in_(scoped_ids))

    if months is not None:
        cutoff = datetime.combine(_months_ago(months), time.min)
        hw_query = hw_query.filter(Submission.submitted_at >= cutoff)
        test_query = test_query.filter(TestSubmission.submitted_at >= cutoff)

    rows = [
        (submitted_at.date(), marks / max_marks * 100)
        for submitted_at, marks, max_marks in (*hw_query.all(), *test_query.all())
        if max_marks
    ]
    return _group_by_month_marks(rows)