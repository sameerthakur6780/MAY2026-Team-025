from flask_mail import Message

from app.services.email_service import EmailSendError, EmailService


class FlaskMailEmailService(EmailService):
    """SMTP-backed EmailService using Flask-Mail. Chosen over a transactional
    API (SendGrid/Resend) to avoid a third-party account dependency for this
    project -- see get_email_service() for the tradeoff this implies."""

    def __init__(self, mail, default_sender):
        self._mail = mail
        self._default_sender = default_sender

    def send(self, to_email, subject, body, html_body=None):
        message = Message(
            subject=subject, recipients=[to_email], body=body, html=html_body, sender=self._default_sender
        )
        try:
            self._mail.send(message)
        except Exception as exc:  # smtplib/socket errors -- provider-specific, not worth enumerating
            raise EmailSendError(str(exc)) from exc