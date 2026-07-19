"""Seed demo data.

Run: `docker compose run --rm api python -m app.seed` (or `uv run python -m app.seed`).
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.db_sync import SyncSessionLocal
from app.models import (
    CheckResult,
    Incident,
    IncidentStatus,
    Membership,
    Monitor,
    MonitorType,
    Role,
    Team,
    User,
)
from app.security import hash_password


def seed() -> None:
    demo_emails = ["owner@pulsedemo.com", "admin@pulsedemo.com", "member@pulsedemo.com"]
    with SyncSessionLocal.begin() as s:
        # Idempotent: remove any prior demo data. Users are global, so delete them by email;
        # deleting the team cascades its monitors/results/incidents.
        s.execute(delete(User).where(User.email.in_(demo_emails)))
        existing = s.execute(select(Team).where(Team.slug == "demo")).scalar_one_or_none()
        if existing:
            s.delete(existing)
        s.flush()

        team = Team(
            name="Demo Co",
            slug="demo",
            tier="pro",
            subscription_status="active",
            stripe_customer_id="cus_demo",
            stripe_subscription_id="sub_demo",
        )
        s.add(team)
        s.flush()

        for email, role in [
            ("owner@pulsedemo.com", Role.owner),
            ("admin@pulsedemo.com", Role.admin),
            ("member@pulsedemo.com", Role.member),
        ]:
            user = User(email=email, password_hash=hash_password("password123"))
            s.add(user)
            s.flush()
            s.add(Membership(user_id=user.id, team_id=team.id, role=role))

        now = datetime.now(UTC)
        m_up = Monitor(
            team_id=team.id,
            name="Marketing site",
            type=MonitorType.http,
            url="https://example.com",
            public=True,
            next_check_at=now,
        )
        m_down = Monitor(
            team_id=team.id,
            name="API",
            type=MonitorType.http,
            url="https://api.example.com/health",
            public=True,
            next_check_at=now,
        )
        m_tcp = Monitor(
            team_id=team.id,
            name="Postgres",
            type=MonitorType.tcp,
            host="db.example.com",
            port=5432,
            next_check_at=now,
        )
        m_ping = Monitor(
            team_id=team.id,
            name="Gateway",
            type=MonitorType.ping,
            host="1.1.1.1",
            public=True,
            next_check_at=now,
        )
        s.add_all([m_up, m_down, m_tcp, m_ping])
        s.flush()

        for i in range(5):
            s.add(
                CheckResult(
                    team_id=team.id,
                    monitor_id=m_up.id,
                    up=True,
                    status_code=200,
                    latency_ms=120,
                    checked_at=now - timedelta(minutes=i),
                )
            )
        for i in range(3):
            s.add(
                CheckResult(
                    team_id=team.id,
                    monitor_id=m_down.id,
                    up=False,
                    status_code=503,
                    error="503 Service Unavailable",
                    checked_at=now - timedelta(minutes=i),
                )
            )
        s.add(
            Incident(
                team_id=team.id,
                monitor_id=m_down.id,
                status=IncidentStatus.open,
                started_at=now - timedelta(minutes=2),
            )
        )

    print(
        "Seeded 'demo' team. Login owner@pulsedemo.com / admin@pulsedemo.com / "
        "member@pulsedemo.com (password 'password123'). Public status page: /status/demo"
    )


if __name__ == "__main__":
    seed()
