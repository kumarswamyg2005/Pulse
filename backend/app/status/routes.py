import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models import Incident, IncidentStatus, Monitor, Team
from app.monitors.routes import _latest_statuses, _uptime_24h
from app.ratelimit import limiter
from app.redis import redis_client

router = APIRouter(tags=["status"])

CACHE_TTL = 30


@router.get("/status/{slug}")
@limiter.limit("60/minute")
async def public_status(request: Request, slug: str, db: AsyncSession = Depends(get_db)) -> dict:
    cache_key = f"status:{slug}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    team = (await db.execute(select(Team).where(Team.slug == slug))).scalar_one_or_none()
    if team is None:
        raise HTTPException(404, "Status page not found")

    # Public endpoint has no session, so scope RLS to this team explicitly.
    await db.execute(
        text("SELECT set_config('app.current_team_id', :t, true)"), {"t": str(team.id)}
    )
    monitors = (
        (await db.execute(select(Monitor).where(Monitor.public.is_(True)).order_by(Monitor.name)))
        .scalars()
        .all()
    )
    ids = [m.id for m in monitors]
    latest = await _latest_statuses(db, ids)
    uptime = await _uptime_24h(db, ids)

    mons = [
        {
            "name": m.name,
            "type": m.type,
            "status": latest[m.id][0] if m.id in latest else None,
            "uptime_24h": uptime.get(m.id),
        }
        for m in monitors
    ]

    incidents = []
    if ids:
        since = datetime.now(UTC) - timedelta(days=7)
        rows = (
            await db.execute(
                select(Incident, Monitor.name)
                .join(Monitor, Monitor.id == Incident.monitor_id)
                .where(Incident.monitor_id.in_(ids))
                .where((Incident.status == IncidentStatus.open) | (Incident.started_at >= since))
                .order_by(Incident.started_at.desc())
                .limit(20)
            )
        ).all()
        incidents = [
            {
                "monitor_name": name,
                "status": inc.status,
                "started_at": inc.started_at.isoformat(),
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            }
            for inc, name in rows
        ]

    payload = {"team": team.name, "monitors": mons, "incidents": incidents}
    await redis_client.set(cache_key, json.dumps(payload), ex=CACHE_TTL)
    return payload
