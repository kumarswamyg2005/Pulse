import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_membership, get_db, require_role
from app.models import CheckResult, Membership, Monitor, MonitorType, Role, Team
from app.plans import limits

router = APIRouter(prefix="/monitors", tags=["monitors"])


class MonitorCreate(BaseModel):
    name: str
    type: MonitorType = MonitorType.http
    url: str | None = None
    host: str | None = None
    port: int | None = None
    expected_status_min: int = 200
    expected_status_max: int = 399
    keyword: str | None = None
    timeout_seconds: int = 10
    interval_seconds: int = 60
    public: bool = False


class MonitorUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    host: str | None = None
    port: int | None = None
    expected_status_min: int | None = None
    expected_status_max: int | None = None
    keyword: str | None = None
    timeout_seconds: int | None = None
    interval_seconds: int | None = None
    public: bool | None = None
    paused: bool | None = None


class MonitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    team_id: uuid.UUID
    name: str
    type: MonitorType
    url: str | None
    host: str | None
    port: int | None
    expected_status_min: int
    expected_status_max: int
    keyword: str | None
    timeout_seconds: int
    interval_seconds: int
    public: bool
    paused: bool
    next_check_at: datetime | None
    cert_expires_at: datetime | None
    # computed
    last_status: bool | None = None
    last_checked_at: datetime | None = None
    uptime_24h: float | None = None


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    checked_at: datetime
    up: bool
    status_code: int | None
    latency_ms: int | None
    error: str | None


def _now() -> datetime:
    return datetime.now(UTC)


async def _get_owned(db: AsyncSession, monitor_id: uuid.UUID) -> Monitor:
    # RLS scopes this to the current team; another team's id simply returns None.
    m = await db.get(Monitor, monitor_id)
    if m is None:
        raise HTTPException(404, "Monitor not found")
    return m


async def _latest_statuses(
    db: AsyncSession, ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[bool, datetime]]:
    if not ids:
        return {}
    rows = (
        await db.execute(
            select(CheckResult.monitor_id, CheckResult.up, CheckResult.checked_at)
            .distinct(CheckResult.monitor_id)
            .where(CheckResult.monitor_id.in_(ids))
            .order_by(CheckResult.monitor_id, CheckResult.checked_at.desc())
        )
    ).all()
    return {mid: (up, at) for mid, up, at in rows}


async def _uptime_24h(db: AsyncSession, ids: list[uuid.UUID]) -> dict[uuid.UUID, float | None]:
    if not ids:
        return {}
    since = _now() - timedelta(hours=24)
    rows = (
        await db.execute(
            select(
                CheckResult.monitor_id,
                func.count().label("total"),
                func.count().filter(CheckResult.up.is_(True)).label("up_count"),
            )
            .where(CheckResult.monitor_id.in_(ids), CheckResult.checked_at >= since)
            .group_by(CheckResult.monitor_id)
        )
    ).all()
    return {mid: (round(up / total * 100, 2) if total else None) for mid, total, up in rows}


async def _enrich(db: AsyncSession, monitors: list[Monitor]) -> list[MonitorOut]:
    ids = [m.id for m in monitors]
    latest = await _latest_statuses(db, ids)
    uptime = await _uptime_24h(db, ids)
    out: list[MonitorOut] = []
    for m in monitors:
        o = MonitorOut.model_validate(m)
        if (status := latest.get(m.id)) is not None:
            o.last_status, o.last_checked_at = status
        o.uptime_24h = uptime.get(m.id)
        out.append(o)
    return out


@router.post("", status_code=201, response_model=MonitorOut)
async def create_monitor(
    body: MonitorCreate,
    membership: Membership = Depends(require_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> MonitorOut:
    if body.type == MonitorType.http and not body.url:
        raise HTTPException(422, "HTTP monitors require a url")
    if body.type in (MonitorType.tcp, MonitorType.ping) and not body.host:
        raise HTTPException(422, f"{body.type} monitors require a host")
    team = await db.get(Team, membership.team_id)
    assert team is not None
    max_monitors = limits(team.tier)["max_monitors"]
    if max_monitors >= 0:
        count = (await db.execute(select(func.count()).select_from(Monitor))).scalar_one()
        if count >= max_monitors:
            raise HTTPException(
                402, f"Monitor limit reached ({max_monitors}). Upgrade your plan to add more."
            )
    interval = max(body.interval_seconds, limits(team.tier)["min_interval"])
    monitor = Monitor(
        team_id=membership.team_id,
        name=body.name,
        type=body.type,
        url=body.url,
        host=body.host,
        port=body.port,
        expected_status_min=body.expected_status_min,
        expected_status_max=body.expected_status_max,
        keyword=body.keyword,
        timeout_seconds=body.timeout_seconds,
        interval_seconds=interval,
        public=body.public,
        next_check_at=_now(),
    )
    db.add(monitor)
    await db.flush()
    return MonitorOut.model_validate(monitor)


@router.get("", response_model=list[MonitorOut])
async def list_monitors(
    _: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> list[MonitorOut]:
    rows = (await db.execute(select(Monitor).order_by(Monitor.created_at))).scalars().all()
    return await _enrich(db, list(rows))


@router.get("/{monitor_id}", response_model=MonitorOut)
async def get_monitor(
    monitor_id: uuid.UUID,
    _: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> MonitorOut:
    monitor = await _get_owned(db, monitor_id)
    return (await _enrich(db, [monitor]))[0]


@router.get("/{monitor_id}/results", response_model=list[ResultOut])
async def monitor_results(
    monitor_id: uuid.UUID,
    limit: int = 50,
    _: Membership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_db),
) -> list[ResultOut]:
    await _get_owned(db, monitor_id)  # 404 if not in the current team
    rows = (
        (
            await db.execute(
                select(CheckResult)
                .where(CheckResult.monitor_id == monitor_id)
                .order_by(CheckResult.checked_at.desc())
                .limit(min(limit, 200))
            )
        )
        .scalars()
        .all()
    )
    return [ResultOut.model_validate(r) for r in rows]


@router.patch("/{monitor_id}", response_model=MonitorOut)
async def update_monitor(
    monitor_id: uuid.UUID,
    body: MonitorUpdate,
    membership: Membership = Depends(require_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> MonitorOut:
    monitor = await _get_owned(db, monitor_id)
    data = body.model_dump(exclude_unset=True)
    if "interval_seconds" in data:
        team = await db.get(Team, membership.team_id)
        assert team is not None
        data["interval_seconds"] = max(data["interval_seconds"], limits(team.tier)["min_interval"])
    for key, value in data.items():
        setattr(monitor, key, value)
    await db.flush()
    return MonitorOut.model_validate(monitor)


@router.delete("/{monitor_id}", status_code=204)
async def delete_monitor(
    monitor_id: uuid.UUID,
    _: Membership = Depends(require_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.delete(await _get_owned(db, monitor_id))
