import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.alerts import maybe_cert_warning, send_incident_alerts
from app.celery_app import celery_app
from app.checks import run_monitor_check
from app.db_sync import SyncSessionLocal
from app.incidents.engine import evaluate_incident
from app.models import CheckResult, Monitor


def _now() -> datetime:
    return datetime.now(UTC)


def _next_with_jitter(interval_seconds: int) -> datetime:
    # ±15% jitter so checks don't fire in a synchronized thundering herd.
    factor = 1 + random.uniform(-0.15, 0.15)
    return _now() + timedelta(seconds=interval_seconds * factor)


@celery_app.task(name="app.tasks.dispatch_due_checks")
def dispatch_due_checks() -> int:
    """Enqueue a check for every monitor that is due. Restart-safe: state lives in Postgres."""
    dispatched = 0
    with SyncSessionLocal.begin() as session:
        due = (
            session.execute(
                select(Monitor)
                .where(Monitor.paused.is_(False), Monitor.next_check_at <= _now())
                .with_for_update(skip_locked=True)
            )
            .scalars()
            .all()
        )
        for monitor in due:
            monitor.next_check_at = _next_with_jitter(monitor.interval_seconds)
            run_check.delay(str(monitor.id))
            dispatched += 1
    return dispatched


@celery_app.task(name="app.tasks.run_check")
def run_check(monitor_id: str) -> None:
    with SyncSessionLocal.begin() as session:
        monitor = session.get(Monitor, monitor_id)
        if monitor is None or monitor.paused:
            return
        outcome = run_monitor_check(monitor)
        session.add(
            CheckResult(
                team_id=monitor.team_id,
                monitor_id=monitor.id,
                up=outcome.up,
                status_code=outcome.status_code,
                latency_ms=outcome.latency_ms,
                error=outcome.error,
            )
        )
        if outcome.cert_expires_at:
            monitor.cert_expires_at = outcome.cert_expires_at
        session.flush()
        event = evaluate_incident(session, monitor)
        if event:
            send_incident_alerts(session, monitor, event)
        maybe_cert_warning(session, monitor)
