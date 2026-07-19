import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_membership, get_current_user, get_db
from app.models import Incident, IncidentStatus, Membership, Monitor, User

router = APIRouter(tags=["incidents"])


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID
    monitor_name: str | None = None
    status: IncidentStatus
    started_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    acknowledged_by: uuid.UUID | None


async def _list(db: AsyncSession, where: ColumnElement[bool] | None = None) -> list[IncidentOut]:
    stmt = (
        select(Incident, Monitor.name)
        .join(Monitor, Monitor.id == Incident.monitor_id)
        .order_by(Incident.started_at.desc())
    )
    if where is not None:
        stmt = stmt.where(where)
    rows = (await db.execute(stmt.limit(100))).all()
    result = []
    for incident, name in rows:
        out = IncidentOut.model_validate(incident)
        out.monitor_name = name
        result.append(out)
    return result


@router.get("/incidents", response_model=list[IncidentOut])
async def list_incidents(
    _: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> list[IncidentOut]:
    return await _list(db)


@router.get("/monitors/{monitor_id}/incidents", response_model=list[IncidentOut])
async def monitor_incidents(
    monitor_id: uuid.UUID,
    _: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> list[IncidentOut]:
    return await _list(db, Incident.monitor_id == monitor_id)


@router.post("/incidents/{incident_id}/acknowledge", response_model=IncidentOut)
async def acknowledge_incident(
    incident_id: uuid.UUID,
    user: User = Depends(get_current_user),
    _: Membership = Depends(get_current_membership),  # any member may acknowledge
    db: AsyncSession = Depends(get_db),
) -> IncidentOut:
    incident = await db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(404, "Incident not found")
    incident.acknowledged_at = datetime.now(UTC)
    incident.acknowledged_by = user.id
    await db.flush()
    name = (
        await db.execute(select(Monitor.name).where(Monitor.id == incident.monitor_id))
    ).scalar_one_or_none()
    out = IncidentOut.model_validate(incident)
    out.monitor_name = name
    return out
