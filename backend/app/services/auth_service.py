from datetime import date

from sqlalchemy.exc import IntegrityError

from app.extensions import bcrypt, db
from app.models.parent import Parent
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import RoleEnum, User


CREATABLE_ROLES = {RoleEnum.TEACHER.value, RoleEnum.PARENT.value, RoleEnum.STUDENT.value}


class AuthError(Exception):
    def __init__(self, message, code="auth_error", status_code=400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def authenticate(email, password):
    if not email or not password:
        raise AuthError("Email and password are required", "missing_credentials", 400)

    user = User.query.filter_by(email=email).first()
    if user is None or not bcrypt.check_password_hash(user.password_hash, password):
        raise AuthError("Invalid email or password", "invalid_credentials", 401)

    return user


def create_managed_account(data):
    role = data.get("role")
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if role not in CREATABLE_ROLES:
        raise AuthError("role must be one of: teacher, parent, student", "invalid_role", 400)
    if not full_name or not email:
        raise AuthError("full_name and email are required", "missing_fields", 400)
    if len(password) < 6:
        raise AuthError("password must be at least 6 characters", "weak_password", 400)
    if User.query.filter_by(email=email).first() is not None:
        raise AuthError("An account with this email already exists", "email_taken", 409)

    user = User(
        full_name=full_name,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        phone=data.get("phone"),
        role=RoleEnum(role),
    )
    db.session.add(user)
    db.session.flush()  

    if role == RoleEnum.TEACHER.value:
        db.session.add(Teacher(user_id=user.id))
    elif role == RoleEnum.PARENT.value:
        db.session.add(
            Parent(user_id=user.id, occupation=data.get("occupation"), address=data.get("address"))
        )
    elif role == RoleEnum.STUDENT.value:
        # admission_no is unique+required at the DB level, but nobody types
        # a meaningful one for a small tuition centre -- derive it from the
        # user's own id (already unique) so it's never a required form field.
        admission_no = data.get("admission_no") or f"STU{user.id:05d}"
        db.session.add(
            Student(
                user_id=user.id,
                admission_no=admission_no,
                dob=_parse_date(data.get("dob")),
                gender=data.get("gender"),
                class_id=data.get("class_id"),
                parent_id=data.get("parent_id"),
            )
        )

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise AuthError(
            "A record with conflicting unique fields already exists",
            "conflict",
            409,
        )

    return user


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)