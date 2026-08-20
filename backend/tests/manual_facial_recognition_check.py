"""Real end-to-end verification of the facial-recognition attendance flow,
using real photos and the real DeepFace/OpenCV pipeline -- nothing about
face detection, embedding, or matching is mocked here. The only thing
substituted is Supabase Storage (same FakeStorageService the pytest suite
uses everywhere), since profile-photo storage is orthogonal to what this
script is verifying.

Not part of the pytest suite on purpose (no `test_` prefix) -- it downloads/
uses real ML models and real photos and is meant to be run deliberately,
not on every `pytest` invocation. Run directly:

    venv/Scripts/python.exe tests/manual_facial_recognition_check.py

Requires the real photos in tests/fixtures/: person1.jpg, person2.jpg,
person3.jpg (the three enrolled students), person4.jpg (a 4th person NOT
in the group photo, for false-positive testing), group.png (all three
students together).
"""
import io
import json
import sys
from datetime import timedelta
from http.cookies import SimpleCookie
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import create_app  # noqa: E402
import app.services.resource_service as resource_service  # noqa: E402
import app.services.student_service as student_service  # noqa: E402
from app.extensions import bcrypt  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.user import RoleEnum, User  # noqa: E402
from app.models.attendance import Attendance, AttendanceMethod  # noqa: E402
from app.services.facial_recognition import detect_faces, match_embedding  # noqa: E402
from app.services.facial_recognition.engine import _cosine_similarity  # noqa: E402

PASSWORD = "Password123"


class VerifyConfig:
    TESTING = True
    DEBUG = False  # see the comment on tests/conftest.py's TestConfig.DEBUG
    SECRET_KEY = "verify-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FRONTEND_ORIGINS = ["http://localhost:5173"]
    RATELIMIT_STORAGE_URI = "memory://"

    JWT_SECRET_KEY = "verify-jwt-secret-at-least-32-bytes-long"
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Lax"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_REFRESH_COOKIE_PATH = "/api/auth/refresh"

    SUPABASE_URL = "http://fake.invalid"
    SUPABASE_SERVICE_ROLE_KEY = "fake-key"
    SUPABASE_BUCKET_NAME = "fake-bucket"

    MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx", "txt"}
    RESOURCE_SIGNED_URL_EXPIRY_SECONDS = 300
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_BYTES + 1024 * 1024

    FACE_IMAGE_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    FACE_MODEL_NAME = "VGG-Face"
    FACE_DETECTOR_BACKEND = "opencv"
    FACE_HIGH_CONFIDENCE_THRESHOLD = 0.60
    FACE_LOW_CONFIDENCE_THRESHOLD = 0.40

    MAIL_DEFAULT_SENDER = "SmartBatch <no-reply@smartbatch.test>"
    MAIL_SUPPRESS_SEND = True
    SCHEDULER_ENABLED = False


class FakeStorageService:
    def __init__(self):
        self.store = {}

    def upload(self, path, file_bytes, content_type):
        self.store[path] = file_bytes
        return path

    def get_signed_url(self, path, expires_in):
        return f"https://fake-storage.test/{path}?expires_in={expires_in}"

    def delete(self, path):
        self.store.pop(path, None)


def extract_cookie(resp, name):
    for header in resp.headers.getlist("Set-Cookie"):
        c = SimpleCookie()
        c.load(header)
        if name in c:
            return c[name].value
    return None


def main():
    print("=" * 78)
    print("REAL end-to-end facial recognition verification (no mocked face logic)")
    print("=" * 78)

    app = create_app(VerifyConfig)
    with app.app_context():
        _db.create_all()

        fake_storage = FakeStorageService()
        resource_service.get_storage_service = lambda: fake_storage
        student_service.get_storage_service = lambda: fake_storage

        client = app.test_client()

        # --- admin + class setup (direct DB, same as conftest helpers) ---
        admin = User(
            full_name="Verify Admin",
            email="verifyadmin@test.com",
            password_hash=bcrypt.generate_password_hash(PASSWORD).decode("utf-8"),
            phone="9876500000",
            role=RoleEnum.ADMIN,
        )
        _db.session.add(admin)
        _db.session.commit()

        login_resp = client.post("/api/auth/login", json={"email": admin.email, "password": PASSWORD})
        assert login_resp.status_code == 200, login_resp.get_json()
        csrf = extract_cookie(login_resp, "csrf_access_token")

        def authed_post(path, **kwargs):
            headers = kwargs.pop("headers", {})
            headers["X-CSRF-TOKEN"] = csrf
            return client.post(path, headers=headers, **kwargs)

        class_resp = authed_post("/api/classes", json={"grade": 7})
        assert class_resp.status_code == 201, class_resp.get_json()
        class_id = class_resp.get_json()["id"]
        print(f"\n[setup] created class id={class_id} grade=7")

        # --- step 1: create 3 students, upload real profile photos ---
        print("\n" + "-" * 78)
        print("STEP 1: create 3 students, upload real profile photos via "
              "POST /api/students/<id>/profile-image")
        print("-" * 78)

        students = {}
        for n, photo in [(1, "person1.jpg"), (2, "person2.jpg"), (3, "person3.jpg")]:
            create_resp = authed_post(
                "/api/students",
                json={
                    "full_name": f"Verify Student {n}",
                    "email": f"verifystudent{n}@test.com",
                    "password": PASSWORD,
                    "phone": f"987650000{n}",
                    "admission_no": f"VERIFY-{n}",
                    "class_id": class_id,
                },
            )
            assert create_resp.status_code == 201, create_resp.get_json()
            student_id = create_resp.get_json()["id"]

            photo_bytes = (FIXTURES / photo).read_bytes()
            upload_resp = authed_post(
                f"/api/students/{student_id}/profile-image",
                data={"file": (io.BytesIO(photo_bytes), photo)},
                content_type="multipart/form-data",
            )
            assert upload_resp.status_code == 200, upload_resp.get_json()
            body = upload_resp.get_json()
            assert body["has_face_embedding"] is True, f"embedding not stored for student {n}"

            row = Student.query.get(student_id)
            embedding_len = len(row.face_embedding) if row.face_embedding else 0
            print(f"  student {n} ({photo}): id={student_id}, has_face_embedding=True, "
                  f"real embedding stored, dims={embedding_len}")
            students[n] = student_id

        # --- step 2: real group photo through POST /api/attendance/facial ---
        print("\n" + "-" * 78)
        print("STEP 2: group.png through POST /api/attendance/facial")
        print("-" * 78)

        group_bytes = (FIXTURES / "group.png").read_bytes()
        facial_resp = authed_post(
            "/api/attendance/facial",
            data={"class_id": str(class_id), "date": "2026-08-14", "image": (io.BytesIO(group_bytes), "group.png")},
            content_type="multipart/form-data",
        )
        assert facial_resp.status_code == 200, facial_resp.get_json()
        facial_body = facial_resp.get_json()
        print("  raw response:")
        print(" ", json.dumps(facial_body, indent=2).replace("\n", "\n  "))

        # Also compute the raw cosine similarity directly against the engine
        # (not just what the route surfaces) so we have the true number for
        # every face x every candidate, independent of the threshold logic.
        candidate_pairs = [(sid, Student.query.get(sid).face_embedding) for sid in students.values()]
        faces = detect_faces(group_bytes)
        print(f"\n  detect_faces(group.png) found {len(faces)} face(s). Raw similarity matrix:")
        group_scores = {}
        for i, face in enumerate(faces):
            row_scores = {}
            for sid, emb in candidate_pairs:
                row_scores[sid] = round(_cosine_similarity(face["embedding"], emb), 4)
            best_sid, best_conf = match_embedding(face["embedding"], candidate_pairs)
            print(f"    face[{i}]: vs students {row_scores}  -> best={best_sid} conf={round(best_conf, 4)}")
            group_scores[i] = (best_sid, best_conf)

        # --- step 3: person4 (not in the group photo) ---
        print("\n" + "-" * 78)
        print("STEP 3a: person4.jpg ALONE through POST /api/attendance/facial")
        print("-" * 78)

        person4_bytes = (FIXTURES / "person4.jpg").read_bytes()
        p4_resp = authed_post(
            "/api/attendance/facial",
            data={"class_id": str(class_id), "date": "2026-08-15", "image": (io.BytesIO(person4_bytes), "person4.jpg")},
            content_type="multipart/form-data",
        )
        assert p4_resp.status_code == 200, p4_resp.get_json()
        p4_body = p4_resp.get_json()
        print("  raw response:")
        print(" ", json.dumps(p4_body, indent=2).replace("\n", "\n  "))

        p4_faces = detect_faces(person4_bytes)
        assert len(p4_faces) == 1, f"expected 1 face in person4.jpg, got {len(p4_faces)}"
        p4_best_sid, p4_best_conf = match_embedding(p4_faces[0]["embedding"], candidate_pairs)
        print(f"\n  raw best match for person4 (regardless of threshold): "
              f"student_id={p4_best_sid}, confidence={round(p4_best_conf, 4)}")

        print("\n" + "-" * 78)
        print("STEP 3b: composite [group.png + person4.jpg] (4 real faces, 1 unknown) "
              "through POST /api/attendance/facial")
        print("-" * 78)

        group_img = cv2.imdecode(np.frombuffer(group_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        p4_img = cv2.imdecode(np.frombuffer(person4_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        target_h = group_img.shape[0]
        scale = target_h / p4_img.shape[0]
        p4_resized = cv2.resize(p4_img, (int(p4_img.shape[1] * scale), target_h))
        composite = cv2.hconcat([group_img, p4_resized])
        ok, composite_bytes = cv2.imencode(".png", composite)
        composite_bytes = composite_bytes.tobytes()

        composite_resp = authed_post(
            "/api/attendance/facial",
            data={"class_id": str(class_id), "date": "2026-08-16", "image": (io.BytesIO(composite_bytes), "composite.png")},
            content_type="multipart/form-data",
        )
        assert composite_resp.status_code == 200, composite_resp.get_json()
        composite_body = composite_resp.get_json()
        print("  raw response:")
        print(" ", json.dumps(composite_body, indent=2).replace("\n", "\n  "))

        # --- step 4: threshold gap analysis ---
        print("\n" + "-" * 78)
        print("STEP 4: threshold gap analysis (using STEP 2 correct matches vs "
              "STEP 3a raw person4 best-match score)")
        print("-" * 78)

        correct_confidences = [conf for (_sid, conf) in group_scores.values()]
        min_correct = min(correct_confidences)
        max_correct = max(correct_confidences)
        print(f"  correct-match confidences (group.png, 3 students): "
              f"{[round(c, 4) for c in correct_confidences]}")
        print(f"  lowest correct-match confidence:  {round(min_correct, 4)}")
        print(f"  highest correct-match confidence: {round(max_correct, 4)}")
        print(f"  person4 (incorrect) best-match confidence: {round(p4_best_conf, 4)}")
        gap = min_correct - p4_best_conf
        print(f"  threshold gap (lowest correct - person4 incorrect): {round(gap, 4)}")
        print(f"\n  current FACE_HIGH_CONFIDENCE_THRESHOLD = {VerifyConfig.FACE_HIGH_CONFIDENCE_THRESHOLD}")
        print(f"  current FACE_LOW_CONFIDENCE_THRESHOLD  = {VerifyConfig.FACE_LOW_CONFIDENCE_THRESHOLD}")
        print(f"  min correct match {'>=' if min_correct >= VerifyConfig.FACE_HIGH_CONFIDENCE_THRESHOLD else '<'} "
              f"HIGH threshold ({VerifyConfig.FACE_HIGH_CONFIDENCE_THRESHOLD})")
        print(f"  person4 score {'>=' if p4_best_conf >= VerifyConfig.FACE_LOW_CONFIDENCE_THRESHOLD else '<'} "
              f"LOW threshold ({VerifyConfig.FACE_LOW_CONFIDENCE_THRESHOLD})")

        # --- step 5: confirm the Attendance rows from step 2 ---
        print("\n" + "-" * 78)
        print("STEP 5: confirm resulting Attendance rows (method=facial, correct student_ids)")
        print("-" * 78)

        rows = Attendance.query.filter_by(class_id=class_id, method=AttendanceMethod.FACIAL).all()
        for r in rows:
            print(f"  Attendance(id={r.id}, student_id={r.student_id}, class_id={r.class_id}, "
                  f"date={r.date}, status={r.status.value}, method={r.method.value})")

        expected_ids = set(students.values())
        actual_ids = {r.student_id for r in rows if r.date.isoformat() == "2026-08-14"}
        print(f"\n  expected student_ids marked from group.png: {sorted(expected_ids)}")
        print(f"  actual student_ids marked with method=facial: {sorted(actual_ids)}")
        print(f"  match: {expected_ids == actual_ids}")

        # person4-alone run: nobody should have been auto-marked at all.
        print(f"\n  STEP 3a (person4 alone) auto_marked: {p4_body['auto_marked']} "
              f"(expected: [])")
        print(f"  STEP 3a (person4 alone) needs_confirmation: {p4_body['needs_confirmation']}")

        # composite run: exactly the 3 real students should be auto-marked
        # (from their own faces), and person4's face should show up as its
        # own needs_confirmation/unmatched entry, not folded into one of
        # the 3 real matches.
        composite_auto_ids = {m["student_id"] for m in composite_body["auto_marked"]}
        print(f"\n  STEP 3b (composite) auto_marked student_ids: {sorted(composite_auto_ids)} "
              f"(expected: {sorted(expected_ids)})")
        print(f"  STEP 3b (composite) faces_detected: {composite_body['faces_detected']} (expected: 4)")
        print(f"  STEP 3b (composite) needs_confirmation: {composite_body['needs_confirmation']}")
        print(f"  STEP 3b correctly isolated person4 without folding into a real match: "
              f"{composite_auto_ids == expected_ids}")

        print("\n" + "=" * 78)
        print("DONE")
        print("=" * 78)


if __name__ == "__main__":
    main()