import re
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts import send_email_task
from app.config import settings
from app.deps import get_current_user, get_db, team_member, team_role
from app.models import Invite, Membership, Role, Team, User
from app.plans import limits
from app.security import hash_token
from app.sessions import new_token, set_current_team


async def _seat_check(db: AsyncSession, team: Team) -> None:
    max_seats = limits(team.tier)["max_seats"]
    count = (
        await db.execute(
            select(func.count()).select_from(Membership).where(Membership.team_id == team.id)
        )
    ).scalar_one()
    if count >= max_seats:
        raise HTTPException(
            402, f"Seat limit reached ({max_seats}). Upgrade your plan to add teammates."
        )


router = APIRouter(tags=["teams"])


class TeamCreate(BaseModel):
    name: str


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    role: Role


class InviteCreate(BaseModel):
    email: EmailStr
    role: Role = Role.member


class InviteInfo(BaseModel):
    team_name: str
    email: EmailStr
    role: Role


class RoleUpdate(BaseModel):
    role: Role


class UserRef(BaseModel):
    user_id: uuid.UUID


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "team"


def _now() -> datetime:
    return datetime.now(UTC)


@router.post("/teams", status_code=201, response_model=TeamOut)
async def create_team(
    body: TeamCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> TeamOut:
    slug = _slugify(body.name)
    if (await db.execute(select(Team).where(Team.slug == slug))).scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    team = Team(name=body.name, slug=slug)
    db.add(team)
    await db.flush()
    db.add(Membership(user_id=user.id, team_id=team.id, role=Role.owner))
    await db.flush()
    return TeamOut(id=team.id, name=team.name, slug=team.slug)


@router.get("/teams/{team_id}/members", response_model=list[MemberOut])
async def list_members(
    team_id: uuid.UUID,
    _: Membership = Depends(team_member),
    db: AsyncSession = Depends(get_db),
) -> list[MemberOut]:
    rows = (
        await db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.team_id == team_id)
            .order_by(Membership.created_at)
        )
    ).all()
    return [MemberOut(user_id=u.id, email=u.email, role=m.role) for m, u in rows]


@router.post("/teams/{team_id}/invites", status_code=201)
async def create_invite(
    team_id: uuid.UUID,
    body: InviteCreate,
    _: Membership = Depends(team_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
):
    if body.role == Role.owner:
        raise HTTPException(400, "Cannot invite someone as owner")
    existing_user = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if existing_user:
        already = (
            await db.execute(
                select(Membership).where(
                    Membership.user_id == existing_user.id, Membership.team_id == team_id
                )
            )
        ).scalar_one_or_none()
        if already:
            raise HTTPException(409, "Already a member of this team")

    team = await db.get(Team, team_id)
    assert team is not None
    await _seat_check(db, team)

    token = new_token()
    invite = Invite(
        team_id=team_id,
        email=body.email,
        role=body.role,
        token_hash=hash_token(token),
        expires_at=_now() + timedelta(seconds=settings.invite_ttl_seconds),
    )
    db.add(invite)
    await db.flush()
    link = f"{settings.frontend_origin}/invite/{token}"
    send_email_task.delay(
        body.email,
        "You've been invited to a Pulse team",
        f'<p>Join the team: <a href="{link}">{link}</a></p>',
    )
    return {"id": invite.id, "email": body.email, "role": body.role}


async def _load_open_invite(token: str, db: AsyncSession) -> Invite:
    invite = (
        await db.execute(select(Invite).where(Invite.token_hash == hash_token(token)))
    ).scalar_one_or_none()
    if invite is None or invite.accepted_at is not None or invite.expires_at < _now():
        raise HTTPException(400, "Invalid or expired invite")
    return invite


@router.get("/invites/{token}", response_model=InviteInfo)
async def get_invite(token: str, db: AsyncSession = Depends(get_db)) -> InviteInfo:
    invite = await _load_open_invite(token, db)
    team = await db.get(Team, invite.team_id)
    assert team is not None
    return InviteInfo(team_name=team.name, email=invite.email, role=invite.role)


@router.post("/invites/{token}/accept", status_code=201)
async def accept_invite(
    token: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    invite = await _load_open_invite(token, db)
    if user.email.lower() != invite.email.lower():
        raise HTTPException(403, "This invite is for a different email address")
    existing = (
        await db.execute(
            select(Membership).where(
                Membership.user_id == user.id, Membership.team_id == invite.team_id
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        team = await db.get(Team, invite.team_id)
        assert team is not None
        await _seat_check(db, team)
        db.add(Membership(user_id=user.id, team_id=invite.team_id, role=invite.role))
    invite.accepted_at = _now()
    return {"team_id": invite.team_id}


@router.patch("/teams/{team_id}/members/{user_id}", status_code=204)
async def change_role(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    body: RoleUpdate,
    _: Membership = Depends(team_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
):
    if body.role == Role.owner:
        raise HTTPException(400, "Use transfer-ownership to change the owner")
    target = await _member(db, team_id, user_id)
    if target.role == Role.owner:
        raise HTTPException(403, "Cannot change the owner's role")
    target.role = body.role


@router.delete("/teams/{team_id}/members/{user_id}", status_code=204)
async def remove_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    _: Membership = Depends(team_role(Role.owner, Role.admin)),
    db: AsyncSession = Depends(get_db),
):
    target = await _member(db, team_id, user_id)
    if target.role == Role.owner:
        raise HTTPException(403, "Cannot remove the owner")
    await db.delete(target)


@router.post("/teams/{team_id}/transfer-ownership", status_code=204)
async def transfer_ownership(
    team_id: uuid.UUID,
    body: UserRef,
    actor: Membership = Depends(team_role(Role.owner)),
    db: AsyncSession = Depends(get_db),
):
    target = await _member(db, team_id, body.user_id)
    actor.role = Role.admin
    target.role = Role.owner


@router.delete("/teams/{team_id}", status_code=204)
async def delete_team(
    team_id: uuid.UUID,
    _: Membership = Depends(team_role(Role.owner)),
    db: AsyncSession = Depends(get_db),
):
    team = await db.get(Team, team_id)
    if team is not None:
        await db.delete(team)


@router.post("/teams/{team_id}/switch", response_model=TeamOut)
async def switch_team(
    team_id: uuid.UUID,
    request: Request,
    membership: Membership = Depends(team_member),
    db: AsyncSession = Depends(get_db),
) -> TeamOut:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await set_current_team(token, team_id)
    team = await db.get(Team, membership.team_id)
    assert team is not None
    return TeamOut(id=team.id, name=team.name, slug=team.slug)


async def _member(db: AsyncSession, team_id: uuid.UUID, user_id: uuid.UUID) -> Membership:
    m = (
        await db.execute(
            select(Membership).where(Membership.team_id == team_id, Membership.user_id == user_id)
        )
    ).scalar_one_or_none()
    if m is None:
        raise HTTPException(404, "Member not found")
    return m
