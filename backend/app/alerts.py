from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.config import settings
from app.email import send_email
from app.models import Membership, Monitor, Role, User, Webhook


@celery_app.task(name="app.alerts.send_email_task")
def send_email_task(to: str, subject: str, html: str) -> None:
    send_email(to, subject, html)


def _post_webhook(url: str, payload: dict[str, str]) -> None:
    with httpx.Client(timeout=10) as client:
        client.post(url, json=payload).raise_for_status()


@celery_app.task(bind=True, max_retries=3, name="app.alerts.deliver_webhook")
def deliver_webhook(self, url: str, payload: dict[str, str]) -> None:
    try:
        _post_webhook(url, payload)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10) from exc


def _admin_emails(session: Session, team_id) -> list[str]:
    return list(
        session.execute(
            select(User.email)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.team_id == team_id, Membership.role.in_([Role.owner, Role.admin]))
        )
        .scalars()
        .all()
    )


def send_incident_alerts(session: Session, monitor: Monitor, event: str) -> None:
    if event not in ("opened", "resolved"):
        return
    down = event == "opened"
    target = monitor.url or monitor.host or monitor.name
    subject = f"[Pulse] {monitor.name} is {'DOWN' if down else 'back UP'}"
    html = (
        f"<p>Monitor <strong>{monitor.name}</strong> ({target}) is "
        f"{'DOWN' if down else 'back up'}.</p>"
    )
    for email in _admin_emails(session, monitor.team_id):
        send_email_task.delay(email, subject, html)

    hooks = (
        session.execute(
            select(Webhook.url).where(Webhook.team_id == monitor.team_id, Webhook.active.is_(True))
        )
        .scalars()
        .all()
    )
    payload = {
        "event": event,
        "monitor": monitor.name,
        "monitor_id": str(monitor.id),
        "target": target,
    }
    for url in hooks:
        deliver_webhook.delay(url, payload)


def maybe_cert_warning(session: Session, monitor: Monitor) -> None:
    """Warn once when a TLS cert nears expiry; reset when it's renewed. Not an incident."""
    if monitor.cert_expires_at is None:
        monitor.cert_warning_sent = False
        return
    days = (monitor.cert_expires_at - datetime.now(UTC)).days
    if days <= settings.cert_warning_days:
        if not monitor.cert_warning_sent:
            subject = f"[Pulse] TLS certificate for {monitor.name} expires in {days} days"
            html = (
                f"<p>The TLS certificate for <strong>{monitor.name}</strong> "
                f"expires in {days} days.</p>"
            )
            for email in _admin_emails(session, monitor.team_id):
                send_email_task.delay(email, subject, html)
            monitor.cert_warning_sent = True
    else:
        monitor.cert_warning_sent = False
