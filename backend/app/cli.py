import click
from flask import current_app
from flask.cli import with_appcontext

from app.extensions import bcrypt, db
from app.models.user import RoleEnum, User
from app.services.email import get_email_service, render_email
from app.services.email_service import EmailSendError
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


@click.command("send-test-email")
@click.argument("address")
@with_appcontext
def send_test_email(address):
    """Renders the payment_received template with fake data and sends it
    synchronously via the configured MAIL_* settings -- run this after
    filling in MAIL_USERNAME/MAIL_PASSWORD in .env to confirm end-to-end
    delivery (e.g. to a Mailtrap sandbox inbox) without going through the
    app's UI. Unlike app.services.email.send_email(), this blocks and
    surfaces the outcome directly, since the whole point here is an
    immediate pass/fail rather than off-thread delivery."""
    context = {
        "recipient_name": "Test Parent",
        "amount": "1500.00",
        "receipt_no": "TEST-0001",
        "student_name": "Test Student",
    }
    html_body, text_body = render_email("payment_received", context)
    try:
        get_email_service().send(address, "SmartBatch test email", text_body, html_body=html_body)
    except EmailSendError as exc:
        click.echo(f"Send failed: {exc}")
        raise SystemExit(1)
    click.echo(f"Test email sent to {address} via {current_app.config['MAIL_SERVER']}:{current_app.config['MAIL_PORT']}")