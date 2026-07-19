from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CheckResult, Incident, IncidentStatus, Monitor


def evaluate_incident(session: Session, monitor: Monitor) -> str | None:
    """After a new CheckResult is flushed, open/resolve the monitor's incident.

    Returns "opened", "resolved", or None (used by ticket 08 to fire alerts).
    """
    open_incident = session.execute(
        select(Incident).where(
            Incident.monitor_id == monitor.id, Incident.status == IncidentStatus.open
        )
    ).scalar_one_or_none()

    window = max(settings.incident_open_threshold, settings.incident_resolve_threshold)
    recent = (
        session.execute(
            select(CheckResult.up)
            .where(CheckResult.monitor_id == monitor.id)
            .order_by(CheckResult.checked_at.desc())
            .limit(window)
        )
        .scalars()
        .all()
    )

    if open_incident is None:
        n = settings.incident_open_threshold
        if len(recent) >= n and not any(recent[:n]):  # last n checks all failed
            session.add(
                Incident(
                    team_id=monitor.team_id,
                    monitor_id=monitor.id,
                    status=IncidentStatus.open,
                    started_at=datetime.now(UTC),
                )
            )
            return "opened"
    else:
        n = settings.incident_resolve_threshold
        if len(recent) >= n and all(recent[:n]):  # last n checks all succeeded
            open_incident.status = IncidentStatus.resolved
            open_incident.resolved_at = datetime.now(UTC)
            return "resolved"
    return None
