import os

# Test env: app role (RLS enforced) for runtime, admin for migrations/truncate, isolated redis db.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://pulse_app:pulse_app@localhost:55432/pulse"
)
os.environ.setdefault(
    "ADMIN_DATABASE_URL", "postgresql+psycopg://pulse:pulse@localhost:55432/pulse"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:56379/15")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("STRIPE_PRICE_PRO", "price_pro")
os.environ.setdefault("STRIPE_PRICE_TEAM", "price_team")

import psycopg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.celery_app import celery_app  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import AsyncSessionLocal  # noqa: E402
from app.email import outbox  # noqa: E402
from app.main import app  # noqa: E402
from app.redis import redis_client  # noqa: E402

# Run Celery tasks inline so .delay() executes in-process (email outbox, webhook capture).
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

# Don't rate-limit the test suite (it makes many requests from one address).
from app.ratelimit import limiter  # noqa: E402

limiter.enabled = False


def _admin_dsn() -> str:
    return settings.admin_database_url.replace("postgresql+psycopg://", "postgresql://")


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture(autouse=True)
async def _clean():
    with psycopg.connect(_admin_dsn(), autocommit=True) as conn:
        # One TRUNCATE for all tables so ACCESS EXCLUSIVE locks are taken atomically
        # (per-table truncation can deadlock on lock ordering).
        conn.execute(
            """
            DO $$ DECLARE tbls text; BEGIN
              SELECT string_agg(quote_ident(tablename), ', ') INTO tbls
              FROM pg_tables WHERE schemaname='public' AND tablename <> 'alembic_version';
              IF tbls IS NOT NULL THEN
                EXECUTE 'TRUNCATE TABLE ' || tbls || ' RESTART IDENTITY CASCADE';
              END IF;
            END $$;
            """
        )
    await redis_client.flushdb()
    outbox.clear()
    yield


@pytest.fixture
async def db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def clients():
    """Factory for independent clients (separate cookie jars) — for multi-user tests."""
    created: list[AsyncClient] = []

    async def make() -> AsyncClient:
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        created.append(c)
        return c

    yield make
    for c in created:
        await c.aclose()


@pytest.fixture
async def auth_client(client):
    """A client signed in as owner@example.com (owner of a fresh personal team)."""
    resp = await client.post(
        "/auth/signup", json={"email": "owner@example.com", "password": "password123"}
    )
    assert resp.status_code == 201, resp.text
    return client
