from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.academic import Subject
from app.utils.errors import ApiError, not_found


def serialize_subject(subject):
    return {"id": subject.id, "name": subject.name}


def get_subject_or_404(subject_id):
    subject = Subject.query.get(subject_id)
    if subject is None:
        raise not_found("Subject")
    return subject


def create_subject(data):
    subject = Subject(name=data["name"].strip())
    db.session.add(subject)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("A subject with this name already exists", "conflict", 409)
    return subject


def update_subject(subject_id, data):
    subject = get_subject_or_404(subject_id)
    if "name" in data:
        subject.name = data["name"].strip()
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("A subject with this name already exists", "conflict", 409)
    return subject


def delete_subject(subject_id):
    subject = get_subject_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
