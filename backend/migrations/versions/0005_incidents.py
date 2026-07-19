"""incidents + RLS

Revision ID: 0005_incidents
Revises: 0004_check_results
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0005_incidents"
down_revision = "0004_check_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "monitor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("monitors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(10), server_default="open", nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "acknowledged_by",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_incidents_team_id", "incidents", ["team_id"])
    op.create_index("ix_incidents_monitor_started", "incidents", ["monitor_id", "started_at"])

    op.execute("ALTER TABLE incidents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE incidents FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY incidents_team_isolation ON incidents
        USING (team_id = current_setting('app.current_team_id', true)::uuid)
        WITH CHECK (team_id = current_setting('app.current_team_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON incidents TO pulse_app")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS incidents_team_isolation ON incidents")
    op.drop_table("incidents")
