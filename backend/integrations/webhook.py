"""Webhook integration adapter."""

import hashlib
import hmac
import json
from typing import Any, Dict, Optional

import httpx

from ..core.config import settings
from ..models.message import Message, MessageChannel
from .base import BaseIntegration


class WebhookIntegration(BaseIntegration):
    """Webhook integration adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url")
        self.secret = config.get("secret") or settings.webhook_secret
    
    async def send_message(
        self,
        content: str,
        channel_id: str,  # This is the webhook URL or endpoint
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message via webhook."""
        try:
            payload = {
                "message": content,
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            # Add signature if secret is configured
            headers = {"Content-Type": "application/json"}
            if self.secret:
                signature = self._generate_signature(payload)
                headers["X-Webhook-Signature"] = signature
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    channel_id or self.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Parse webhook payload into Message."""
        # Verify signature if present
        signature = payload.get("_signature")
        if signature and self.secret:
            if not self._verify_signature(payload, signature):
                raise ValueError("Invalid webhook signature")
        
        content = payload.get("message", payload.get("text", json.dumps(payload)))
        user_id = payload.get("user_id", payload.get("sender_id"))
        
        message = Message(
            channel=MessageChannel.WEBHOOK,
            content=content,
            user_id=str(user_id) if user_id else None,
            channel_id=payload.get("channel_id", payload.get("endpoint")),
            metadata={
                "source": payload.get("source"),
                "event_type": payload.get("event_type"),
                "raw_payload": payload
            }
        )
        
        return message
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """Generate HMAC signature for webhook."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature."""
        expected_signature = self._generate_signature(payload)
        return hmac.compare_digest(expected_signature, signature)
    
    async def validate_config(self) -> bool:
        """Validate webhook configuration."""
        return self.webhook_url is not None or self.secret is not None
    
    def get_channel_type(self) -> MessageChannel:
        """Get channel type."""
        return MessageChannel.WEBHOOK

