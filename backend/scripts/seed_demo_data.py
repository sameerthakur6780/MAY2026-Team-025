"""Resets the demo database to a known-good state.

Creates: one admin, two teachers, three classes (grades 6-8) with subjects
assigned, nine students with linked parents -- including the three real
facial-recognition demo students (grade 6, enrolled together so a facial
attendance run against tests/fixtures/group.png matches all three) with
their real profile photos uploaded to Supabase -- a couple of downloadable
resources, one graded homework and one graded test per class, a fee plan
plus a few cycles of invoice history per student, and two weeks of
attendance history.

Safe to re-run any time: it wipes every row in every table it manages (in
FK-safe order) before recreating everything, so running it after a Render
restart -- or just to reset a messy demo -- always lands on the same state.
Deterministic (fixed random seed) so the generated attendance/marks data is
identical every run.

Usage (from the backend/ directory, with the venv active and migrations
already applied -- see Procfile):

    python scripts/seed_demo_data.py

All seeded accounts share one password: see DEMO_PASSWORD below.

Deliberately bypasses NotificationService for the bulk data (homework,
tests, fees) -- going through the real create_homework/create_test/
generate_upcoming_student_fees service calls would each attempt a real SMTP
connection per student, which is slow (or hangs, if MAIL_* isn't configured
on the current Render environment) and provides no value for what is just
static demo data. The three facial-recognition profile photos and the two
resources DO go through the real service layer and hit real Supabase
storage, because that round-trip is the one thing this script needs to
actually prove works.
"""
import itertools
import random
import sys
from datetime import date, datetime, time, timedelta, timezone
from io import BytesIO
from pathlib import Path

from werkzeug.datastructures import FileStorage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import bcrypt, db  # noqa: E402
from app.models.academic import ClassSubjectTeacher, SchoolClass, Subject  # noqa: E402
from app.models.attendance import Attendance, AttendanceMethod, AttendanceStatus  # noqa: E402
from app.models.fee import FeePlan, FeeStatus, StudentFee  # noqa: E402
from app.models.homework import Homework, Submission, SubmissionStatus  # noqa: E402
from app.models.notification import Notification  # noqa: E402
from app.models.parent import Parent  # noqa: E402
from app.models.resource import Resource, ResourceType  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.teacher import Teacher  # noqa: E402
from app.models.test import Test, TestSubmission  # noqa: E402
from app.models.user import RoleEnum, User  # noqa: E402
from app.services.auth_service import create_managed_account  # noqa: E402
from app.services.resource_service import create_resource  # noqa: E402
from app.services.storage import get_storage_service  # noqa: E402
from app.services.student_service import upload_profile_image  # noqa: E402

DEMO_PASSWORD = "Demo@1234"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
TODAY = date.today()

# Real inboxes for this demo, swapped in for one login of each role so the
# app's actual email flows (fee reminders, payment receipts) land somewhere
# a person can be shown, instead of @smartbatch.demo addresses nobody reads.
REAL_DEMO_EMAILS = {
    "Deebhika Kumaran": "deebhikakumran@gmail.com",
    "Jessy Kumaran": "jessykumaran@gmail.com",
}

random.seed(42)
_phone_seq = itertools.count(1)
_admission_seq = itertools.count(1)


def _phone():
    return f"9{next(_phone_seq):09d}"


def _admission_no():
    return f"SB2026{next(_admission_seq):03d}"


def _file(filename, content_bytes, content_type="text/plain"):
    return FileStorage(stream=BytesIO(content_bytes), filename=filename, content_type=content_type)


def _photo(filename):
    return _file(filename, (FIXTURES_DIR / filename).read_bytes(), "image/jpeg")


def _cycle_str(d):
    return f"{d.year:04d}-{d.month:02d}"


def _add_months(d, months):
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 10)  # matches FEE_DUE_DAY_OF_MONTH's default of 10


# ---------------------------------------------------------------------------
# Wipe
# ---------------------------------------------------------------------------


def wipe_storage_objects():
    """Deletes real Supabase objects from the previous run -- wipe_demo_data()
    only clears DB rows, and this script is meant to be re-run repeatedly
    (after every Render restart), so without this every re-run would leak
    another set of profile photos/resource files into the bucket forever."""
    storage = get_storage_service()
    paths = [row[0] for row in Student.query.with_entities(Student.profile_image).all() if row[0]]
    paths += [row[0] for row in Resource.query.with_entities(Resource.storage_path).all() if row[0]]
    for path in paths:
        storage.delete(path)
    if paths:
        print(f"Deleted {len(paths)} object(s) from Supabase storage...")


def wipe_demo_data():
    print("Wiping existing data...")
    wipe_storage_objects()
    for model in (
        Notification,
        StudentFee,
        FeePlan,
        TestSubmission,
        Test,
        Submission,
        Homework,
        Attendance,
        Resource,
        ClassSubjectTeacher,
        Student,
        Parent,
        Teacher,
        SchoolClass,
        Subject,
        User,
    ):
        model.query.delete()
    db.session.commit()


# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------


def create_admin():
    print("Creating admin...")
    user = User(
        full_name="Blessey Rajavel",
        email="blesseyrajavel@gmail.com",
        password_hash=bcrypt.generate_password_hash(DEMO_PASSWORD).decode("utf-8"),
        phone=_phone(),
        role=RoleEnum.ADMIN,
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_teachers():
    print("Creating teachers...")
    teacher_a = create_managed_account(
        {
            "role": "teacher",
            "full_name": "Guhan Kumaran",
            "email": "guhankumaran@gmail.com",
            "password": DEMO_PASSWORD,
            "phone": _phone(),
        }
    ).teacher
    teacher_b = create_managed_account(
        {
            "role": "teacher",
            "full_name": "Arjun Deshmukh",
            "email": "arjun.deshmukh@smartbatch.demo",
            "password": DEMO_PASSWORD,
            "phone": _phone(),
        }
    ).teacher
    return teacher_a, teacher_b


def create_classes():
    print("Creating classes...")
    classes = {grade: SchoolClass(grade=grade) for grade in (6, 7, 8)}
    db.session.add_all(classes.values())
    db.session.commit()
    return classes


def create_subjects():
    print("Creating subjects...")
    subjects = {name: Subject(name=name) for name in ("Mathematics", "Science", "English")}
    db.session.add_all(subjects.values())
    db.session.commit()
    return subjects


def assign_teachers(classes, subjects, teacher_a, teacher_b):
    print("Assigning teachers to classes/subjects...")
    assignments = [
        (classes[6], subjects["Mathematics"], teacher_a),
        (classes[7], subjects["Mathematics"], teacher_a),
        (classes[8], subjects["Mathematics"], teacher_a),
        (classes[6], subjects["Science"], teacher_a),
        (classes[7], subjects["Science"], teacher_b),
        (classes[8], subjects["Science"], teacher_b),
        (classes[6], subjects["English"], teacher_b),
        (classes[7], subjects["English"], teacher_b),
        (classes[8], subjects["English"], teacher_b),
    ]
    for school_class, subject, teacher in assignments:
        db.session.add(ClassSubjectTeacher(class_id=school_class.id, subject_id=subject.id, teacher_id=teacher.id))
    db.session.commit()


# Grade 6 is dedicated to the three real facial-recognition demo students --
# group.png shows exactly these three, so a facial attendance run against
# grade 6 has no extra classmates to confuse the match.
FACE_STUDENTS = [
    ("Aarav Mehta", "person1.jpg", "Rajesh Mehta"),
    ("Diya Nair", "person2.jpg", "Lakshmi Nair"),
    ("Kabir Singh", "person3.jpg", "Manpreet Singh"),
]
REGULAR_STUDENTS = {
    7: [("Deebhika Kumaran", "Jessy Kumaran"), ("Rohan Gupta", "Anita Gupta"), ("Ishaan Verma", "Deepak Verma")],
    8: [("Ananya Iyer", "Kavita Iyer"), ("Vivaan Joshi", "Ramesh Joshi"), ("Sneha Reddy", "Padma Reddy")],
}


def _slug(name):
    return name.lower().replace(" ", ".")


def _create_student_with_parent(full_name, parent_name, class_id, admission_no):
    parent = create_managed_account(
        {
            "role": "parent",
            "full_name": parent_name,
            "email": REAL_DEMO_EMAILS.get(parent_name, f"{_slug(parent_name)}@smartbatch.demo"),
            "password": DEMO_PASSWORD,
            "phone": _phone(),
        }
    ).parent

    student = create_managed_account(
        {
            "role": "student",
            "full_name": full_name,
            "email": REAL_DEMO_EMAILS.get(full_name, f"{_slug(full_name)}@smartbatch.demo"),
            "password": DEMO_PASSWORD,
            "phone": _phone(),
            "admission_no": admission_no,
            "class_id": class_id,
            "parent_id": parent.id,
        }
    ).student
    return student


def create_students(classes):
    print("Creating students + parents...")
    students = []

    for full_name, photo_filename, parent_name in FACE_STUDENTS:
        admission_no = _admission_no()
        student = _create_student_with_parent(full_name, parent_name, classes[6].id, admission_no)
        upload_profile_image(student.id, _photo(photo_filename))
        students.append(student)
        print(f"  {full_name}: real profile photo ({photo_filename}) uploaded to Supabase")

    for grade, roster in REGULAR_STUDENTS.items():
        for full_name, parent_name in roster:
            admission_no = _admission_no()
            students.append(_create_student_with_parent(full_name, parent_name, classes[grade].id, admission_no))

    return students


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------


def create_resources(classes, subjects, teacher_a, teacher_b):
    print("Creating resources...")
    create_resource(
        _file("chapter3_notes.txt", b"Chapter 3: Fractions and Decimals -- worked examples and practice set.\n"),
        ResourceType.NOTE.value,
        subjects["Mathematics"].id,
        classes[6].id,
        teacher_a.user_id,
    )
    create_resource(
        _file("sample_question_paper.txt", b"Science Unit Test -- Sample Question Paper\n1. ...\n2. ...\n"),
        ResourceType.QUESTION_PAPER.value,
        subjects["Science"].id,
        classes[7].id,
        teacher_b.user_id,
    )


# ---------------------------------------------------------------------------
# Homework / tests with grades
# ---------------------------------------------------------------------------


def _students_in_class(students, class_id):
    return [s for s in students if s.class_id == class_id]


def create_homework_and_tests_with_grades(classes, subjects, teacher_a, students):
    print("Creating graded homework/test submissions...")
    left_ungraded = False  # leave exactly one submission PENDING, for demo variety

    for grade, school_class in classes.items():
        roster = _students_in_class(students, school_class.id)

        homework = Homework(
            class_id=school_class.id,
            subject_id=subjects["Mathematics"].id,
            title="Chapter 3 Worksheet",
            description="Complete all questions and show your work.",
            due_date=TODAY - timedelta(days=5),
            created_by=teacher_a.user_id,
            max_marks=100,
        )
        db.session.add(homework)
        db.session.commit()

        test = Test(
            class_id=school_class.id,
            subject_id=subjects["Science"].id,
            title="Unit Test 1",
            description="Covers chapters 1-3.",
            due_date=TODAY - timedelta(days=3),
            created_by=teacher_a.user_id,
            max_marks=50,
        )
        db.session.add(test)
        db.session.commit()

        for student in roster:
            grade_this_one = True
            if not left_ungraded:
                grade_this_one = False
                left_ungraded = True

            hw_submission = Submission(
                homework_id=homework.id,
                student_id=student.id,
                file_url=f"submissions/{homework.id}/{student.id}_demo.txt",
                submitted_at=datetime.combine(TODAY - timedelta(days=6), time(18, 0), tzinfo=timezone.utc),
                status=SubmissionStatus.GRADED if grade_this_one else SubmissionStatus.PENDING,
            )
            if grade_this_one:
                hw_submission.marks = random.randint(60, 98)
                hw_submission.feedback = "Good work."
                hw_submission.graded_by = teacher_a.user_id
            db.session.add(hw_submission)

            test_submission = TestSubmission(
                test_id=test.id,
                student_id=student.id,
                file_url=f"test-submissions/{test.id}/{student.id}_demo.txt",
                submitted_at=datetime.combine(TODAY - timedelta(days=4), time(18, 0), tzinfo=timezone.utc),
                marks=random.randint(30, 48),
                feedback="Well done.",
                graded_by=teacher_a.user_id,
                status=SubmissionStatus.GRADED,
            )
            db.session.add(test_submission)

        db.session.commit()


# ---------------------------------------------------------------------------
# Attendance history
# ---------------------------------------------------------------------------


def create_attendance_history(students, teacher_a):
    print("Creating two weeks of attendance history...")
    days = []
    d = TODAY - timedelta(days=1)
    while len(days) < 10:  # 10 weekdays ~= two calendar weeks
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)

    for day in days:
        for student in students:
            status = random.choices(
                [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE],
                weights=[80, 12, 8],
            )[0]
            db.session.add(
                Attendance(
                    student_id=student.id,
                    class_id=student.class_id,
                    date=day,
                    status=status,
                    marked_by=teacher_a.user_id,
                    method=AttendanceMethod.MANUAL,
                )
            )
    db.session.commit()


# ---------------------------------------------------------------------------
# Fee plans + invoice history
# ---------------------------------------------------------------------------


def create_fee_plans_and_invoices(students):
    print("Creating fee plans and invoice history...")
    amounts = [1500, 1800, 2000, 2500]

    for i, student in enumerate(students):
        plan = FeePlan(
            student_id=student.id,
            monthly_amount=amounts[i % len(amounts)],
            start_date=_add_months(TODAY, -4).replace(day=1),
            active=True,
        )
        db.session.add(plan)
        db.session.commit()

        last_month_due = _add_months(TODAY, -1)
        paid_fee = StudentFee(
            fee_plan_id=plan.id,
            student_id=student.id,
            cycle=_cycle_str(last_month_due),
            amount=plan.monthly_amount,
            due_date=last_month_due,
            status=FeeStatus.PAID,
            paid_at=datetime.combine(last_month_due, time(10, 0), tzinfo=timezone.utc),
            razorpay_order_id=f"order_demo_{student.id}_1",
            razorpay_payment_id=f"pay_demo_{student.id}_1",
            transaction_id=f"pay_demo_{student.id}_1",
        )
        db.session.add(paid_fee)

        two_months_ago_due = _add_months(TODAY, -2)
        older_status = FeeStatus.OVERDUE if i % 3 == 0 else FeeStatus.PAID
        older_fee = StudentFee(
            fee_plan_id=plan.id,
            student_id=student.id,
            cycle=_cycle_str(two_months_ago_due),
            amount=plan.monthly_amount,
            due_date=two_months_ago_due,
            status=older_status,
            paid_at=None
            if older_status == FeeStatus.OVERDUE
            else datetime.combine(two_months_ago_due, time(10, 0), tzinfo=timezone.utc),
            razorpay_payment_id=None if older_status == FeeStatus.OVERDUE else f"pay_demo_{student.id}_0",
            transaction_id=None if older_status == FeeStatus.OVERDUE else f"pay_demo_{student.id}_0",
        )
        db.session.add(older_fee)

        upcoming_due = _add_months(TODAY, 1)
        upcoming_fee = StudentFee(
            fee_plan_id=plan.id,
            student_id=student.id,
            cycle=_cycle_str(upcoming_due),
            amount=plan.monthly_amount,
            due_date=upcoming_due,
            status=FeeStatus.PENDING,
        )
        db.session.add(upcoming_fee)

    db.session.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()  # safety net -- `flask db upgrade` should already have run
        wipe_demo_data()

        create_admin()
        teacher_a, teacher_b = create_teachers()
        classes = create_classes()
        subjects = create_subjects()
        assign_teachers(classes, subjects, teacher_a, teacher_b)

        students = create_students(classes)
        create_resources(classes, subjects, teacher_a, teacher_b)
        create_homework_and_tests_with_grades(classes, subjects, teacher_a, students)
        create_attendance_history(students, teacher_a)
        create_fee_plans_and_invoices(students)

        print(f"\nDone. {len(students)} students across {len(classes)} classes.")
        print(f"All accounts use the password: {DEMO_PASSWORD}")
        print("Admin login: blesseyrajavel@gmail.com")


if __name__ == "__main__":
    seed()