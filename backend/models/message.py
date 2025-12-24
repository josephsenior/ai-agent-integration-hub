"""Message models for communication."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy import Enum as SQLEnum

from ..core.database import Base


class MessageChannel(str, Enum):
    """Supported message channels."""
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    API = "api"


class MessageStatus(str, Enum):
    """Message status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELIVERED = "delivered"


class Message(Base):
    """Message model for tracking communications."""
    
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel = Column(SQLEnum(MessageChannel), nullable=False, index=True)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.PENDING, index=True)
    
    # Message content
    content = Column(Text, nullable=False)
    user_id = Column(String, nullable=True, index=True)
    channel_id = Column(String, nullable=True)  # Slack channel, Discord channel, etc.
    
    # Metadata
    _metadata = Column("metadata", JSON, default=dict)
    integration_id = Column(String, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Response
    response = Column(Text, nullable=True)
    response_metadata = Column(JSON, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "channel": self.channel.value if isinstance(self.channel, Enum) else self.channel,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "content": self.content,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "metadata": self._metadata or {},
            "integration_id": self.integration_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "response": self.response,
            "response_metadata": self.response_metadata or {},
        }

