import os

import psycopg


def set_tier(team_id: str, tier: str) -> None:
    """Directly set a team's plan tier (multi-member teams require a paid plan)."""
    dsn = os.environ["ADMIN_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("UPDATE teams SET tier = %s WHERE id = %s", (tier, team_id))
