"""monitors + tier column + row-level security

Revision ID: 0003_monitors
Revises: 0002_invites
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0003_monitors"
down_revision = "0002_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("tier", sa.String(20), server_default="free", nullable=False))

    op.create_table(
        "monitors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("type", sa.String(10), server_default="http", nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("host", sa.String(255), nullable=True),
        sa.Column("port", sa.Integer, nullable=True),
        sa.Column("expected_status_min", sa.Integer, server_default="200", nullable=False),
        sa.Column("expected_status_max", sa.Integer, server_default="399", nullable=False),
        sa.Column("keyword", sa.String(255), nullable=True),
        sa.Column("timeout_seconds", sa.Integer, server_default="10", nullable=False),
        sa.Column("interval_seconds", sa.Integer, server_default="60", nullable=False),
        sa.Column("public", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("paused", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_monitors_team_id", "monitors", ["team_id"])
    op.create_index("ix_monitors_next_check_at", "monitors", ["next_check_at"])

    # Row-Level Security: scope every row to the request's current team.
    op.execute("ALTER TABLE monitors ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE monitors FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY monitors_team_isolation ON monitors
        USING (team_id = current_setting('app.current_team_id', true)::uuid)
        WITH CHECK (team_id = current_setting('app.current_team_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON monitors TO pulse_app")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS monitors_team_isolation ON monitors")
    op.drop_table("monitors")
    op.drop_column("teams", "tier")
