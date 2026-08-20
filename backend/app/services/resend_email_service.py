"""HTTP-based EmailService using Resend's API. Uses `requests` directly
(already a dependency, same pattern as razorpay_service.py) rather than the
`resend` PyPI package -- one POST request doesn't need a whole SDK.

Exists because Render blocks/restricts outbound raw SMTP: a plain smtplib
connection to Gmail (or any SMTP host) from a Render web service just hangs
instead of being refused -- see the timeout comment in
flask_mail_email_service.py, and the worker-timeout crash that motivated it.
Resend sends over HTTPS, which Render's egress allows without issue.
"""
import requests

from app.services.email_service import EmailSendError, EmailService

_RESEND_URL = "https://api.resend.com/emails"


class ResendEmailService(EmailService):
    def __init__(self, api_key, default_sender):
        self._api_key = api_key
        self._default_sender = default_sender

    def send(self, to_email, subject, body, html_body=None):
        payload = {
            "from": self._default_sender,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
        if html_body:
            payload["html"] = html_body

        try:
            response = requests.post(
                _RESEND_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            # Includes Resend's own error body where available (e.g. "You can
            # only send testing emails to your own email address" on an
            # unverified sandbox domain) -- surfacing it here rather than a
            # bare status code is what makes that failure mode debuggable.
            detail = exc.response.text if getattr(exc, "response", None) is not None else str(exc)
            raise EmailSendError(detail) from exc
