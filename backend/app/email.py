from dataclasses import dataclass

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()


@dataclass
class Email:
    to: str
    subject: str
    html: str


# Dev/test backend captures here so tests can assert on what was "sent".
outbox: list[Email] = []


def send_email(to: str, subject: str, html: str) -> None:
    """Synchronous send. Callers enqueue app.alerts.send_email_task so it runs in a worker."""
    if settings.email_backend == "resend":
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": settings.email_from, "to": [to], "subject": subject, "html": html},
            )
            resp.raise_for_status()
    else:
        outbox.append(Email(to=to, subject=subject, html=html))
        log.info("email.console", to=to, subject=subject, html=html)
