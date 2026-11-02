"""Add durable inbox and outbox tables.

Revision ID: 20261102_01
Revises:
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa

revision = "20261102_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("inbox_events"):
        op.create_table(
            "inbox_events",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("provider", sa.String(length=40), nullable=False),
            sa.Column("provider_event_id", sa.String(length=255), nullable=False),
            sa.Column("message_id", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(length=120), nullable=True),
            sa.Column("received_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("provider", "provider_event_id", name="uq_inbox_provider_event"),
        )
        op.create_index("ix_inbox_events_message_id", "inbox_events", ["message_id"])
    if not inspector.has_table("outbox_events"):
        op.create_table(
            "outbox_events",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("event_type", sa.String(length=80), nullable=False),
            sa.Column("aggregate_id", sa.String(), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("max_attempts", sa.Integer(), nullable=False),
            sa.Column("available_at", sa.DateTime(), nullable=False),
            sa.Column("locked_until", sa.DateTime(), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])
        op.create_index("ix_outbox_events_available_at", "outbox_events", ["available_at"])
        op.create_index("ix_outbox_events_status", "outbox_events", ["status"])
        op.create_index("ix_outbox_ready", "outbox_events", ["status", "available_at", "created_at"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("outbox_events"):
        op.drop_table("outbox_events")
    if inspector.has_table("inbox_events"):
        op.drop_table("inbox_events")
