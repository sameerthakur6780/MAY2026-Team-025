"""/api/teachers CRUD (admin-only)."""

from app.models.academic import ClassSubjectTeacher
from app.models.user import User
from conftest import create_assignment, create_class, create_subject, create_teacher


def test_list_teachers_requires_admin(teacher):
    authed, _ = teacher
    resp = authed.get("/api/teachers")
    assert resp.status_code == 403


def test_list_teachers_requires_authentication(client):
    assert client.get("/api/teachers").status_code == 401


def test_list_teachers_success(admin):
    create_teacher(full_name="Alice Teach")
    create_teacher(full_name="Bob Teach")
    resp = admin.get("/api/teachers")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 2
    names = sorted(t["full_name"] for t in body["items"])
    assert names == ["Alice Teach", "Bob Teach"]


def test_get_teacher_not_found(admin):
    resp = admin.get("/api/teachers/999999")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_get_teacher_success(admin):
    teacher_row = create_teacher(full_name="Detail Teacher")
    resp = admin.get(f"/api/teachers/{teacher_row.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["full_name"] == "Detail Teacher"
    assert body["assigned_class_ids"] == []


def test_create_teacher_requires_admin(parent):
    authed, _ = parent
    resp = authed.post(
        "/api/teachers", json={"full_name": "X", "email": "xteach@test.com", "password": "Password123"}
    )
    assert resp.status_code == 403


def test_create_teacher_success(admin):
    resp = admin.post(
        "/api/teachers",
        json={
            "full_name": "New Teacher",
            "email": "newteach@test.com",
            "password": "Password123",
            "phone": "9876543210",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["full_name"] == "New Teacher"
    assert body["phone"] == "9876543210"
    assert body["assigned_class_ids"] == []


def test_create_teacher_missing_fields_validation_error(admin):
    resp = admin.post("/api/teachers", json={"email": "onlyemail@test.com"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "full_name" in body["message"]
    assert "password" in body["message"]
    assert "phone" in body["message"]


def test_create_teacher_invalid_phone_format_validation_error(admin):
    resp = admin.post(
        "/api/teachers",
        json={"full_name": "Bad Phone", "email": "badphoneteach@test.com", "password": "Password123", "phone": "5551234567"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "phone" in body["message"]


def test_create_teacher_duplicate_email_conflict(admin):
    create_teacher(email="dupteach@test.com")
    resp = admin.post(
        "/api/teachers",
        json={"full_name": "Dup", "email": "dupteach@test.com", "password": "Password123", "phone": "9876543211"},
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "email_taken"


def test_update_teacher_requires_admin(teacher):
    authed, teacher_row = teacher
    resp = authed.patch(f"/api/teachers/{teacher_row.id}", json={})
    assert resp.status_code == 403


def test_update_teacher_empty_body_is_a_no_op(admin):
    teacher_row = create_teacher(full_name="No Op Teacher")
    resp = admin.patch(f"/api/teachers/{teacher_row.id}", json={})
    assert resp.status_code == 200
    assert resp.get_json()["full_name"] == "No Op Teacher"


def test_update_teacher_full_name_and_phone(admin):
    teacher_row = create_teacher(full_name="Original Name", phone="9876543210")
    resp = admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"full_name": "Updated Name", "phone": "9876543211"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["full_name"] == "Updated Name"
    assert body["phone"] == "9876543211"


def test_update_teacher_email_success(admin):
    teacher_row = create_teacher(email="oldteach@test.com")
    resp = admin.patch(f"/api/teachers/{teacher_row.id}", json={"email": "newteach@test.com"})
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "newteach@test.com"


def test_update_teacher_duplicate_email_conflict(admin):
    create_teacher(email="taken@test.com")
    teacher_row = create_teacher(email="other@test.com")
    resp = admin.patch(f"/api/teachers/{teacher_row.id}", json={"email": "taken@test.com"})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "email_taken"


def test_update_teacher_assign_classes_for_subject(admin):
    teacher_row = create_teacher()
    school_class_a = create_class(5)
    school_class_b = create_class(6)
    subject = create_subject("Physics")

    resp = admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"subject_id": subject.id, "class_ids": [school_class_a.id, school_class_b.id]},
    )
    assert resp.status_code == 200
    assert set(resp.get_json()["assigned_class_ids"]) == {school_class_a.id, school_class_b.id}


def test_update_teacher_reassign_removes_old_classes_for_subject(admin, app):
    teacher_row = create_teacher()
    school_class_a = create_class(7)
    school_class_b = create_class(8)
    subject = create_subject("Chemistry")

    admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"subject_id": subject.id, "class_ids": [school_class_a.id, school_class_b.id]},
    )
    resp = admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"subject_id": subject.id, "class_ids": [school_class_a.id]},
    )
    assert resp.status_code == 200
    assert resp.get_json()["assigned_class_ids"] == [school_class_a.id]

    with app.app_context():
        rows = ClassSubjectTeacher.query.filter_by(teacher_id=teacher_row.id, subject_id=subject.id).all()
        assert {row.class_id for row in rows} == {school_class_a.id}


def test_update_teacher_class_subject_conflict(admin):
    teacher_row = create_teacher()
    other_teacher = create_teacher(email="otherteach@test.com")
    school_class = create_class(9)
    subject = create_subject("Biology")
    create_assignment(school_class.id, subject.id, other_teacher.id)

    resp = admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"subject_id": subject.id, "class_ids": [school_class.id]},
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


def test_update_teacher_bad_subject_not_found(admin):
    teacher_row = create_teacher()
    school_class = create_class(10)
    resp = admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"subject_id": 999999, "class_ids": [school_class.id]},
    )
    assert resp.status_code == 404


def test_update_teacher_bad_class_not_found(admin):
    teacher_row = create_teacher()
    subject = create_subject("History")
    resp = admin.patch(
        f"/api/teachers/{teacher_row.id}",
        json={"subject_id": subject.id, "class_ids": [999999]},
    )
    assert resp.status_code == 404


def test_update_teacher_subject_without_class_ids_rejected(admin):
    teacher_row = create_teacher()
    subject = create_subject("Geography")
    resp = admin.patch(f"/api/teachers/{teacher_row.id}", json={"subject_id": subject.id})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_request"


def test_update_teacher_not_found(admin):
    resp = admin.patch("/api/teachers/999999", json={})
    assert resp.status_code == 404


def test_delete_teacher_requires_admin(teacher):
    authed, teacher_row = teacher
    resp = authed.delete(f"/api/teachers/{teacher_row.id}")
    assert resp.status_code == 403


def test_delete_teacher_not_found(admin):
    resp = admin.delete("/api/teachers/999999")
    assert resp.status_code == 404


def test_delete_teacher_cascades_to_user_row(admin, app):
    teacher_row = create_teacher()
    teacher_id = teacher_row.id
    user_id = teacher_row.user_id

    resp = admin.delete(f"/api/teachers/{teacher_id}")
    assert resp.status_code == 204

    with app.app_context():
        assert User.query.get(user_id) is None

    assert admin.get(f"/api/teachers/{teacher_id}").status_code == 404
