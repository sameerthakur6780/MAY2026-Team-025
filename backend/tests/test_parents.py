"""/api/parents CRUD (admin-only)."""

from app.models.user import User
from conftest import create_parent, create_student


def test_list_parents_requires_admin(parent):
    authed, _ = parent
    resp = authed.get("/api/parents")
    assert resp.status_code == 403


def test_list_parents_requires_authentication(client):
    assert client.get("/api/parents").status_code == 401


def test_list_parents_success(admin):
    create_parent(full_name="Parent One")
    create_parent(full_name="Parent Two")
    resp = admin.get("/api/parents")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 2


def test_get_parent_not_found(admin):
    resp = admin.get("/api/parents/999999")
    assert resp.status_code == 404


def test_get_parent_success_includes_student_ids(admin):
    parent_row = create_parent(full_name="Detail Parent")
    child = create_student(parent_id=parent_row.id)
    resp = admin.get(f"/api/parents/{parent_row.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["full_name"] == "Detail Parent"
    assert body["student_ids"] == [child.id]


def test_create_parent_requires_admin(teacher):
    authed, _ = teacher
    resp = authed.post(
        "/api/parents", json={"full_name": "X", "email": "xparent@test.com", "password": "Password123"}
    )
    assert resp.status_code == 403


def test_create_parent_success(admin):
    resp = admin.post(
        "/api/parents",
        json={
            "full_name": "New Parent",
            "email": "newparent2@test.com",
            "password": "Password123",
            "phone": "9876543210",
            "occupation": "Doctor",
            "address": "123 Main St",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["occupation"] == "Doctor"
    assert body["student_ids"] == []


def test_create_parent_missing_fields_validation_error(admin):
    resp = admin.post("/api/parents", json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert set(["full_name", "email", "password"]).issubset(body["message"].keys())


def test_create_parent_duplicate_email_conflict(admin):
    create_parent(email="dupparent@test.com")
    resp = admin.post(
        "/api/parents",
        json={
            "full_name": "Dup",
            "email": "dupparent@test.com",
            "password": "Password123",
            "phone": "9876543211",
        },
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "email_taken"


def test_update_parent_requires_admin(parent):
    authed, parent_row = parent
    resp = authed.patch(f"/api/parents/{parent_row.id}", json={"occupation": "Hacker"})
    assert resp.status_code == 403


def test_update_parent_success(admin):
    parent_row = create_parent()
    resp = admin.patch(f"/api/parents/{parent_row.id}", json={"occupation": "Pilot", "address": "New Address"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["occupation"] == "Pilot"
    assert body["address"] == "New Address"


def test_update_parent_not_found(admin):
    resp = admin.patch("/api/parents/999999", json={"occupation": "X"})
    assert resp.status_code == 404


def test_delete_parent_requires_admin(parent):
    authed, parent_row = parent
    resp = authed.delete(f"/api/parents/{parent_row.id}")
    assert resp.status_code == 403


def test_delete_parent_not_found(admin):
    resp = admin.delete("/api/parents/999999")
    assert resp.status_code == 404


def test_delete_parent_with_linked_student_is_conflict(admin):
    parent_row = create_parent()
    create_student(parent_id=parent_row.id)
    resp = admin.delete(f"/api/parents/{parent_row.id}")
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


def test_delete_parent_cascades_to_user_row(admin, app):
    parent_row = create_parent()
    parent_id = parent_row.id
    user_id = parent_row.user_id

    resp = admin.delete(f"/api/parents/{parent_id}")
    assert resp.status_code == 204

    with app.app_context():
        assert User.query.get(user_id) is None

    assert admin.get(f"/api/parents/{parent_id}").status_code == 404
