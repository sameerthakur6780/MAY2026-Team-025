"""/api/teachers CRUD (admin-only)."""

from app.models.user import User
from conftest import create_teacher


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
        json={"full_name": "New Teacher", "email": "newteach@test.com", "password": "Password123", "phone": "12345"},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["full_name"] == "New Teacher"
    assert body["phone"] == "12345"
    assert body["assigned_class_ids"] == []


def test_create_teacher_missing_fields_validation_error(admin):
    resp = admin.post("/api/teachers", json={"email": "onlyemail@test.com"})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert "full_name" in body["message"]
    assert "password" in body["message"]


def test_create_teacher_duplicate_email_conflict(admin):
    create_teacher(email="dupteach@test.com")
    resp = admin.post(
        "/api/teachers",
        json={"full_name": "Dup", "email": "dupteach@test.com", "password": "Password123"},
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


def test_update_teacher_any_field_is_rejected(admin):
    """The teachers table has no editable fields -- sending anything at all
    must fail schema validation rather than silently doing nothing."""
    teacher_row = create_teacher()
    resp = admin.patch(f"/api/teachers/{teacher_row.id}", json={"full_name": "Should Not Work"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


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
