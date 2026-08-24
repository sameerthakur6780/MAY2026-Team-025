"""LLM-based answer-key parsing and per-question grading."""

from __future__ import annotations

from pydantic import BaseModel, Field, ValidationError

from rag.config import get_rag_config
from rag.generation.json_utils import extract_json_object
from rag.generation.llm_router import completion_json_with_fallback, completion_with_fallback


class ParsedQuestion(BaseModel):
    question_no: int
    question_text: str
    expected_answer: str
    max_marks: int


class ParsedAnswerKey(BaseModel):
    questions: list[ParsedQuestion] = Field(default_factory=list)


class QuestionGrade(BaseModel):
    question_no: int
    awarded_marks: int
    feedback: str
    student_excerpt: str = ""


class GradedResponse(BaseModel):
    questions: list[QuestionGrade] = Field(default_factory=list)
    overall_feedback: str = ""
    model_used: str = ""


PARSE_KEY_SYSTEM = (
    "You parse exam answer keys into structured questions. Extract every question with its "
    "expected answer and marks. The sum of max_marks across all questions must equal the "
    "provided total_marks. If individual marks are not stated, distribute total_marks evenly "
    "across questions (adjust the last question so the sum is exact). "
    'Respond with JSON only: {"questions": [{"question_no": 1, "question_text": "...", '
    '"expected_answer": "...", "max_marks": 5}]}'
)

GRADE_SYSTEM = (
    "You are an exam grader. Compare the student's response against the expected answers. "
    "Award marks strictly from the rubric: never exceed max_marks for any question, never "
    "award marks for content not present in the student response, and be fair on partial "
    "credit when the student shows partial understanding. "
    'Respond with JSON only: {"questions": [{"question_no": 1, "awarded_marks": 3, '
    '"feedback": "brief reason", "student_excerpt": "relevant quote from student"}], '
    '"overall_feedback": "summary"}'
)


def _truncate(text: str, limit: int) -> str:
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "\n...[truncated]"


def _validate_parsed_key(parsed: ParsedAnswerKey, total_marks: int) -> ParsedAnswerKey:
    if not parsed.questions:
        raise ValueError("Answer key contained no questions")
    seen = set()
    for question in parsed.questions:
        if question.question_no in seen:
            raise ValueError(f"Duplicate question_no {question.question_no}")
        seen.add(question.question_no)
        if question.max_marks < 0:
            raise ValueError(f"Question {question.question_no} has negative max_marks")
    total = sum(q.max_marks for q in parsed.questions)
    if total != total_marks:
        raise ValueError(f"Parsed marks sum {total} != expected total {total_marks}")
    return parsed


def parse_answer_key(text: str, total_marks: int, *, max_chars: int = 50000) -> ParsedAnswerKey:
    """Parse raw answer-key text into structured questions."""
    trimmed = _truncate(text, max_chars)
    messages = [
        {"role": "system", "content": PARSE_KEY_SYSTEM},
        {
            "role": "user",
            "content": f"total_marks: {total_marks}\n\nAnswer key:\n{trimmed}",
        },
    ]
    # The response echoes back every question's text and expected answer as
    # JSON, so it can be as large as the source document -- give it headroom
    # proportional to the input rather than the small RAG-rewrite budget.
    max_tokens = max(get_rag_config().grading_max_output_tokens, len(trimmed) // 2)
    try:
        payload, _model = completion_json_with_fallback(messages, temperature=0.0, max_tokens=max_tokens)
        parsed = ParsedAnswerKey.model_validate(payload)
        return _validate_parsed_key(parsed, total_marks)
    except (ValidationError, ValueError, KeyError):
        raw, _model = completion_with_fallback(messages, temperature=0.0, max_tokens=max_tokens)
        payload = extract_json_object(raw, salvage_truncated=True)
        if payload is None:
            raise ValueError("LLM response did not contain valid JSON for answer key parsing")
        parsed = ParsedAnswerKey.model_validate(payload)
        return _validate_parsed_key(parsed, total_marks)


def _format_rubric(questions: list[ParsedQuestion]) -> str:
    lines = []
    for q in questions:
        lines.append(
            f"Q{q.question_no} (max {q.max_marks} marks)\n"
            f"Question: {q.question_text}\n"
            f"Expected answer: {q.expected_answer}"
        )
    return "\n\n".join(lines)


def grade_response(
    questions: list[ParsedQuestion],
    response_text: str,
    *,
    grade: int,
    subject: str,
    max_chars: int = 50000,
) -> GradedResponse:
    """Grade a student response against parsed answer-key questions."""
    trimmed = _truncate(response_text, max_chars)
    rubric = _format_rubric(questions)
    messages = [
        {"role": "system", "content": GRADE_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Grade: {grade}\nSubject: {subject}\n\n"
                f"Answer key rubric:\n{rubric}\n\n"
                f"Student response:\n{trimmed}"
            ),
        },
    ]
    # Scale the budget with the number of questions -- per-question feedback
    # and excerpts add up fast and must not get truncated mid-JSON.
    max_tokens = max(get_rag_config().grading_max_output_tokens, len(questions) * 300)
    try:
        payload, model_used = completion_json_with_fallback(messages, temperature=0.1, max_tokens=max_tokens)
        graded = GradedResponse.model_validate(payload)
        graded.model_used = model_used
        return _clamp_grades(graded, questions, model_used)
    except (ValidationError, ValueError, KeyError):
        raw, model_used = completion_with_fallback(messages, temperature=0.1, max_tokens=max_tokens)
        payload = extract_json_object(raw, salvage_truncated=True)
        if payload is None:
            raise ValueError("LLM response did not contain valid JSON for grading")
        graded = GradedResponse.model_validate(payload)
        graded.model_used = model_used
        return _clamp_grades(graded, questions, model_used)


def _clamp_grades(graded: GradedResponse, questions: list[ParsedQuestion], model_used: str) -> GradedResponse:
    max_by_no = {q.question_no: q.max_marks for q in questions}
    clamped: list[QuestionGrade] = []
    for item in graded.questions:
        cap = max_by_no.get(item.question_no)
        if cap is None:
            continue
        awarded = max(0, min(item.awarded_marks, cap))
        clamped.append(
            QuestionGrade(
                question_no=item.question_no,
                awarded_marks=awarded,
                feedback=item.feedback.strip(),
                student_excerpt=item.student_excerpt.strip(),
            )
        )
    return GradedResponse(
        questions=clamped,
        overall_feedback=graded.overall_feedback.strip(),
        model_used=model_used,
    )
