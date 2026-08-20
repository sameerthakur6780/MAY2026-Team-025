from app.models.academic import SchoolClass
from app.models.student import Student
from app.services.notification_service import NotificationService
from app.utils.errors import not_found


def _recipient_user_ids(class_id):
    """Students + their linked parents are the actual audience for a centre
    announcement -- admins/teachers aren't "in a batch" and don't need a
    broadcast meant for families. Deduped via a set since one student's
    parent can have more than one child, and would otherwise get the same
    email once per child."""
    query = Student.query.filter_by(status="active")
    if class_id is not None:
        if SchoolClass.query.get(class_id) is None:
            raise not_found("SchoolClass")
        query = query.filter_by(class_id=class_id)

    user_ids = set()
    for student in query.all():
        user_ids.add(student.user_id)
        if student.parent is not None:
            user_ids.add(student.parent.user_id)
    return user_ids


def send_broadcast(title, message, class_id, priority):
    user_ids = _recipient_user_ids(class_id)
    NotificationService.notify_broadcast_announcement(user_ids, title, message, priority)
    return len(user_ids)
