"""/api/homework delete (admin/teacher)."""

from datetime import datetime, timezone

from app.extensions import db
from app.models.homework import Homework, Submission, SubmissionStatus
from conftest import create_assignment, create_class, create_student, create_subject, create_teacher, login_as


def _create_homework(admin, school_class, subject, title="Worksheet 1"):
    resp = admin.post(
        "/api/homework",
        json={
            "class_id": school_class.id,
            "subject_id": subject.id,
            "title": title,
            "due_date": "2026-03-01",
            "max_marks": 100,
        },
    )
    assert resp.status_code == 201
    return resp.get_json()


def test_delete_homework_forbidden_for_parent_and_student(parent, student):
    parent_authed, _ = parent
    student_authed, _ = student
    assert parent_authed.delete("/api/homework/1").status_code == 403
    assert student_authed.delete("/api/homework/1").status_code == 403


def test_delete_homework_by_admin_success(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    homework = _create_homework(admin, school_class, subject)
    resp = admin.delete(f"/api/homework/{homework['id']}")
    assert resp.status_code == 204
    assert admin.get(f"/api/homework/{homework['id']}").status_code == 404


def test_delete_homework_by_creating_teacher_success(teacher):
    authed, teacher_row = teacher
    school_class = create_class(2)
    subject = create_subject("English")
    create_assignment(school_class.id, subject.id, teacher_row.id)

    resp = authed.post(
        "/api/homework",
        json={
            "class_id": school_class.id,
            "subject_id": subject.id,
            "title": "Essay draft",
            "due_date": "2026-03-05",
            "max_marks": 50,
        },
    )
    assert resp.status_code == 201
    homework_id = resp.get_json()["id"]

    delete_resp = authed.delete(f"/api/homework/{homework_id}")
    assert delete_resp.status_code == 204


def test_delete_homework_by_non_creating_teacher_forbidden(make_client):
    school_class = create_class(3)
    subject = create_subject("Science")
    creator = create_teacher(email="creator@test.com")
    other_teacher = create_teacher(email="othercreator@test.com")

    creator_authed = login_as(make_client(), creator.user.email)
    homework_id = _create_homework(creator_authed, school_class, subject)["id"]

    other_authed = login_as(make_client(), other_teacher.user.email)
    resp = other_authed.delete(f"/api/homework/{homework_id}")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "forbidden"


def test_delete_homework_not_found(admin):
    resp = admin.delete("/api/homework/999999")
    assert resp.status_code == 404


def test_delete_homework_cascades_submissions(admin, app, fake_storage, monkeypatch):
    monkeypatch.setattr("app.services.homework_service.get_storage_service", lambda: fake_storage)
    monkeypatch.setattr("app.services.homework_submission_service.get_storage_service", lambda: fake_storage)

    school_class = create_class(4)
    subject = create_subject("Physics")
    student_row = create_student(class_id=school_class.id)
    homework = _create_homework(admin, school_class, subject)

    file_path = f"submissions/{homework['id']}/sample.pdf"
    fake_storage.store[file_path] = b"homework bytes"

    with app.app_context():
        submission = Submission(
            homework_id=homework["id"],
            student_id=student_row.id,
            file_url=file_path,
            submitted_at=datetime.now(timezone.utc),
            status=SubmissionStatus.PENDING,
        )
        db.session.add(submission)
        db.session.commit()
        submission_id = submission.id

    resp = admin.delete(f"/api/homework/{homework['id']}")
    assert resp.status_code == 204
    assert file_path not in fake_storage.store

    with app.app_context():
        assert Homework.query.get(homework["id"]) is None
        assert Submission.query.get(submission_id) is None
