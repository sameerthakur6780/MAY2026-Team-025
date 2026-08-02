from pathlib import Path

from flask import current_app
from sqlalchemy import false
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.academic import SchoolClass
from app.models.attendance import Attendance, AttendanceMethod, AttendanceStatus
from app.models.student import Student
from app.services.facial_recognition import detect_faces, match_embedding
from app.utils.errors import ApiError, forbidden, not_found
from app.utils.scoping import current_parent, current_student, current_teacher, teacher_class_ids


def serialize_attendance(attendance):
    return {
        "id": attendance.id,
        "student_id": attendance.student_id,
        "student_name": attendance.student.user.full_name,
        "class_id": attendance.class_id,
        "grade": attendance.school_class.grade,
        "date": attendance.date.isoformat(),
        "status": attendance.status.value,
        "method": attendance.method.value,
        "marked_by": attendance.marked_by,
        "marked_by_name": attendance.marker.full_name,
        "created_at": attendance.created_at.isoformat(),
        "updated_at": attendance.updated_at.isoformat(),
    }


def get_attendance_or_404(attendance_id):
    attendance = Attendance.query.get(attendance_id)
    if attendance is None:
        raise not_found("Attendance record")
    return attendance


def bulk_mark_attendance(class_id, date, entries, method, marked_by):
    if SchoolClass.query.get(class_id) is None:
        raise not_found("Class")

    student_ids = [entry["student_id"] for entry in entries]
    students_by_id = {s.id: s for s in Student.query.filter(Student.id.in_(student_ids)).all()}

    missing = [sid for sid in student_ids if sid not in students_by_id]
    if missing:
        raise ApiError(f"Unknown student_id(s): {missing}", "not_found", 404)

    wrong_class = [sid for sid in student_ids if students_by_id[sid].class_id != class_id]
    if wrong_class:
        raise ApiError(
            f"student_id(s) not enrolled in class {class_id}: {wrong_class}",
            "invalid_student_class",
            400,
        )

    existing_student_ids = {
        row[0]
        for row in Attendance.query.with_entities(Attendance.student_id)
        .filter(
            Attendance.class_id == class_id,
            Attendance.date == date,
            Attendance.student_id.in_(student_ids),
        )
        .all()
    }

    created = []
    for entry in entries:
        sid = entry["student_id"]
        if sid in existing_student_ids:
            continue
        record = Attendance(
            student_id=sid,
            class_id=class_id,
            date=date,
            status=AttendanceStatus(entry["status"]),
            marked_by=marked_by,
            method=AttendanceMethod(method),
        )
        db.session.add(record)
        created.append(record)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError(
            "Some entries conflicted with existing records for this class/date",
            "conflict",
            409,
        )

    return created, sorted(existing_student_ids)


def mark_attendance_facial(class_id, date, file_storage, marked_by):
    if not file_storage or not file_storage.filename:
        raise ApiError("No image was uploaded", "missing_file", 400)

    allowed = current_app.config["FACE_IMAGE_ALLOWED_EXTENSIONS"]
    ext = Path(file_storage.filename).suffix.lstrip(".").lower()
    if ext not in allowed:
        raise ApiError(
            f"File type .{ext or '?'} isn't allowed. Allowed types: {', '.join(sorted(allowed))}",
            "invalid_file_type",
            400,
        )

    image_bytes = file_storage.read()
    if len(image_bytes) == 0:
        raise ApiError("Uploaded image is empty", "empty_file", 400)
    max_size = current_app.config["MAX_UPLOAD_SIZE_BYTES"]
    if len(image_bytes) > max_size:
        raise ApiError(f"Image exceeds the {max_size // (1024 * 1024)}MB size limit", "file_too_large", 400)

    if SchoolClass.query.get(class_id) is None:
        raise not_found("Class")

    faces = detect_faces(image_bytes)

    candidates = Student.query.filter(
        Student.class_id == class_id, Student.face_embedding.isnot(None)
    ).all()
    candidate_pairs = [(s.id, s.face_embedding) for s in candidates]

    high = current_app.config["FACE_HIGH_CONFIDENCE_THRESHOLD"]
    low = current_app.config["FACE_LOW_CONFIDENCE_THRESHOLD"]

    auto_match_by_student = {}
    needs_confirmation = []

    for idx, face in enumerate(faces):
        student_id, confidence = match_embedding(face["embedding"], candidate_pairs)
        if student_id is not None and confidence >= high:
            if student_id not in auto_match_by_student or confidence > auto_match_by_student[student_id]:
                auto_match_by_student[student_id] = confidence
        elif student_id is not None and confidence >= low:
            needs_confirmation.append(
                {"face_index": idx, "best_match_student_id": student_id, "confidence": round(confidence, 3)}
            )
        else:
            needs_confirmation.append({"face_index": idx, "best_match_student_id": None, "confidence": None})

    # A face that ended up auto-marked doesn't also need to be listed as
    # "needs confirmation" just because a second, weaker-matching face also
    # pointed at the same student.
    needs_confirmation = [
        item for item in needs_confirmation if item["best_match_student_id"] not in auto_match_by_student
    ]

    entries = [{"student_id": sid, "status": "present"} for sid in auto_match_by_student]
    if entries:
        created, skipped_student_ids = bulk_mark_attendance(class_id, date, entries, "facial", marked_by)
    else:
        created, skipped_student_ids = [], []

    students_without_photo = Student.query.filter(
        Student.class_id == class_id, Student.face_embedding.is_(None)
    ).count()

    return {
        "faces_detected": len(faces),
        "auto_marked": [
            {"student_id": record.student_id, "confidence": round(auto_match_by_student[record.student_id], 3)}
            for record in created
        ],
        "skipped_student_ids": skipped_student_ids,
        "needs_confirmation": needs_confirmation,
        "students_without_profile_photo": students_without_photo,
    }


def update_attendance(attendance_id, data):
    attendance = get_attendance_or_404(attendance_id)
    if "status" in data:
        attendance.status = AttendanceStatus(data["status"])
    if "method" in data:
        attendance.method = AttendanceMethod(data["method"])
    db.session.commit()
    return attendance


def _scoped_query(role):
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


def list_attendance_query(role, student_id=None, class_id=None, date_from=None, date_to=None):
    query = _scoped_query(role)
    if student_id is not None:
        query = query.filter(Attendance.student_id == student_id)
    if class_id is not None:
        query = query.filter(Attendance.class_id == class_id)
    if date_from is not None:
        query = query.filter(Attendance.date >= date_from)
    if date_to is not None:
        query = query.filter(Attendance.date <= date_to)
    return query.order_by(Attendance.date.desc(), Attendance.student_id)
