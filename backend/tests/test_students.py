"""/api/students CRUD, role-scoped."""

from app.models.user import User
from conftest import (
    create_admin_user,
    create_assignment,
    create_class,
    create_parent,
    create_student,
    create_subject,
    create_teacher,
    login_as,
)


# ---------------------------------------------------------------------------
# GET /api/students (list, role-scoped)
# ---------------------------------------------------------------------------


def test_list_students_requires_authentication(client):
    assert client.get("/api/students").status_code == 401


def test_list_students_forbidden_for_student_role(student):
    authed, _ = student
    resp = authed.get("/api/students")
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "forbidden"


def test_admin_sees_all_students(admin):
    create_student()
    create_student()
    resp = admin.get("/api/students")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 2
    assert {"items", "page", "per_page", "total", "pages"} == set(body.keys())


def test_teacher_sees_only_students_in_assigned_classes(make_client):
    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    teacher_row = create_teacher()
    create_assignment(class_a.id, subject.id, teacher_row.id)

    in_class_a = create_student(class_id=class_a.id)
    create_student(class_id=class_b.id)  # not visible

    authed = login_as(make_client(), teacher_row.user.email)
    resp = authed.get("/api/students")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.get_json()["items"]]
    assert ids == [in_class_a.id]


def test_teacher_with_no_assignments_sees_no_students(make_client):
    create_student()
    teacher_row = create_teacher()
    authed = login_as(make_client(), teacher_row.user.email)
    resp = authed.get("/api/students")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_parent_sees_only_their_own_children(make_client):
    parent_row = create_parent()
    other_parent = create_parent()
    own_child = create_student(parent_id=parent_row.id)
    create_student(parent_id=other_parent.id)

    authed = login_as(make_client(), parent_row.user.email)
    resp = authed.get("/api/students")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.get_json()["items"]]
    assert ids == [own_child.id]


def test_list_students_filter_by_class_id(admin):
    class_a = create_class(3)
    class_b = create_class(4)
    in_a = create_student(class_id=class_a.id)
    create_student(class_id=class_b.id)

    resp = admin.get(f"/api/students?class_id={class_a.id}")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.get_json()["items"]]
    assert ids == [in_a.id]


def test_list_students_filter_by_grade(admin):
    class_a = create_class(5)
    in_a = create_student(class_id=class_a.id)
    resp = admin.get("/api/students?grade=5")
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.get_json()["items"]]
    assert ids == [in_a.id]


def test_list_students_bad_class_id_is_validation_error(admin):
    resp = admin.get("/api/students?class_id=not-a-number")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


# ---------------------------------------------------------------------------
# GET /api/students/{id} (scoped detail)
# ---------------------------------------------------------------------------


def test_get_student_not_found(admin):
    resp = admin.get("/api/students/999999")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_get_student_forbidden_for_unrelated_parent(make_client):
    other_parent = create_parent()
    someone_elses_child = create_student(parent_id=other_parent.id)
    my_parent = create_parent()

    authed = login_as(make_client(), my_parent.user.email)
    resp = authed.get(f"/api/students/{someone_elses_child.id}")
    assert resp.status_code == 403


def test_get_student_success_for_admin(admin):
    student_row = create_student(full_name="Detail Student")
    resp = admin.get(f"/api/students/{student_row.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["full_name"] == "Detail Student"
    assert body["has_face_embedding"] is False
    assert body["status"] == "active"


# ---------------------------------------------------------------------------
# POST /api/students
# ---------------------------------------------------------------------------


def test_create_student_requires_admin(teacher):
    authed, _ = teacher
    resp = authed.post(
        "/api/students",
        json={"full_name": "X", "email": "x@test.com", "password": "Password123", "admission_no": "A1"},
    )
    assert resp.status_code == 403


def test_create_student_success(admin):
    school_class = create_class(6)
    resp = admin.post(
        "/api/students",
        json={
            "full_name": "Brand New Student",
            "email": "bns@test.com",
            "password": "Password123",
            "phone": "9876543210",
            "admission_no": "ADM-500",
            "class_id": school_class.id,
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["admission_no"] == "ADM-500"
    assert body["grade"] == 6
    assert body["status"] == "active"


def test_create_student_missing_admission_no_validation_error(admin):
    resp = admin.post(
        "/api/students", json={"full_name": "No Adm", "email": "noadm2@test.com", "password": "Password123"}
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_create_student_duplicate_email_conflict(admin):
    create_student(email="taken@test.com")
    resp = admin.post(
        "/api/students",
        json={
            "full_name": "Dup",
            "email": "taken@test.com",
            "password": "Password123",
            "phone": "9876543211",
            "admission_no": "ADM-9",
        },
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "email_taken"


def test_create_student_duplicate_admission_no_conflict(admin):
    create_student(admission_no="DUPADM")
    resp = admin.post(
        "/api/students",
        json={
            "full_name": "Dup Admission",
            "email": "dupadm@test.com",
            "password": "Password123",
            "phone": "9876543212",
            "admission_no": "DUPADM",
        },
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


# ---------------------------------------------------------------------------
# PATCH /api/students/{id}
# ---------------------------------------------------------------------------


def test_update_student_requires_admin(teacher):
    authed, teacher_row = teacher
    student_row = create_student()
    resp = authed.patch(f"/api/students/{student_row.id}", json={"status": "inactive"})
    assert resp.status_code == 403


def test_update_student_success(admin):
    student_row = create_student()
    resp = admin.patch(f"/api/students/{student_row.id}", json={"status": "inactive", "gender": "female"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "inactive"
    assert body["gender"] == "female"


def test_update_student_invalid_status_validation_error(admin):
    student_row = create_student()
    resp = admin.patch(f"/api/students/{student_row.id}", json={"status": "graduated"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_update_student_not_found(admin):
    resp = admin.patch("/api/students/999999", json={"status": "inactive"})
    assert resp.status_code == 404


def test_update_student_duplicate_admission_no_conflict(admin):
    create_student(admission_no="EXIST-1")
    victim = create_student(admission_no="EXIST-2")
    resp = admin.patch(f"/api/students/{victim.id}", json={"admission_no": "EXIST-1"})
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


# ---------------------------------------------------------------------------
# DELETE /api/students/{id}
# ---------------------------------------------------------------------------


def test_delete_student_requires_admin(teacher):
    authed, _ = teacher
    student_row = create_student()
    resp = authed.delete(f"/api/students/{student_row.id}")
    assert resp.status_code == 403


def test_delete_student_not_found(admin):
    resp = admin.delete("/api/students/999999")
    assert resp.status_code == 404


def test_delete_student_cascades_to_user_row(admin, app):
    student_row = create_student()
    student_id = student_row.id
    user_id = student_row.user_id

    resp = admin.delete(f"/api/students/{student_id}")
    assert resp.status_code == 204
    assert resp.data == b""

    with app.app_context():
        assert User.query.get(user_id) is None

    assert admin.get(f"/api/students/{student_id}").status_code == 404
