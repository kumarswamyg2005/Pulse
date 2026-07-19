"""check_results + cert_expires_at + RLS

Revision ID: 0004_check_results
Revises: 0003_monitors
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0004_check_results"
down_revision = "0003_monitors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monitors", sa.Column("cert_expires_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_table(
        "check_results",
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
        sa.Column(
            "checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("up", sa.Boolean, nullable=False),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error", sa.String(500), nullable=True),
    )
    op.create_index(
        "ix_check_results_monitor_checked", "check_results", ["monitor_id", "checked_at"]
    )
    op.create_index("ix_check_results_team_id", "check_results", ["team_id"])

    op.execute("ALTER TABLE check_results ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE check_results FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY check_results_team_isolation ON check_results
        USING (team_id = current_setting('app.current_team_id', true)::uuid)
        WITH CHECK (team_id = current_setting('app.current_team_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON check_results TO pulse_app")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS check_results_team_isolation ON check_results")
    op.drop_table("check_results")
    op.drop_column("monitors", "cert_expires_at")
