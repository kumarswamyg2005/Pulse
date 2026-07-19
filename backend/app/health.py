from fastapi import APIRouter, Response

from app.db import ping_db
from app.redis import ping_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness: the process is up. No dependencies checked."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(response: Response) -> dict:
    """Readiness: Postgres and Redis are reachable."""
    checks = {"postgres": await ping_db(), "redis": await ping_redis()}
    if all(checks.values()):
        return {"status": "ready", "checks": checks}
    response.status_code = 503
    return {"status": "not ready", "checks": checks}
