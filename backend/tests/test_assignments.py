"""/api/assignments (class/subject -> teacher mapping), admin-only."""

from conftest import create_assignment, create_class, create_subject, create_teacher


def test_list_assignments_requires_admin(teacher):
    authed, _ = teacher
    resp = authed.get("/api/assignments")
    assert resp.status_code == 403


def test_list_assignments_requires_authentication(client):
    assert client.get("/api/assignments").status_code == 401


def test_list_assignments_success(admin):
    school_class = create_class(1)
    subject = create_subject("English")
    teacher_row = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_row.id)

    resp = admin.get("/api/assignments")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["grade"] == 1
    assert item["subject_name"] == "English"


def test_list_assignments_filter_by_class_id(admin):
    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    teacher_row = create_teacher()
    create_assignment(class_a.id, subject.id, teacher_row.id)
    subject2 = create_subject("Physics")
    create_assignment(class_b.id, subject2.id, teacher_row.id)

    resp = admin.get(f"/api/assignments?class_id={class_a.id}")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["items"][0]["class_id"] == class_a.id


def test_list_assignments_filter_by_teacher_id(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    teacher_a = create_teacher()
    teacher_b = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_a.id)

    resp = admin.get(f"/api/assignments?teacher_id={teacher_b.id}")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 0


def test_create_assignment_requires_admin(teacher):
    authed, teacher_row = teacher
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = authed.post(
        "/api/assignments", json={"class_id": school_class.id, "subject_id": subject.id, "teacher_id": teacher_row.id}
    )
    assert resp.status_code == 403


def test_create_assignment_success(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    teacher_row = create_teacher()
    resp = admin.post(
        "/api/assignments", json={"class_id": school_class.id, "subject_id": subject.id, "teacher_id": teacher_row.id}
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["class_id"] == school_class.id
    assert body["subject_id"] == subject.id
    assert body["teacher_id"] == teacher_row.id


def test_create_assignment_missing_fields_validation_error(admin):
    resp = admin.post("/api/assignments", json={})
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert set(["class_id", "subject_id", "teacher_id"]).issubset(body["message"].keys())


def test_create_assignment_nonexistent_class_not_found(admin):
    subject = create_subject("Maths")
    teacher_row = create_teacher()
    resp = admin.post(
        "/api/assignments", json={"class_id": 999999, "subject_id": subject.id, "teacher_id": teacher_row.id}
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_create_assignment_nonexistent_subject_not_found(admin):
    school_class = create_class(1)
    teacher_row = create_teacher()
    resp = admin.post(
        "/api/assignments", json={"class_id": school_class.id, "subject_id": 999999, "teacher_id": teacher_row.id}
    )
    assert resp.status_code == 404


def test_create_assignment_nonexistent_teacher_not_found(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    resp = admin.post(
        "/api/assignments", json={"class_id": school_class.id, "subject_id": subject.id, "teacher_id": 999999}
    )
    assert resp.status_code == 404


def test_create_assignment_duplicate_class_subject_conflict(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    teacher_a = create_teacher()
    teacher_b = create_teacher()
    create_assignment(school_class.id, subject.id, teacher_a.id)

    resp = admin.post(
        "/api/assignments", json={"class_id": school_class.id, "subject_id": subject.id, "teacher_id": teacher_b.id}
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"] == "conflict"


def test_delete_assignment_requires_admin(teacher):
    authed, teacher_row = teacher
    school_class = create_class(1)
    subject = create_subject("Maths")
    assignment = create_assignment(school_class.id, subject.id, teacher_row.id)
    resp = authed.delete(f"/api/assignments/{assignment.id}")
    assert resp.status_code == 403


def test_delete_assignment_success(admin):
    school_class = create_class(1)
    subject = create_subject("Maths")
    teacher_row = create_teacher()
    assignment = create_assignment(school_class.id, subject.id, teacher_row.id)
    resp = admin.delete(f"/api/assignments/{assignment.id}")
    assert resp.status_code == 204


def test_delete_assignment_not_found(admin):
    resp = admin.delete("/api/assignments/999999")
    assert resp.status_code == 404
