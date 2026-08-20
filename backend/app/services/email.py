import logging
import threading

from flask import current_app, render_template

from app.extensions import mail
from app.services.flask_mail_email_service import FlaskMailEmailService

logger = logging.getLogger(__name__)

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


def render_email(template, context):
    """Renders `app/templates/email/{template}.html` and `.txt` with
    `context`. Separate from send_email() so the CLI test command (and
    anything else that wants a preview or full control over error handling)
    can render without also triggering a send."""
    html_body = render_template(f"email/{template}.html", **context)
    text_body = render_template(f"email/{template}.txt", **context)
    return html_body, text_body


def _deliver_templated(app, to, subject, template, context):
    with app.app_context():
        try:
            html_body, text_body = render_email(template, context)
            get_email_service().send(to, subject, text_body, html_body=html_body)
        except Exception:
            # Best-effort, fire-and-forget send (see send_email) -- nothing
            # is waiting on this, so log and move on rather than raise on a
            # background thread where nothing would catch it.
            logger.exception("Failed to send templated email %r to %s", template, to)


def send_email(to, subject, template, **context):
    """Renders the `template` (html + txt) with `context` and sends it.

    Non-blocking: runs on a background thread so a request handler calling
    this never waits on an SMTP round-trip -- matching how
    NotificationService.schedule() gets bulk/fan-out sends off the request
    thread, just via a plain thread instead of the APScheduler-backed
    `scheduler` (that scheduler is for *time-delayed* jobs; this send is
    "now", just off-thread, so a raw thread is simpler and doesn't need a
    job store entry). Runs synchronously under TESTING instead, so
    mail.record_messages() sees the send deterministically without a test
    needing to wait on a background thread.
    """
    app = current_app._get_current_object()
    if app.testing:
        _deliver_templated(app, to, subject, template, context)
    else:
        threading.Thread(target=_deliver_templated, args=(app, to, subject, template, context), daemon=True).start()