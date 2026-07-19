import json
import secrets
import uuid

from app.config import settings
from app.redis import redis_client

_PREFIX = "session:"


def new_token() -> str:
    return secrets.token_urlsafe(32)


async def create_session(user_id: uuid.UUID, team_id: uuid.UUID | None) -> str:
    token = new_token()
    payload = {"user_id": str(user_id), "team_id": str(team_id) if team_id else None}
    await redis_client.set(_PREFIX + token, json.dumps(payload), ex=settings.session_ttl_seconds)
    return token


async def get_session(token: str) -> dict | None:
    raw = await redis_client.get(_PREFIX + token)
    return json.loads(raw) if raw is not None else None


async def set_current_team(token: str, team_id: uuid.UUID) -> None:
    data = await get_session(token)
    if data:
        data["team_id"] = str(team_id)
        await redis_client.set(_PREFIX + token, json.dumps(data), ex=settings.session_ttl_seconds)


async def delete_session(token: str) -> None:
    await redis_client.delete(_PREFIX + token)
