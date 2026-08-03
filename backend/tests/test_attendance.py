"""/api/attendance list (role-scoped), bulk marking, single-record correction."""

from conftest import create_assignment, create_class, create_parent, create_student, create_subject, create_teacher, login_as


def _mark(authed, school_class, entries, date="2026-01-15", method=None):
    payload = {"class_id": school_class.id, "date": date, "entries": entries}
    if method is not None:
        payload["method"] = method
    return authed.post("/api/attendance/bulk", json=payload)


# ---------------------------------------------------------------------------
# POST /api/attendance/bulk
# ---------------------------------------------------------------------------


def test_bulk_mark_requires_authentication(client):
    resp = client.post("/api/attendance/bulk", json={"class_id": 1, "date": "2026-01-01", "entries": []})
    assert resp.status_code == 401


def test_bulk_mark_forbidden_for_parent_and_student(parent, student):
    parent_authed, _ = parent
    student_authed, _ = student
    payload = {"class_id": 1, "date": "2026-01-01", "entries": [{"student_id": 1, "status": "present"}]}
    assert parent_authed.post("/api/attendance/bulk", json=payload).status_code == 403
    assert student_authed.post("/api/attendance/bulk", json=payload).status_code == 403


def test_bulk_mark_success_by_admin(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    s2 = create_student(class_id=school_class.id)

    resp = _mark(admin, school_class, [{"student_id": s1.id, "status": "present"}, {"student_id": s2.id, "status": "absent"}])
    assert resp.status_code == 201
    body = resp.get_json()
    assert len(body["created"]) == 2
    assert body["skipped_student_ids"] == []
    statuses = {r["student_id"]: r["status"] for r in body["created"]}
    assert statuses == {s1.id: "present", s2.id: "absent"}
    assert all(r["method"] == "manual" for r in body["created"])


def test_bulk_mark_success_by_teacher(teacher):
    authed, teacher_row = teacher
    school_class = create_class(1)
    subject = create_subject("Maths")
    create_assignment(school_class.id, subject.id, teacher_row.id)
    s1 = create_student(class_id=school_class.id)

    resp = _mark(authed, school_class, [{"student_id": s1.id, "status": "late"}])
    assert resp.status_code == 201
    assert resp.get_json()["created"][0]["status"] == "late"


def test_bulk_mark_skips_already_marked_students_instead_of_rejecting(admin):
    """Deliberate design: re-marking an already-recorded student/date pair
    is skipped, not rejected, so manual marking can coexist with a future
    facial-recognition auto-marking pass for the same class/date."""
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    s2 = create_student(class_id=school_class.id)

    first = _mark(admin, school_class, [{"student_id": s1.id, "status": "present"}])
    assert first.status_code == 201
    assert len(first.get_json()["created"]) == 1

    second = _mark(admin, school_class, [
        {"student_id": s1.id, "status": "absent"},  # already marked -> skipped
        {"student_id": s2.id, "status": "present"},  # new -> created
    ])
    assert second.status_code == 201
    body = second.get_json()
    assert [r["student_id"] for r in body["created"]] == [s2.id]
    assert body["skipped_student_ids"] == [s1.id]


def test_bulk_mark_duplicate_student_id_in_entries_is_validation_error(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    resp = _mark(admin, school_class, [
        {"student_id": s1.id, "status": "present"},
        {"student_id": s1.id, "status": "absent"},
    ])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_bulk_mark_empty_entries_is_validation_error(admin):
    school_class = create_class(1)
    resp = _mark(admin, school_class, [])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_bulk_mark_invalid_status_is_validation_error(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    resp = _mark(admin, school_class, [{"student_id": s1.id, "status": "on_vacation"}])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_bulk_mark_nonexistent_class_not_found(admin):
    class Fake:
        id = 999999

    resp = _mark(admin, Fake(), [{"student_id": 1, "status": "present"}])
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_bulk_mark_unknown_student_id_not_found(admin):
    school_class = create_class(1)
    resp = _mark(admin, school_class, [{"student_id": 999999, "status": "present"}])
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not_found"


def test_bulk_mark_student_not_enrolled_in_class_is_bad_request(admin):
    class_a = create_class(1)
    class_b = create_class(2)
    outside_student = create_student(class_id=class_b.id)

    resp = _mark(admin, class_a, [{"student_id": outside_student.id, "status": "present"}])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "invalid_student_class"


# ---------------------------------------------------------------------------
# GET /api/attendance (list, role-scoped)
# ---------------------------------------------------------------------------


def test_list_attendance_requires_authentication(client):
    assert client.get("/api/attendance").status_code == 401


def test_admin_sees_all_attendance(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    _mark(admin, school_class, [{"student_id": s1.id, "status": "present"}])
    resp = admin.get("/api/attendance")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 1


def test_teacher_sees_only_assigned_class_attendance(make_client):
    from conftest import create_admin_user

    class_a = create_class(1)
    class_b = create_class(2)
    subject = create_subject("Maths")
    admin_authed = login_as(make_client(), create_admin_user().email)

    s_in_a = create_student(class_id=class_a.id)
    s_in_b = create_student(class_id=class_b.id)
    _mark(admin_authed, class_a, [{"student_id": s_in_a.id, "status": "present"}])
    _mark(admin_authed, class_b, [{"student_id": s_in_b.id, "status": "present"}])

    teacher_row = create_teacher()
    create_assignment(class_a.id, subject.id, teacher_row.id)
    teacher_authed = login_as(make_client(), teacher_row.user.email)

    resp = teacher_authed.get("/api/attendance")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["items"][0]["student_id"] == s_in_a.id


def test_parent_sees_only_their_childs_attendance_by_identity_not_class(make_client):
    """Parent/student scoping is by identity, not class_id -- a parent must
    never see a classmate's record even for the same class."""
    from conftest import create_admin_user

    school_class = create_class(1)
    admin_authed = login_as(make_client(), create_admin_user().email)

    parent_row = create_parent()
    my_child = create_student(class_id=school_class.id, parent_id=parent_row.id)
    classmate = create_student(class_id=school_class.id)
    _mark(admin_authed, school_class, [
        {"student_id": my_child.id, "status": "present"},
        {"student_id": classmate.id, "status": "absent"},
    ])

    parent_authed = login_as(make_client(), parent_row.user.email)
    resp = parent_authed.get("/api/attendance")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["items"][0]["student_id"] == my_child.id


def test_student_sees_only_their_own_attendance(make_client):
    from conftest import create_admin_user

    school_class = create_class(1)
    admin_authed = login_as(make_client(), create_admin_user().email)

    me = create_student(class_id=school_class.id)
    classmate = create_student(class_id=school_class.id)
    _mark(admin_authed, school_class, [
        {"student_id": me.id, "status": "present"},
        {"student_id": classmate.id, "status": "present"},
    ])

    student_authed = login_as(make_client(), me.user.email)
    resp = student_authed.get("/api/attendance")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 1
    assert body["items"][0]["student_id"] == me.id


def test_list_attendance_bad_date_is_validation_error(admin):
    resp = admin.get("/api/attendance?date_from=not-a-date")
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_list_attendance_filters_by_date_range(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    _mark(admin, school_class, [{"student_id": s1.id, "status": "present"}], date="2026-01-01")

    resp = admin.get("/api/attendance?date_from=2026-02-01")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 0

    resp = admin.get("/api/attendance?date_from=2026-01-01&date_to=2026-01-31")
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 1


# ---------------------------------------------------------------------------
# PATCH /api/attendance/{id}
# ---------------------------------------------------------------------------


def test_update_attendance_requires_admin_or_teacher(parent):
    authed, _ = parent
    resp = authed.patch("/api/attendance/1", json={"status": "present"})
    assert resp.status_code == 403


def test_update_attendance_success(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    record_id = _mark(admin, school_class, [{"student_id": s1.id, "status": "absent"}]).get_json()["created"][0]["id"]

    resp = admin.patch(f"/api/attendance/{record_id}", json={"status": "present"})
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "present"


def test_update_attendance_invalid_status_validation_error(admin):
    school_class = create_class(1)
    s1 = create_student(class_id=school_class.id)
    record_id = _mark(admin, school_class, [{"student_id": s1.id, "status": "absent"}]).get_json()["created"][0]["id"]

    resp = admin.patch(f"/api/attendance/{record_id}", json={"status": "sleeping"})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_update_attendance_not_found(admin):
    resp = admin.patch("/api/attendance/999999", json={"status": "present"})
    assert resp.status_code == 404
