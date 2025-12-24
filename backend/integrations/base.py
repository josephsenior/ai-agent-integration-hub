"""Base integration adapter."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models.message import Message, MessageChannel


class BaseIntegration(ABC):
    """Base class for all integration adapters."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize integration with configuration."""
        self.config = config
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    async def send_message(
        self,
        content: str,
        channel_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message through this integration."""
        pass
    
    @abstractmethod
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Receive and parse a message from this integration."""
        pass
    
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate integration configuration."""
        pass
    
    @abstractmethod
    def get_channel_type(self) -> MessageChannel:
        """Get the message channel type for this integration."""
        pass

