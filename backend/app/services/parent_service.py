from app.extensions import db
from app.models.parent import Parent
from app.services.auth_service import create_managed_account
from app.utils.errors import ApiError, not_found


def serialize_parent(parent):
    return {
        "id": parent.id,
        "user_id": parent.user_id,
        "full_name": parent.user.full_name,
        "email": parent.user.email,
        "phone": parent.user.phone,
        "occupation": parent.occupation,
        "address": parent.address,
        "student_ids": [s.id for s in parent.students],
    }


def get_parent_or_404(parent_id):
    parent = Parent.query.get(parent_id)
    if parent is None:
        raise not_found("Parent")
    return parent


def create_parent(data):
    """Creates the account (user + parent row) in one shot -- see
    teacher_service.create_teacher for why this delegates to signup's
    account-creation logic rather than reimplementing it."""
    data = dict(data, role="parent")
    user = create_managed_account(data)
    return user.parent


def update_parent(parent_id, data):
    parent = get_parent_or_404(parent_id)
    if "occupation" in data:
        parent.occupation = data["occupation"]
    if "address" in data:
        parent.address = data["address"]
    db.session.commit()
    return parent


def delete_parent(parent_id):
    parent = get_parent_or_404(parent_id)
    if parent.students:
        raise ApiError(
            f"Cannot delete: {len(parent.students)} student(s) are still linked to this parent",
            "conflict",
            409,
        )
    db.session.delete(parent.user)
    db.session.commit()
