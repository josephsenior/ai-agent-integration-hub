"""Integration models."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from sqlalchemy import JSON, Boolean, Column, DateTime, String, Text
from sqlalchemy import Enum as SQLEnum

from ..core.database import Base


class IntegrationType(str, Enum):
    """Supported integration types."""
    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    WEBHOOK = "webhook"
    CUSTOM_API = "custom_api"


class IntegrationStatus(str, Enum):
    """Integration status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONFIGURING = "configuring"


class Integration(Base):
    """Integration configuration model."""
    
    __tablename__ = "integrations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(SQLEnum(IntegrationType), nullable=False, index=True)
    status = Column(SQLEnum(IntegrationStatus), default=IntegrationStatus.CONFIGURING, index=True)
    
    # Configuration
    config = Column(JSON, default=dict)  # Encrypted credentials and settings
    enabled = Column(Boolean, default=True, index=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    _metadata = Column("metadata", JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive config)."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, Enum) else self.type,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "enabled": self.enabled,
            "description": self.description,
            "metadata": self._metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

