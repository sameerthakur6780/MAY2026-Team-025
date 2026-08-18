from abc import ABC, abstractmethod


class EmailService(ABC):
    """Provider-agnostic outbound email interface. NotificationService only
    ever calls `send` -- swapping providers later (e.g. to a transactional
    API like SendGrid/Resend) means writing a new implementation of this
    interface, not touching notification_service.py."""

    @abstractmethod
    def send(self, to_email, subject, body, html_body=None):
        """Sends an email with a plain-text `body`, plus an optional HTML
        alternative (`html_body`). Raises EmailSendError on failure."""


class EmailSendError(Exception):
    """Raised by an EmailService implementation when a send attempt fails."""