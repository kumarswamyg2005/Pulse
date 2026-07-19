import secrets
import uuid

from app.config import settings
from app.redis import redis_client

_RESET_PREFIX = "pwreset:"


async def create_reset_token(user_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    await redis_client.set(
        _RESET_PREFIX + token, str(user_id), ex=settings.password_reset_ttl_seconds
    )
    return token


async def consume_reset_token(token: str) -> uuid.UUID | None:
    """One-time use: returns the user id and deletes the token, or None if invalid/expired."""
    key = _RESET_PREFIX + token
    raw = await redis_client.get(key)
    if raw is None:
        return None
    await redis_client.delete(key)
    return uuid.UUID(raw.decode() if isinstance(raw, bytes) else raw)
