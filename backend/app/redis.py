from redis.asyncio import Redis

from app.config import settings

redis_client: Redis = Redis.from_url(settings.redis_url)


async def ping_redis() -> bool:
    try:
        return bool(await redis_client.ping())
    except Exception:
        return False
