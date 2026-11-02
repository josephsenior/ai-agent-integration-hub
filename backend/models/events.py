"""Durable inbox and outbox records for external events."""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text, UniqueConstraint

from ..core.database import Base


class InboxEvent(Base):
    """Provider event identity used to make webhook receipt idempotent."""

    __tablename__ = "inbox_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_inbox_provider_event"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(40), nullable=False)
    provider_event_id = Column(String(255), nullable=False)
    message_id = Column(String, nullable=False, index=True)
    event_type = Column(String(120), nullable=True)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class OutboxEvent(Base):
    """Work item committed atomically with its accepted inbox message."""

    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_ready", "status", "available_at", "created_at"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(80), nullable=False)
    aggregate_id = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    available_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    locked_until = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Return operational fields without exposing payload data."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "status": self.status,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "available_at": self.available_at.isoformat() if self.available_at else None,
            "last_error": self.last_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
