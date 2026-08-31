"""AI auto-grading for tests: scheduling, evaluation, visibility, and scoring."""

import io
from datetime import datetime, timedelta, timezone

import pytest

from app.extensions import db
from app.models.homework import SubmissionStatus
from app.models.resource import Resource, ResourceType
from app.models.test import Test, TestSubmission
from app.models.test_evaluation import EvaluationStatus, GradedSource, TestAnswerKeyQuestion, TestQuestionScore
from app.services.ai_grading_service import _run_evaluation
from app.services.test_submission_service import grade_submission
from conftest import (
    create_assignment,
    create_class,
    create_parent,
    create_student,
    create_subject,
    create_teacher,
    login_as,
    next_id,
)
from rag.generation.grading import GradedResponse, ParsedAnswerKey, ParsedQuestion, QuestionGrade


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
    return resp.get_json(), qp, ak


def _fake_parse_answer_key(text, total_marks, **kwargs):
    return ParsedAnswerKey(
        questions=[
            ParsedQuestion(
                question_no=1,
                question_text="What is 2+2?",
                expected_answer="4",
                max_marks=5,
            ),
            ParsedQuestion(
                question_no=2,
                question_text="What is 3+3?",
                expected_answer="6",
                max_marks=5,
            ),
        ]
    )


def _fake_grade_response(questions, response_text, **kwargs):
    return GradedResponse(
        questions=[
            QuestionGrade(question_no=1, awarded_marks=4, feedback="Almost correct", student_excerpt="4"),
            QuestionGrade(question_no=2, awarded_marks=5, feedback="Correct", student_excerpt="6"),
        ],
        overall_feedback="Good work",
        model_used="test-model",
    )


class _FakeBlock:
    def __init__(self, text):
        self.text = text


class _FakeExtraction:
    def __init__(self, text):
        self.blocks = [_FakeBlock(text)]


@pytest.fixture()
def grading_patches(fake_storage, monkeypatch):
    monkeypatch.setattr("app.services.ai_grading_service.get_storage_service", lambda: fake_storage)
    monkeypatch.setattr("app.services.test_submission_service.get_storage_service", lambda: fake_storage)
    monkeypatch.setattr("app.services.ai_grading_service._worker_count", lambda: 1)
    monkeypatch.setattr(
        "app.services.ai_grading_service.extract_pdf",
        lambda pdf_bytes, title="": _FakeExtraction("Sample extracted text"),
    )
    monkeypatch.setattr("app.services.ai_grading_service.parse_answer_key", _fake_parse_answer_key)
    monkeypatch.setattr("app.services.ai_grading_service.grade_response", _fake_grade_response)
    return fake_storage


def test_schedule_evaluation_requires_answer_key(teacher):
    authed, teacher_row = teacher
    school_class = create_class(5)
    subject = create_subject("Science")
    create_assignment(school_class.id, subject.id, teacher_row.id)
    resp = authed.post(
        "/api/tests",
        json={
            "class_id": school_class.id,
            "subject_id": subject.id,
            "title": "No key test",
            "due_date": "2026-09-01T23:59:00",
            "max_marks": 10,
        },
    )
    test_id = resp.get_json()["id"]
    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    bad = authed.post(f"/api/tests/{test_id}/evaluation", json={"scheduled_at": scheduled_at})
    assert bad.status_code == 400
    assert bad.get_json()["error"] == "missing_answer_key"


def test_admin_cannot_create_schedule_or_run_tests(app, admin):
    school_class = create_class(10)
    subject = create_subject(f"Geography-{next_id()}")
    test_data, _, _ = _create_test_with_resources(app, school_class, subject)

    create_resp = admin.post(
        "/api/tests",
        json={
            "class_id": school_class.id,
            "subject_id": subject.id,
            "title": "Admin-created test",
            "due_date": "2026-09-01T23:59:00",
            "max_marks": 10,
        },
    )
    assert create_resp.status_code == 403

    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    schedule_resp = admin.post(f"/api/tests/{test_data['id']}/evaluation", json={"scheduled_at": scheduled_at})
    assert schedule_resp.status_code == 403

    run_resp = admin.post(f"/api/tests/{test_data['id']}/evaluation/run")
    assert run_resp.status_code == 403

    assert admin.get(f"/api/tests/{test_data['id']}").status_code == 200


def test_run_evaluation_grades_submission_and_missing_student(app, grading_patches):
    school_class = create_class(6)
    subject = create_subject(f"Maths-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)

    test_data, qp, ak = _create_test_with_resources(app, school_class, subject, teacher_row=teacher_row)
    student_with = create_student(class_id=school_class.id, admission_no=f"ADM{next_id()}")
    create_student(class_id=school_class.id, admission_no=f"ADM{next_id()}")

    student_authed = login_as(app.test_client(), student_with.user.email)
    submit_resp = student_authed.post(
        f"/api/tests/{test_data['id']}/submissions",
        data={"file": (io.BytesIO(b"%PDF student answers"), "answers.pdf")},
        content_type="multipart/form-data",
    )
    assert submit_resp.status_code == 201

    with app.app_context():
        _run_evaluation(test_data["id"])

        test = Test.query.get(test_data["id"])
        assert test.evaluation_status == EvaluationStatus.COMPLETED

        submissions = TestSubmission.query.filter_by(test_id=test.id).all()
        assert len(submissions) == 2
        for sub in submissions:
            assert sub.status == SubmissionStatus.GRADED
            assert sub.graded_source == GradedSource.AI

        graded_with_response = next(s for s in submissions if "no-response" not in s.file_url)
        assert graded_with_response.marks == 9
        assert graded_with_response.ai_marks == 9

        missing = next(s for s in submissions if "no-response" in s.file_url)
        assert missing.marks == 0
        assert missing.feedback == "No response submitted"

        scores = TestQuestionScore.query.filter_by(submission_id=graded_with_response.id).all()
        assert len(scores) == 2
        assert sum(s.awarded_marks for s in scores) == 9


def test_question_scores_endpoint(app, grading_patches):
    school_class = create_class(7)
    subject = create_subject(f"Physics-{next_id()}")
    test_data, _, _ = _create_test_with_resources(app, school_class, subject)
    student_row = create_student(class_id=school_class.id)

    student_authed = login_as(app.test_client(), student_row.user.email)
    student_authed.post(
        f"/api/tests/{test_data['id']}/submissions",
        data={"file": (io.BytesIO(b"%PDF"), "ans.pdf")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        _run_evaluation(test_data["id"])
        submission = TestSubmission.query.filter_by(test_id=test_data["id"], student_id=student_row.id).first()

    scores_resp = student_authed.get(f"/api/test-submissions/{submission.id}/scores")
    assert scores_resp.status_code == 200
    body = scores_resp.get_json()
    assert len(body["scores"]) == 2
    assert body["scores"][0]["question_no"] == 1


def test_answer_key_hidden_until_evaluation_completed(app, grading_patches):
    school_class = create_class(8)
    subject = create_subject(f"Chemistry-{next_id()}")
    parent_row = create_parent()
    student_row = create_student(class_id=school_class.id, parent_id=parent_row.id)
    test_data, _, ak = _create_test_with_resources(app, school_class, subject)

    student_authed = login_as(app.test_client(), student_row.user.email)
    parent_authed = login_as(app.test_client(), parent_row.user.email)

    hidden_student = student_authed.get(f"/api/resources/{ak['id']}")
    assert hidden_student.status_code == 403

    list_resp = student_authed.get("/api/resources?per_page=100")
    assert all(r["id"] != ak["id"] for r in list_resp.get_json()["items"])

    with app.app_context():
        _run_evaluation(test_data["id"])

    visible = student_authed.get(f"/api/resources/{ak['id']}")
    assert visible.status_code == 200

    parent_visible = parent_authed.get(f"/api/resources/{ak['id']}")
    assert parent_visible.status_code == 200


def test_manual_grade_overrides_ai_marks(app, grading_patches):
    school_class = create_class(9)
    subject = create_subject(f"Biology-{next_id()}")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)
    test_data, _, _ = _create_test_with_resources(app, school_class, subject, teacher_row=teacher_row)
    student_row = create_student(class_id=school_class.id)

    student_authed = login_as(app.test_client(), student_row.user.email)
    student_authed.post(
        f"/api/tests/{test_data['id']}/submissions",
        data={"file": (io.BytesIO(b"%PDF"), "ans.pdf")},
        content_type="multipart/form-data",
    )

    with app.app_context():
        _run_evaluation(test_data["id"])
        submission = TestSubmission.query.filter_by(test_id=test_data["id"]).first()
        assert submission.marks == 9
        assert submission.graded_source == GradedSource.AI

        grade_submission(submission.id, 10, "Teacher override", teacher_row.user_id)
        db.session.refresh(submission)
        assert submission.marks == 10
        assert submission.graded_source == GradedSource.MANUAL

        _run_evaluation(test_data["id"])
        db.session.refresh(submission)
        assert submission.marks == 10
        assert submission.graded_source == GradedSource.MANUAL
