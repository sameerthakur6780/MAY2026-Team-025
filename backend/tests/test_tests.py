"""/api/tests delete (creator teacher only)."""

import io
from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db, scheduler
from app.models.resource import Resource
from app.models.test import Test, TestSubmission
from app.models.test_evaluation import EvaluationStatus, TestAnswerKeyQuestion, TestQuestionScore
from app.models.homework import SubmissionStatus
from app.services.ai_grading_service import _job_id
from conftest import (
    create_assignment,
    create_class,
    create_student,
    create_subject,
    create_teacher,
    login_as,
    next_id,
)


@pytest.fixture(autouse=True)
def patch_storage(fake_storage, monkeypatch):
    monkeypatch.setattr("app.services.resource_service.get_storage_service", lambda: fake_storage)
    monkeypatch.setattr("app.services.test_service.get_storage_service", lambda: fake_storage)
    monkeypatch.setattr("app.services.test_submission_service.get_storage_service", lambda: fake_storage)


def _upload(authed, school_class, subject, rtype, filename="doc.pdf", content=b"%PDF-1.4 fake"):
    return authed.post(
        "/api/resources",
        data={
            "type": rtype,
            "subject_id": str(subject.id),
            "class_id": str(school_class.id),
            "file": (io.BytesIO(content), filename),
        },
        content_type="multipart/form-data",
    )


def _create_test_with_resources(app, school_class, subject, teacher_row=None):
    uploader = login_as(app.test_client(), (teacher_row or create_teacher()).user.email)
    qp = _upload(uploader, school_class, subject, "question_paper", "paper.pdf").get_json()
    ak = _upload(uploader, school_class, subject, "answer_key", "key.pdf").get_json()
    resp = uploader.post(
        "/api/tests",
        json={
            "class_id": school_class.id,
            "subject_id": subject.id,
            "title": "Unit Test 1",
            "due_date": "2026-09-01T23:59:00",
            "max_marks": 10,
            "question_paper_resource_id": qp["id"],
            "answer_key_resource_id": ak["id"],
        },
    )
    assert resp.status_code == 201
    return uploader, resp.get_json(), qp, ak


def test_delete_test_forbidden_for_admin_parent_student(app, admin, parent, student):
    school_class = create_class(1)
    subject = create_subject(f"Maths-{next_id()}")
    _, test_data, _, _ = _create_test_with_resources(app, school_class, subject)
    test_id = test_data["id"]

    parent_authed, _ = parent
    student_authed, _ = student
    assert admin.delete(f"/api/tests/{test_id}").status_code == 403
    assert parent_authed.delete(f"/api/tests/{test_id}").status_code == 403
    assert student_authed.delete(f"/api/tests/{test_id}").status_code == 403


def test_delete_test_by_creator_teacher_success(app):
    school_class = create_class(2)
    subject = create_subject(f"English-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)
    teacher_authed, test_data, _, _ = _create_test_with_resources(
        app, school_class, subject, teacher_row=teacher_row
    )

    resp = teacher_authed.delete(f"/api/tests/{test_data['id']}")
    assert resp.status_code == 204
    assert teacher_authed.get(f"/api/tests/{test_data['id']}").status_code == 404


def test_delete_test_by_non_creating_teacher_forbidden(app, make_client):
    school_class = create_class(3)
    subject = create_subject(f"Science-{next_id()}")
    creator = create_teacher(email=f"creator-{next_id()}@test.com")
    other_teacher = create_teacher(email=f"other-{next_id()}@test.com")
    create_assignment(school_class.id, subject.id, creator.id)

    creator_authed, test_data, _, _ = _create_test_with_resources(
        app, school_class, subject, teacher_row=creator
    )
    other_authed = login_as(make_client(), other_teacher.user.email)

    resp = other_authed.delete(f"/api/tests/{test_data['id']}")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "forbidden"


def test_delete_test_not_found(teacher):
    authed, _ = teacher
    resp = authed.delete("/api/tests/999999")
    assert resp.status_code == 404


def test_delete_test_cascades_submissions_and_scores(app, fake_storage):
    school_class = create_class(4)
    subject = create_subject(f"Physics-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)
    student_row = create_student(class_id=school_class.id, admission_no=f"ADM{next_id()}")
    teacher_authed, test_data, _, _ = _create_test_with_resources(
        app, school_class, subject, teacher_row=teacher_row
    )

    file_path = f"test-submissions/{test_data['id']}/sample.pdf"
    fake_storage.store[file_path] = b"test bytes"

    with app.app_context():
        submission = TestSubmission(
            test_id=test_data["id"],
            student_id=student_row.id,
            file_url=file_path,
            submitted_at=datetime.now(timezone.utc),
            status=SubmissionStatus.PENDING,
        )
        db.session.add(submission)
        db.session.flush()

        question = TestAnswerKeyQuestion(
            test_id=test_data["id"],
            question_no=1,
            question_text="Q1",
            expected_answer="A",
            max_marks=5,
        )
        db.session.add(question)
        db.session.flush()
        score = TestQuestionScore(
            submission_id=submission.id,
            answer_key_question_id=question.id,
            awarded_marks=4,
            feedback="Good",
        )
        db.session.add(score)
        db.session.commit()
        submission_id = submission.id
        question_id = question.id
        score_id = score.id

    resp = teacher_authed.delete(f"/api/tests/{test_data['id']}")
    assert resp.status_code == 204
    assert file_path not in fake_storage.store

    with app.app_context():
        assert Test.query.get(test_data["id"]) is None
        assert TestSubmission.query.get(submission_id) is None
        assert TestAnswerKeyQuestion.query.get(question_id) is None
        assert TestQuestionScore.query.get(score_id) is None


def test_delete_test_blocked_while_evaluation_running(app):
    school_class = create_class(5)
    subject = create_subject(f"Chemistry-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)
    teacher_authed, test_data, _, _ = _create_test_with_resources(
        app, school_class, subject, teacher_row=teacher_row
    )

    with app.app_context():
        test = Test.query.get(test_data["id"])
        test.evaluation_status = EvaluationStatus.RUNNING
        db.session.commit()

    resp = teacher_authed.delete(f"/api/tests/{test_data['id']}")
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "evaluation_running"


def test_delete_test_removes_scheduled_job(app):
    school_class = create_class(6)
    subject = create_subject(f"Biology-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)
    teacher_authed, test_data, _, _ = _create_test_with_resources(
        app, school_class, subject, teacher_row=teacher_row
    )
    test_id = test_data["id"]

    scheduled_at = "2026-09-02T09:00:00"
    schedule_resp = teacher_authed.post(
        f"/api/tests/{test_id}/evaluation",
        json={"scheduled_at": scheduled_at},
    )
    assert schedule_resp.status_code == 201
    assert scheduler.get_job(_job_id(test_id)) is not None

    delete_resp = teacher_authed.delete(f"/api/tests/{test_id}")
    assert delete_resp.status_code == 204
    assert scheduler.get_job(_job_id(test_id)) is None


def test_delete_test_leaves_resources_intact(app):
    school_class = create_class(7)
    subject = create_subject(f"History-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)
    teacher_authed, test_data, qp, ak = _create_test_with_resources(
        app, school_class, subject, teacher_row=teacher_row
    )

    resp = teacher_authed.delete(f"/api/tests/{test_data['id']}")
    assert resp.status_code == 204

    with app.app_context():
        assert Resource.query.get(qp["id"]) is not None
        assert Resource.query.get(ak["id"]) is not None
