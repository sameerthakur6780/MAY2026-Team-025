"""/api/resources upload/list/get/download/delete, role-scoped."""

import io
from datetime import date

from app.extensions import db
from app.models.homework import Homework
from conftest import (
    create_assignment,
    create_class,
    create_parent,
    create_student,
    create_subject,
    create_teacher,
    login_as,
)


def _upload(authed, school_class, subject, filename="notes.pdf", content=b"%PDF-1.4 fake pdf content", rtype="note"):
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


# ---------------------------------------------------------------------------
# POST /api/resources
# ---------------------------------------------------------------------------


def test_upload_requires_authentication(client):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = client.post(
        "/api/resources",
        data={"type": "note", "subject_id": str(subject.id), "class_id": str(school_class.id), "file": (io.BytesIO(b"x"), "a.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401


def test_upload_forbidden_for_parent_and_student(parent, student):
    school_class = create_class(1)
    subject = create_subject("Maths")
    parent_authed, _ = parent
    student_authed, _ = student
    assert _upload(parent_authed, school_class, subject).status_code == 403
    assert _upload(student_authed, school_class, subject).status_code == 403


def test_upload_success_by_admin(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = _upload(admin, school_class, subject)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["type"] == "note"
    assert body["subject_name"] == "Maths"
    assert body["grade"] == 1
    assert body["filename"] == "notes.pdf"
    assert body["size"] == len(b"%PDF-1.4 fake pdf content")


def test_upload_success_by_teacher(teacher):
    authed, _ = teacher
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = _upload(authed, school_class, subject)
    assert resp.status_code == 201


def test_upload_missing_file_is_error(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = admin.post(
        "/api/resources",
        data={"type": "note", "subject_id": str(subject.id), "class_id": str(school_class.id)},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "missing_file"


def test_upload_invalid_file_type_rejected(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = _upload(admin, school_class, subject, filename="virus.exe")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_file_type"


def test_upload_empty_file_rejected(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = _upload(admin, school_class, subject, content=b"")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "empty_file"


def test_upload_missing_form_fields_validation_error(admin):
    resp = admin.post(
        "/api/resources",
        data={"file": (io.BytesIO(b"x"), "a.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_upload_invalid_type_enum_validation_error(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = _upload(admin, school_class, subject, rtype="not_a_real_type")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_upload_nonexistent_class_not_found(admin):
    subject = create_subject("Maths")

    class FakeClass:
        id = 999999

    resp = _upload(admin, FakeClass(), subject)
    assert resp.status_code == 404


def test_upload_nonexistent_subject_not_found(admin):
    school_class = create_class(1)

    class FakeSubject:
        id = 999999

    resp = _upload(admin, school_class, FakeSubject())
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/resources (list, role-scoped) and /{id}, /{id}/download
# ---------------------------------------------------------------------------


def test_list_resources_requires_authentication(client):
    assert client.get("/api/resources").status_code == 401


def test_admin_sees_all_resources(admin):
    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    _upload(admin, class_a, subject)
    _upload(admin, class_b, subject)
    resp = admin.get("/api/resources")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 2


def test_student_sees_only_own_class_resources(make_client):
    from conftest import create_admin_user

    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    admin_authed = login_as(make_client(), create_admin_user().email)
    _upload(admin_authed, class_a, subject, filename="visible.pdf")
    _upload(admin_authed, class_b, subject, filename="hidden.pdf")

    student_row = create_student(class_id=class_a.id)
    student_authed = login_as(make_client(), student_row.user.email)
    resp = student_authed.get("/api/resources")
    assert resp.status_code == 200
    filenames = [r["filename"] for r in resp.get_json()["items"]]
    assert filenames == ["visible.pdf"]


def test_parent_sees_only_childs_class_resources(make_client):
    from conftest import create_admin_user

    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    admin_user = create_admin_user()
    admin_authed = login_as(make_client(), admin_user.email)
    _upload(admin_authed, class_a, subject, filename="visible.pdf")
    _upload(admin_authed, class_b, subject, filename="hidden.pdf")

    parent_row = create_parent()
    create_student(class_id=class_a.id, parent_id=parent_row.id)
    parent_authed = login_as(make_client(), parent_row.user.email)
    resp = parent_authed.get("/api/resources")
    assert resp.status_code == 200
    filenames = [r["filename"] for r in resp.get_json()["items"]]
    assert filenames == ["visible.pdf"]


def test_teacher_sees_only_assigned_class_resources(make_client):
    from conftest import create_admin_user

    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    admin_user = create_admin_user()
    admin_authed = login_as(make_client(), admin_user.email)
    _upload(admin_authed, class_a, subject, filename="visible.pdf")
    _upload(admin_authed, class_b, subject, filename="hidden.pdf")

    teacher_row = create_teacher()
    create_assignment(class_a.id, subject.id, teacher_row.id)
    teacher_authed = login_as(make_client(), teacher_row.user.email)
    resp = teacher_authed.get("/api/resources")
    assert resp.status_code == 200
    filenames = [r["filename"] for r in resp.get_json()["items"]]
    assert filenames == ["visible.pdf"]


def test_get_resource_not_found(admin):
    resp = admin.get("/api/resources/999999")
    assert resp.status_code == 404


def test_get_resource_forbidden_for_unrelated_student(make_client):
    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    from conftest import create_admin_user

    admin_authed = login_as(make_client(), create_admin_user().email)
    resource_id = _upload(admin_authed, class_a, subject).get_json()["id"]

    student_row = create_student(class_id=class_b.id)
    student_authed = login_as(make_client(), student_row.user.email)
    resp = student_authed.get(f"/api/resources/{resource_id}")
    assert resp.status_code == 403


def test_download_returns_signed_url(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resource_id = _upload(admin, school_class, subject, filename="dl.pdf").get_json()["id"]

    resp = admin.get(f"/api/resources/{resource_id}/download")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["filename"] == "dl.pdf"
    assert body["expires_in"] == 300
    assert body["url"].startswith("https://fake-storage.test/")


def test_download_not_found(admin):
    resp = admin.get("/api/resources/999999/download")
    assert resp.status_code == 404


def test_download_forbidden_for_unrelated_teacher(make_client):
    from conftest import create_admin_user

    class_a = create_class(1)
    subject = create_subject("Maths")
    admin_authed = login_as(make_client(), create_admin_user().email)
    resource_id = _upload(admin_authed, class_a, subject).get_json()["id"]

    other_teacher = create_teacher()  # not assigned to class_a
    teacher_authed = login_as(make_client(), other_teacher.user.email)
    resp = teacher_authed.get(f"/api/resources/{resource_id}/download")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/resources/{id}
# ---------------------------------------------------------------------------


def test_delete_resource_forbidden_for_parent_and_student(parent, student):
    # role_required rejects before the route ever looks up the resource, so
    # an arbitrary id is enough to prove parent/student can't reach this route.
    parent_authed, _ = parent
    student_authed, _ = student
    assert parent_authed.delete("/api/resources/1").status_code == 403
    assert student_authed.delete("/api/resources/1").status_code == 403


def test_delete_resource_by_admin_success(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resource_id = _upload(admin, school_class, subject).get_json()["id"]
    resp = admin.delete(f"/api/resources/{resource_id}")
    assert resp.status_code == 204
    assert admin.get(f"/api/resources/{resource_id}").status_code == 404


def test_delete_resource_by_uploading_teacher_success(teacher):
    authed, _ = teacher
    school_class = create_class(1)
    subject = create_subject("Maths")
    resource_id = _upload(authed, school_class, subject).get_json()["id"]
    resp = authed.delete(f"/api/resources/{resource_id}")
    assert resp.status_code == 204


def test_delete_resource_by_non_uploading_teacher_forbidden(make_client):
    school_class = create_class(1)
    subject = create_subject("Maths")
    uploader = create_teacher()
    other_teacher = create_teacher()

    uploader_authed = login_as(make_client(), uploader.user.email)
    resource_id = _upload(uploader_authed, school_class, subject).get_json()["id"]

    other_authed = login_as(make_client(), other_teacher.user.email)
    resp = other_authed.delete(f"/api/resources/{resource_id}")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "forbidden"


def test_delete_resource_not_found(admin):
    resp = admin.delete("/api/resources/999999")
    assert resp.status_code == 404


def test_delete_resource_referenced_by_homework_is_conflict(admin, app):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resource_id = _upload(admin, school_class, subject).get_json()["id"]

    with app.app_context():
        homework = Homework(
            class_id=school_class.id,
            subject_id=subject.id,
            title="Homework referencing this resource",
            due_date=date(2026, 1, 1),
            created_by=1,
            resource_id=resource_id,
        )
        db.session.add(homework)
        db.session.commit()

    resp = admin.delete(f"/api/resources/{resource_id}")
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"
