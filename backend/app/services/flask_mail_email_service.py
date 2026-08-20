import socket

from flask_mail import Message

from app.services.email_service import EmailSendError, EmailService

# flask-mail/smtplib open the SMTP connection with no timeout at all --
# socket.create_connection() then blocks indefinitely if the network
# silently drops the packets instead of refusing the connection (exactly
# what happens calling smtp.gmail.com:587 from Render, which restricts
# outbound raw SMTP). With no timeout, that hang doesn't fail this one
# email -- it pins the request until gunicorn's *worker* timeout (120s)
# kills the whole process, taking down whatever else that worker was
# doing. 10s is generous for an SMTP handshake (a real connect+login
# measured ~2s) and turns a worker-killing hang into a clean, logged
# EmailSendError.
_SMTP_CONNECT_TIMEOUT_SECONDS = 10


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
        previous_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(_SMTP_CONNECT_TIMEOUT_SECONDS)
        try:
            self._mail.send(message)
        except Exception as exc:  # smtplib/socket errors -- provider-specific, not worth enumerating
            raise EmailSendError(str(exc)) from exc
        finally:
            # Global default -- restore it so this doesn't leak a shorter
            # timeout onto unrelated sockets (Supabase, Razorpay) for the
            # rest of this worker's lifetime. Those clients set their own
            # explicit per-call timeouts already, so this only ever matters
            # as a fallback -- but no reason to touch it longer than needed.
            socket.setdefaulttimeout(previous_timeout)