"""Agent request and response models."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .message import MessageChannel


class AgentRequest(BaseModel):
    """Request model for agent interactions."""
    
    message: str = Field(..., description="User message to send to agent")
    channel: MessageChannel = Field(..., description="Communication channel")
    user_id: Optional[str] = Field(None, description="User identifier")
    channel_id: Optional[str] = Field(None, description="Channel identifier (Slack channel, Discord channel, etc.)")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    integration_id: Optional[str] = Field(None, description="Integration ID to use")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Request metadata")
    
    class Config:
        use_enum_values = True


class AgentResponse(BaseModel):
    """Response model from agent interactions."""
    
    message_id: str = Field(..., description="Message ID")
    response: str = Field(..., description="Agent response text")
    status: str = Field(..., description="Response status")
    channel: MessageChannel = Field(..., description="Communication channel")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Response metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        use_enum_values = True

