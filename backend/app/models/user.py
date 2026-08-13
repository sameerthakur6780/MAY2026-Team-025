import enum

from app.extensions import db
from app.models.mixins import TimestampMixin


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    PARENT = "parent"
    STUDENT = "student"


class User(db.Model, TimestampMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, index=True)

    teacher = db.relationship("Teacher", back_populates="user", uselist=False, cascade="all, delete-orphan")
    parent = db.relationship("Parent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student = db.relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role.value})>"
