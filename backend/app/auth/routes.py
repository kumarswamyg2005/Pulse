import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.accounts import create_user_with_personal_team
from app.alerts import send_email_task
from app.config import settings
from app.deps import current_session, get_current_user, get_db
from app.models import Membership, Role, Team, User
from app.ratelimit import limiter
from app.security import hash_password, verify_password
from app.sessions import create_session, delete_session
from app.tokens import consume_reset_token, create_reset_token

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: Role


class MeOut(BaseModel):
    user: UserOut
    current_team: TeamOut | None
    teams: list[TeamOut]


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
    )


@router.post("/signup", status_code=201)
@limiter.limit("10/minute")
async def signup(
    request: Request, creds: Credentials, response: Response, db: AsyncSession = Depends(get_db)
):
    if len(creds.password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")
    if (await db.execute(select(User).where(User.email == creds.email))).scalar_one_or_none():
        raise HTTPException(409, "Email already registered")

    user, team = await create_user_with_personal_team(
        db, creds.email, hash_password(creds.password)
    )
    token = await create_session(user.id, team.id)
    set_session_cookie(response, token)
    return {
        "user": {"id": user.id, "email": user.email},
        "current_team": {"id": team.id, "name": team.name, "slug": team.slug},
    }


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request, creds: Credentials, response: Response, db: AsyncSession = Depends(get_db)
):
    user = (await db.execute(select(User).where(User.email == creds.email))).scalar_one_or_none()
    if (
        not user
        or not user.password_hash
        or not verify_password(creds.password, user.password_hash)
    ):
        raise HTTPException(401, "Invalid credentials")
    m = (
        (
            await db.execute(
                select(Membership)
                .where(Membership.user_id == user.id)
                .order_by(Membership.created_at)
            )
        )
        .scalars()
        .first()
    )
    token = await create_session(user.id, m.team_id if m else None)
    set_session_cookie(response, token)
    return {"user": {"id": user.id, "email": user.email}}


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await delete_session(token)
    response.delete_cookie(settings.session_cookie_name, path="/")


@router.post("/forgot-password", status_code=202)
@limiter.limit("10/minute")
async def forgot_password(request: Request, body: ForgotIn, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if user:
        token = await create_reset_token(user.id)
        link = f"{settings.frontend_origin}/reset-password?token={token}"
        send_email_task.delay(
            user.email,
            "Reset your Pulse password",
            f'<p>Reset your password: <a href="{link}">{link}</a></p>',
        )
    # Always 202 regardless of existence, so we don't leak which emails are registered.
    return {"status": "sent"}


@router.post("/reset-password")
async def reset_password(body: ResetIn, db: AsyncSession = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters")
    user_id = await consume_reset_token(body.token)
    if user_id is None:
        raise HTTPException(400, "Invalid or expired token")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(400, "Invalid or expired token")
    user.password_hash = hash_password(body.password)
    return {"status": "ok"}


@router.get("/providers")
async def providers() -> dict:
    """Which optional auth providers are configured (so the UI can show/hide buttons)."""
    return {"google": settings.google_client_id is not None}


@router.get("/me", response_model=MeOut)
async def me(
    user: User = Depends(get_current_user),
    session: dict | None = Depends(current_session),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    rows = (
        await db.execute(
            select(Team, Membership.role)
            .join(Membership, Membership.team_id == Team.id)
            .where(Membership.user_id == user.id)
        )
    ).all()
    teams = [TeamOut(id=t.id, name=t.name, slug=t.slug, role=role) for t, role in rows]
    current_team = None
    if session and session.get("team_id"):
        tid = uuid.UUID(session["team_id"])
        current_team = next((t for t in teams if t.id == tid), None)
    return MeOut(user=UserOut(id=user.id, email=user.email), current_team=current_team, teams=teams)
