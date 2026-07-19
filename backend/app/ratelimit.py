from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Per-IP limits backed by Redis. Auth routes add stricter per-route limits.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url,
    default_limits=["200/minute"],
)
