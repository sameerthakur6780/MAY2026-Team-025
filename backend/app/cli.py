import click
from flask.cli import with_appcontext

from app.extensions import bcrypt, db
from app.models.user import RoleEnum, User
from app.utils.validators import INDIAN_PHONE_ERROR, INDIAN_PHONE_REGEX


def _validate_phone(ctx, param, value):
    if not INDIAN_PHONE_REGEX.match(value):
        raise click.BadParameter(INDIAN_PHONE_ERROR)
    return value


@click.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--full-name", prompt="Full name")
@click.option("--phone", prompt="Phone number", callback=_validate_phone)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin(email, full_name, phone, password):
    email = email.strip().lower()
    if User.query.filter_by(email=email).first() is not None:
        click.echo(f"A user with email {email} already exists.")
        return

    user = User(
        full_name=full_name,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        phone=phone,
        role=RoleEnum.ADMIN,
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin account created: {email}")