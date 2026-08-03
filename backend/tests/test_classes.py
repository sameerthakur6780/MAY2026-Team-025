"""/api/classes CRUD, role-scoped."""

from conftest import (
    create_assignment,
    create_class,
    create_parent,
    create_student,
    create_subject,
    create_teacher,
    login_as,
)


def test_list_classes_requires_authentication(client):
    assert client.get("/api/classes").status_code == 401


def test_admin_sees_all_classes(admin):
    create_class(1)
    create_class(2)
    resp = admin.get("/api/classes")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 2


def test_teacher_sees_only_assigned_classes(make_client):
    class_a = create_class(1)
    create_class(2)
    subject = create_subject("Science")
    teacher_row = create_teacher()
    create_assignment(class_a.id, subject.id, teacher_row.id)

    authed = login_as(make_client(), teacher_row.user.email)
    resp = authed.get("/api/classes")
    assert resp.status_code == 200
    grades = [c["grade"] for c in resp.get_json()["items"]]
    assert grades == [1]


def test_parent_sees_only_childrens_classes(make_client):
    class_a = create_class(1)
    create_class(2)
    parent_row = create_parent()
    create_student(class_id=class_a.id, parent_id=parent_row.id)

    authed = login_as(make_client(), parent_row.user.email)
    resp = authed.get("/api/classes")
    assert resp.status_code == 200
    grades = [c["grade"] for c in resp.get_json()["items"]]
    assert grades == [1]


def test_get_class_not_found(admin):
    resp = admin.get("/api/classes/999999")
    assert resp.status_code == 404


def test_get_class_forbidden_for_unrelated_teacher(make_client):
    class_a = create_class(7)
    teacher_row = create_teacher()  # no assignment to class_a
    authed = login_as(make_client(), teacher_row.user.email)
    resp = authed.get(f"/api/classes/{class_a.id}")
    assert resp.status_code == 403


def test_get_class_includes_student_count(admin):
    class_a = create_class(8)
    create_student(class_id=class_a.id)
    create_student(class_id=class_a.id)
    resp = admin.get(f"/api/classes/{class_a.id}")
    assert resp.status_code == 200
    assert resp.get_json()["student_count"] == 2


def test_create_class_requires_admin(teacher):
    authed, _ = teacher
    resp = authed.post("/api/classes", json={"grade": 9})
    assert resp.status_code == 403


def test_create_class_success(admin):
    resp = admin.post("/api/classes", json={"grade": 9})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["grade"] == 9
    assert body["student_count"] == 0


def test_create_class_grade_out_of_range_validation_error(admin):
    resp = admin.post("/api/classes", json={"grade": 13})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"

    resp = admin.post("/api/classes", json={"grade": 0})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_create_class_missing_grade_validation_error(admin):
    resp = admin.post("/api/classes", json={})
    assert resp.status_code == 400
    assert "grade" in resp.get_json()["message"]


def test_create_class_duplicate_grade_conflict(admin):
    create_class(10)
    resp = admin.post("/api/classes", json={"grade": 10})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


def test_update_class_requires_admin(teacher):
    authed, _ = teacher
    class_a = create_class(11)
    resp = authed.patch(f"/api/classes/{class_a.id}", json={"grade": 12})
    assert resp.status_code == 403


def test_update_class_success(admin):
    class_a = create_class(1)
    resp = admin.patch(f"/api/classes/{class_a.id}", json={"grade": 2})
    assert resp.status_code == 200
    assert resp.get_json()["grade"] == 2


def test_update_class_duplicate_grade_conflict(admin):
    create_class(3)
    class_b = create_class(4)
    resp = admin.patch(f"/api/classes/{class_b.id}", json={"grade": 3})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


def test_update_class_not_found(admin):
    resp = admin.patch("/api/classes/999999", json={"grade": 5})
    assert resp.status_code == 404


def test_delete_class_requires_admin(teacher):
    authed, _ = teacher
    class_a = create_class(1)
    resp = authed.delete(f"/api/classes/{class_a.id}")
    assert resp.status_code == 403


def test_delete_class_success(admin):
    class_a = create_class(1)
    resp = admin.delete(f"/api/classes/{class_a.id}")
    assert resp.status_code == 204
    assert admin.get(f"/api/classes/{class_a.id}").status_code == 404


def test_delete_class_not_found(admin):
    resp = admin.delete("/api/classes/999999")
    assert resp.status_code == 404


def test_delete_class_with_students_is_conflict(admin):
    class_a = create_class(1)
    create_student(class_id=class_a.id)
    resp = admin.delete(f"/api/classes/{class_a.id}")
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"
