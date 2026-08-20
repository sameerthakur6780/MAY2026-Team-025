"""Tests for the templated email helper (app.services.email.send_email /
render_email) and the mail startup validation (config.validate_mail_config).
No real SMTP call happens here -- TestConfig sets MAIL_SUPPRESS_SEND=True,
and mail.record_messages() intercepts sends at the Flask-Mail signal level.
"""

from config import validate_mail_config
from app.extensions import mail
from app.services.email import render_email, send_email


def test_render_email_produces_html_and_text(app):
    with app.app_context():
        html_body, text_body = render_email(
            "payment_received",
            {"recipient_name": "Asha", "amount": "1500.00", "receipt_no": "R-1", "student_name": "Ravi"},
        )

    assert "Asha" in html_body
    assert "1500.00" in html_body
    assert "R-1" in html_body
    assert "Asha" in text_body
    assert "SmartBatch" in text_body


def test_send_email_delivers_html_and_text_body(app):
    with app.app_context():
        with mail.record_messages() as outbox:
            send_email(
                "parent@test.com",
                "Payment received",
                "payment_received",
                recipient_name="Asha",
                amount="1500.00",
                receipt_no="R-1",
                student_name="Ravi",
            )

    assert len(outbox) == 1
    sent = outbox[0]
    assert sent.recipients == ["parent@test.com"]
    assert sent.subject == "Payment received"
    assert "Asha" in sent.body
    assert "Asha" in sent.html


def test_send_email_missing_template_does_not_raise(app):
    """send_email() is fire-and-forget under normal operation, but runs
    synchronously under TESTING -- a bad template name must still not raise
    into the caller, since nothing outside this module would catch it on a
    real background thread either."""
    with app.app_context():
        with mail.record_messages() as outbox:
            send_email("parent@test.com", "Subject", "does_not_exist")

    assert outbox == []


class _FakeApp:
    def __init__(self, config, debug=False, testing=False):
        self.config = config
        self.debug = debug
        self.testing = testing


def test_validate_mail_config_noop_when_suppressed():
    fake_app = _FakeApp({"MAIL_SUPPRESS_SEND": True, "MAIL_USERNAME": None, "MAIL_PASSWORD": None})
    validate_mail_config(fake_app)  # must not raise


def test_validate_mail_config_noop_when_credentials_set():
    fake_app = _FakeApp({"MAIL_SUPPRESS_SEND": False, "MAIL_USERNAME": "u", "MAIL_PASSWORD": "p"})
    validate_mail_config(fake_app)  # must not raise


def test_validate_mail_config_warns_in_debug_without_creds(caplog):
    fake_app = _FakeApp(
        {"MAIL_SUPPRESS_SEND": False, "MAIL_USERNAME": None, "MAIL_PASSWORD": None}, debug=True
    )
    with caplog.at_level("WARNING"):
        validate_mail_config(fake_app)

    assert any("MAIL_USERNAME" in record.message for record in caplog.records)


def test_validate_mail_config_raises_outside_debug_without_creds():
    fake_app = _FakeApp(
        {"MAIL_SUPPRESS_SEND": False, "MAIL_USERNAME": None, "MAIL_PASSWORD": None}, debug=False, testing=False
    )
    try:
        validate_mail_config(fake_app)
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass