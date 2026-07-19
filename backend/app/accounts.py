import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, Role, Team, User


def slugify(email: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", email.split("@")[0].lower()).strip("-") or "team"


async def create_user_with_personal_team(
    db: AsyncSession, email: str, password_hash: str | None = None
) -> tuple[User, Team]:
    """Create a user plus a personal team they own. Shared by signup and OAuth."""
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    await db.flush()

    slug = slugify(email)
    if (await db.execute(select(Team).where(Team.slug == slug))).scalar_one_or_none():
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
    team = Team(name=f"{email.split('@')[0]}'s team", slug=slug)
    db.add(team)
    await db.flush()

    db.add(Membership(user_id=user.id, team_id=team.id, role=Role.owner))
    await db.flush()
    return user, team


async def get_or_create_oauth_user(db: AsyncSession, email: str) -> tuple[User, uuid.UUID | None]:
    """Log in an existing user by verified email, or create one with a personal team."""
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user:
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
        return user, (m.team_id if m else None)
    user, team = await create_user_with_personal_team(db, email)
    return user, team.id
