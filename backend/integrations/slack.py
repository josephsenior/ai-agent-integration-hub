"""Slack integration adapter."""

from typing import Any, Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..core.config import settings
from ..models.message import Message, MessageChannel
from .base import BaseIntegration


class SlackIntegration(BaseIntegration):
    """Slack integration adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = WebClient(token=config.get("bot_token") or settings.slack_bot_token)
    
    async def send_message(
        self,
        content: str,
        channel_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message to Slack channel."""
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=content,
                metadata=metadata or {}
            )
            
            return {
                "success": True,
                "message_id": response["ts"],
                "channel": response["channel"],
                "data": response.data
            }
        except SlackApiError as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": e.response["error"]
            }
    
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Parse Slack event payload into Message."""
        event = payload.get("event", {})
        
        # Skip bot messages
        if event.get("bot_id"):
            return None
        
        message = Message(
            channel=MessageChannel.SLACK,
            content=event.get("text", ""),
            user_id=event.get("user"),
            channel_id=event.get("channel"),
            metadata={
                "event_type": event.get("type"),
                "event_ts": event.get("ts"),
                "thread_ts": event.get("thread_ts"),
                "raw_payload": payload
            }
        )
        
        return message
    
    async def validate_config(self) -> bool:
        """Validate Slack configuration."""
        try:
            response = self.client.auth_test()
            return response["ok"]
        except Exception:
            return False
    
    def get_channel_type(self) -> MessageChannel:
        """Get channel type."""
        return MessageChannel.SLACK

