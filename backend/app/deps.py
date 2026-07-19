import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import AsyncSessionLocal
from app.models import Membership, Role, User
from app.sessions import get_session


async def current_session(request: Request) -> dict | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    return await get_session(token)


async def get_db(
    session: dict | None = Depends(current_session),
) -> AsyncGenerator[AsyncSession, None]:
    """One transaction per request. Sets the RLS current-team GUC when authenticated."""
    async with AsyncSessionLocal() as db:
        async with db.begin():
            if session and session.get("team_id"):
                await db.execute(
                    text("SELECT set_config('app.current_team_id', :t, true)"),
                    {"t": session["team_id"]},
                )
            yield db


async def get_current_user(
    session: dict | None = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user = await db.get(User, uuid.UUID(session["user_id"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


async def get_current_membership(
    session: dict | None = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    if not session or not session.get("team_id"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    m = (
        await db.execute(
            select(Membership).where(
                Membership.user_id == uuid.UUID(session["user_id"]),
                Membership.team_id == uuid.UUID(session["team_id"]),
            )
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this team")
    return m


def require_role(*allowed: Role):
    """Dependency factory: allow only the given roles in the current (session) team."""

    async def _check(membership: Membership = Depends(get_current_membership)) -> Membership:
        if membership.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return membership

    return _check


async def team_member(
    team_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    """Resolve the caller's membership in the team named in the path."""
    m = (
        await db.execute(
            select(Membership).where(Membership.user_id == user.id, Membership.team_id == team_id)
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this team")
    return m


def team_role(*allowed: Role):
    """Dependency factory: require one of the roles in the path's team."""

    async def _check(membership: Membership = Depends(team_member)) -> Membership:
        if membership.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return membership

    return _check
