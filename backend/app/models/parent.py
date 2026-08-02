from app.extensions import db
from app.models.mixins import TimestampMixin


class Parent(db.Model, TimestampMixin):
    __tablename__ = "parents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True, index=True)
    occupation = db.Column(db.String(120))
    address = db.Column(db.Text)

    user = db.relationship("User", back_populates="parent")
    students = db.relationship("Student", back_populates="parent")

    def __repr__(self):
        return f"<Parent {self.id} user_id={self.user_id}>"
