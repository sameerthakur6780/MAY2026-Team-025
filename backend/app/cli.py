import click
from flask.cli import with_appcontext

from app.extensions import bcrypt, db
from app.models.user import RoleEnum, User


@click.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--full-name", prompt="Full name")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin(email, full_name, password):
    email = email.strip().lower()
    if User.query.filter_by(email=email).first() is not None:
        click.echo(f"A user with email {email} already exists.")
        return

    user = User(
        full_name=full_name,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        role=RoleEnum.ADMIN,
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin account created: {email}")