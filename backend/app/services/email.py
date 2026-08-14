from flask import current_app

from app.extensions import mail
from app.services.flask_mail_email_service import FlaskMailEmailService

_service = None


def get_email_service():
    """Lazily builds the email backend from app config on first use.

    TRADEOFF (flagged as requested): this uses Flask-Mail over raw SMTP
    rather than a transactional provider (SendGrid/Resend). Flask-Mail needs
    no third-party account and its MAIL_SUPPRESS_SEND-on-TESTING behavior
    matches this project's existing "no real network calls in tests"
    convention (see FakeStorageService) for free. The real cost: raw SMTP
    has weaker deliverability (more likely to land in spam) and no
    delivery/bounce tracking, which a provider like Resend/SendGrid gives
    you out of the box. Swapping later means writing a new EmailService
    implementation (see email_service.py) and changing only this function.
    """
    global _service
    if _service is None:
        _service = FlaskMailEmailService(mail=mail, default_sender=current_app.config["MAIL_DEFAULT_SENDER"])
    return _service