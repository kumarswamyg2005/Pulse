"""stripe billing columns on teams

Revision ID: 0007_billing
Revises: 0006_webhooks
Create Date: 2026-07-19
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_billing"
down_revision = "0006_webhooks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("teams", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("teams", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.add_column("teams", sa.Column("subscription_status", sa.String(30), nullable=True))
    op.add_column(
        "teams", sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("teams", "current_period_end")
    op.drop_column("teams", "subscription_status")
    op.drop_column("teams", "stripe_subscription_id")
    op.drop_column("teams", "stripe_customer_id")
