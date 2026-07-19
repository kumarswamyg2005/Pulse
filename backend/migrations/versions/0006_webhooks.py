"""webhooks + cert_warning_sent + RLS

Revision ID: 0006_webhooks
Revises: 0005_incidents
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0006_webhooks"
down_revision = "0005_incidents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "monitors",
        sa.Column("cert_warning_sent", sa.Boolean, server_default=sa.false(), nullable=False),
    )

    op.create_table(
        "webhooks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("active", sa.Boolean, server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_webhooks_team_id", "webhooks", ["team_id"])

    op.execute("ALTER TABLE webhooks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE webhooks FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY webhooks_team_isolation ON webhooks
        USING (team_id = current_setting('app.current_team_id', true)::uuid)
        WITH CHECK (team_id = current_setting('app.current_team_id', true)::uuid)
        """
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON webhooks TO pulse_app")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS webhooks_team_isolation ON webhooks")
    op.drop_table("webhooks")
    op.drop_column("monitors", "cert_warning_sent")
