"""AI auto-grading for tests: scheduling, background workers, per-question scoring."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from flask import current_app

from app.extensions import db, scheduler
from app.models.homework import SubmissionStatus
from app.models.student import Student
from app.models.test import Test, TestSubmission
from app.models.test_evaluation import EvaluationStatus, GradedSource, TestAnswerKeyQuestion, TestQuestionScore
from app.services.notification_service import NotificationService
from app.services.storage import get_storage_service
from app.services.test_service import get_test_or_404
from app.utils.dates import isoformat_utc
from app.utils.errors import ApiError, not_found
from rag.extraction.pdf_extractor import extract_pdf
from rag.generation.grading import ParsedQuestion, grade_response, parse_answer_key

logger = logging.getLogger(__name__)

_app = None


def _utcnow():
    return datetime.now(timezone.utc)


def _job_id(test_id):
    return f"test-evaluation-{test_id}"


def _evaluation_enabled():
    return current_app.config.get("AI_GRADING_ENABLED", True)


def _max_chars():
    return current_app.config.get("AI_GRADING_MAX_CHARS", 50000)


def _worker_count():
    return current_app.config.get("AI_GRADING_WORKERS", 3)


def serialize_evaluation_status(test):
    total_students = Student.query.filter_by(class_id=test.class_id).count()
    graded_count = TestSubmission.query.filter_by(test_id=test.id, status=SubmissionStatus.GRADED).count()
    submitted_count = TestSubmission.query.filter_by(test_id=test.id).count()
    return {
        "test_id": test.id,
        "evaluation_status": test.evaluation_status.value,
        "evaluation_scheduled_at": isoformat_utc(test.evaluation_scheduled_at),
        "evaluation_started_at": isoformat_utc(test.evaluation_started_at),
        "evaluation_completed_at": isoformat_utc(test.evaluation_completed_at),
        "evaluation_error": test.evaluation_error,
        "total_students": total_students,
        "submitted_count": submitted_count,
        "graded_count": graded_count,
        "answer_key_question_count": TestAnswerKeyQuestion.query.filter_by(test_id=test.id).count(),
    }


def _ensure_can_schedule(test):
    if not _evaluation_enabled():
        raise ApiError("AI grading is disabled", "grading_disabled", 503)
    if not test.answer_key_resource_id:
        raise ApiError("Test has no answer key attached", "missing_answer_key", 400)
    if test.evaluation_status == EvaluationStatus.RUNNING:
        raise ApiError("Evaluation is already running", "evaluation_running", 409)
    if test.evaluation_status == EvaluationStatus.COMPLETED:
        raise ApiError("Evaluation has already completed", "evaluation_completed", 409)


def _register_job(test):
    scheduler.add_job(
        func=_run_scheduled_evaluation,
        trigger="date",
        run_date=test.evaluation_scheduled_at,
        args=[test.id],
        id=_job_id(test.id),
        replace_existing=True,
        misfire_grace_time=None,
    )


def _remove_job(test_id):
    job_id = _job_id(test_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


def schedule_evaluation(test_id, scheduled_at):
    test = get_test_or_404(test_id)
    _ensure_can_schedule(test)
    if scheduled_at <= _utcnow():
        raise ApiError("scheduled_at must be in the future", "invalid_schedule", 400)

    test.evaluation_status = EvaluationStatus.SCHEDULED
    test.evaluation_scheduled_at = scheduled_at
    test.evaluation_error = None
    db.session.commit()
    _register_job(test)
    return test


def run_evaluation_now(test_id):
    test = get_test_or_404(test_id)
    _ensure_can_schedule(test)
    _remove_job(test_id)
    test.evaluation_status = EvaluationStatus.SCHEDULED
    test.evaluation_scheduled_at = _utcnow()
    test.evaluation_error = None
    db.session.commit()

    if current_app.testing:
        _run_evaluation(test_id)
    else:
        import threading

        app = current_app._get_current_object()
        threading.Thread(target=_run_evaluation_with_app, args=(app, test_id), daemon=True).start()
    return test


def cancel_evaluation(test_id):
    test = get_test_or_404(test_id)
    if test.evaluation_status not in (EvaluationStatus.SCHEDULED, EvaluationStatus.FAILED):
        raise ApiError("Only scheduled or failed evaluations can be cancelled", "invalid_state", 409)
    _remove_job(test_id)
    test.evaluation_status = EvaluationStatus.NOT_SCHEDULED
    test.evaluation_scheduled_at = None
    test.evaluation_error = None
    db.session.commit()
    return test


def get_evaluation_status(test_id):
    test = get_test_or_404(test_id)
    return serialize_evaluation_status(test)


def _run_scheduled_evaluation(test_id):
    with _app.app_context():
        test = Test.query.get(test_id)
        if test is None or test.evaluation_status != EvaluationStatus.SCHEDULED:
            return
        _run_evaluation(test_id)


def _run_evaluation_with_app(app, test_id):
    with app.app_context():
        _run_evaluation(test_id)


def _download_resource_bytes(storage_path):
    return get_storage_service().download(storage_path)


def _parse_and_store_answer_key(test):
    TestAnswerKeyQuestion.query.filter_by(test_id=test.id).delete()
    db.session.commit()

    resource = test.answer_key_resource
    if resource is None:
        raise ApiError("Answer key resource not found", "missing_answer_key", 400)

    pdf_bytes = _download_resource_bytes(resource.storage_path)
    extracted = extract_pdf(pdf_bytes, title=resource.filename or "Answer Key")
    text = "\n\n".join(block.text for block in extracted.blocks if block.text.strip())
    if not text.strip():
        raise ValueError("Answer key PDF contained no extractable text")

    parsed = parse_answer_key(text, test.max_marks or 100, max_chars=_max_chars())
    for question in parsed.questions:
        db.session.add(
            TestAnswerKeyQuestion(
                test_id=test.id,
                question_no=question.question_no,
                question_text=question.question_text,
                expected_answer=question.expected_answer,
                max_marks=question.max_marks,
            )
        )
    db.session.commit()
    return parsed.questions


def _questions_for_test(test_id):
    rows = (
        TestAnswerKeyQuestion.query.filter_by(test_id=test_id)
        .order_by(TestAnswerKeyQuestion.question_no)
        .all()
    )
    return [
        ParsedQuestion(
            question_no=row.question_no,
            question_text=row.question_text,
            expected_answer=row.expected_answer,
            max_marks=row.max_marks,
        )
        for row in rows
    ]


def _grade_missing_student(test_id, student_id, questions, app):
    with app.app_context():
        try:
            submission = TestSubmission.query.filter_by(test_id=test_id, student_id=student_id).first()
            if submission is None:
                submission = TestSubmission(
                    test_id=test_id,
                    student_id=student_id,
                    file_url=f"test-submissions/{test_id}/no-response-{student_id}.txt",
                    submitted_at=_utcnow(),
                    status=SubmissionStatus.GRADED,
                    marks=0,
                    feedback="No response submitted",
                    graded_source=GradedSource.AI,
                    ai_marks=0,
                    ai_feedback="No response submitted",
                    ai_graded_at=_utcnow(),
                )
                db.session.add(submission)
                db.session.flush()
            else:
                submission.marks = 0
                submission.feedback = "No response submitted"
                submission.status = SubmissionStatus.GRADED
                submission.graded_source = GradedSource.AI
                submission.ai_marks = 0
                submission.ai_feedback = "No response submitted"
                submission.ai_graded_at = _utcnow()

            TestQuestionScore.query.filter_by(submission_id=submission.id).delete()
            for question in questions:
                db.session.add(
                    TestQuestionScore(
                        submission_id=submission.id,
                        answer_key_question_id=_question_row_id(test_id, question.question_no),
                        awarded_marks=0,
                        feedback="No response submitted",
                        student_excerpt="",
                    )
                )
            db.session.commit()

            student = Student.query.get(student_id)
            test = Test.query.get(test_id)
            if student and test:
                try:
                    NotificationService.notify_marks_published(
                        student, "test", test.title, test.subject.name, 0, max_marks=test.max_marks
                    )
                except Exception:
                    logger.exception("Failed to notify student %s for missing submission", student_id)
        except Exception:
            db.session.rollback()
            logger.exception("Failed to grade missing submission for student %s test %s", student_id, test_id)
        finally:
            db.session.remove()


def _question_row_id(test_id, question_no):
    row = TestAnswerKeyQuestion.query.filter_by(test_id=test_id, question_no=question_no).first()
    if row is None:
        raise ValueError(f"Question {question_no} not found for test {test_id}")
    return row.id


def _grade_submission_worker(submission_id, questions, grade, subject, app):
    with app.app_context():
        try:
            submission = TestSubmission.query.get(submission_id)
            if submission is None:
                return
            if submission.graded_source == GradedSource.MANUAL and submission.status == SubmissionStatus.GRADED:
                return

            pdf_bytes = _download_resource_bytes(submission.file_url)
            extracted = extract_pdf(pdf_bytes, title="Student Response")
            response_text = "\n\n".join(block.text for block in extracted.blocks if block.text.strip())
            if not response_text.strip():
                response_text = "(empty or unreadable response)"

            graded = grade_response(
                questions,
                response_text,
                grade=grade,
                subject=subject,
                max_chars=_max_chars(),
            )

            TestQuestionScore.query.filter_by(submission_id=submission.id).delete()
            total = 0
            for item in graded.questions:
                db.session.add(
                    TestQuestionScore(
                        submission_id=submission.id,
                        answer_key_question_id=_question_row_id(submission.test_id, item.question_no),
                        awarded_marks=item.awarded_marks,
                        feedback=item.feedback,
                        student_excerpt=item.student_excerpt,
                    )
                )
                total += item.awarded_marks

            submission.ai_marks = total
            submission.ai_feedback = graded.overall_feedback or "Graded by AI"
            submission.ai_model_used = graded.model_used
            submission.ai_graded_at = _utcnow()
            submission.marks = total
            submission.feedback = graded.overall_feedback or "Graded by AI"
            submission.status = SubmissionStatus.GRADED
            submission.graded_source = GradedSource.AI
            db.session.commit()

            try:
                NotificationService.notify_marks_published(
                    submission.student,
                    "test",
                    submission.test.title,
                    submission.test.subject.name,
                    total,
                    max_marks=submission.test.max_marks,
                )
            except Exception:
                logger.exception("Failed to notify for submission %s", submission_id)
        except Exception:
            db.session.rollback()
            logger.exception("Failed to AI-grade submission %s", submission_id)
        finally:
            db.session.remove()


def _run_evaluation(test_id):
    test = Test.query.get(test_id)
    if test is None:
        return

    test.evaluation_status = EvaluationStatus.RUNNING
    test.evaluation_started_at = _utcnow()
    test.evaluation_completed_at = None
    test.evaluation_error = None
    db.session.commit()

    app = current_app._get_current_object()
    try:
        questions = _parse_and_store_answer_key(test)
        if not questions:
            raise ValueError("No questions parsed from answer key")

        students = Student.query.filter_by(class_id=test.class_id).all()
        submission_by_student = {
            s.student_id: s
            for s in TestSubmission.query.filter_by(test_id=test.id).all()
        }

        if app.config.get("TESTING"):
            for student in students:
                existing = submission_by_student.get(student.id)
                if existing is None:
                    _grade_missing_student(test.id, student.id, questions, app)
                else:
                    _grade_submission_worker(
                        existing.id, questions, test.school_class.grade, test.subject.name, app
                    )
        else:
            futures = []
            with ThreadPoolExecutor(max_workers=_worker_count()) as pool:
                for student in students:
                    existing = submission_by_student.get(student.id)
                    if existing is None:
                        futures.append(pool.submit(_grade_missing_student, test.id, student.id, questions, app))
                    else:
                        futures.append(
                            pool.submit(
                                _grade_submission_worker,
                                existing.id,
                                questions,
                                test.school_class.grade,
                                test.subject.name,
                                app,
                            )
                        )
                for future in as_completed(futures):
                    future.result()

        test = Test.query.get(test_id)
        test.evaluation_status = EvaluationStatus.COMPLETED
        test.evaluation_completed_at = _utcnow()
        db.session.commit()
    except Exception as exc:
        logger.exception("Evaluation failed for test %s", test_id)
        db.session.rollback()
        test = Test.query.get(test_id)
        if test:
            test.evaluation_status = EvaluationStatus.FAILED
            test.evaluation_error = str(exc)
            db.session.commit()


def init_evaluation_scheduler(app):
    """Re-register scheduled test evaluations after process restart."""
    global _app

    if not app.config.get("SCHEDULER_ENABLED", True):
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    _app = app
    if not scheduler.running:
        scheduler.start()

    with app.app_context():
        try:
            stuck = Test.query.filter(Test.evaluation_status == EvaluationStatus.RUNNING).all()
            for test in stuck:
                test.evaluation_status = EvaluationStatus.FAILED
                test.evaluation_error = (
                    "Evaluation was interrupted by a server restart. Use Run now to retry."
                )
            if stuck:
                db.session.commit()
                logger.warning(
                    "Reset %d test evaluation(s) stuck in RUNNING after restart",
                    len(stuck),
                )

            pending = Test.query.filter(
                Test.evaluation_status == EvaluationStatus.SCHEDULED,
                Test.evaluation_scheduled_at.isnot(None),
            ).all()
        except Exception:
            return
        for test in pending:
            _register_job(test)
