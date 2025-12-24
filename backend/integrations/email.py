"""Email integration adapter."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import aiosmtplib

from ..core.config import settings
from ..models.message import Message, MessageChannel
from .base import BaseIntegration


class EmailIntegration(BaseIntegration):
    """Email integration adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get("smtp_host") or settings.smtp_host
        self.smtp_port = config.get("smtp_port") or settings.smtp_port
        self.smtp_user = config.get("smtp_user") or settings.smtp_user
        self.smtp_password = config.get("smtp_password") or settings.smtp_password
        self.from_email = config.get("from_email") or settings.smtp_from_email
    
    async def send_message(
        self,
        content: str,
        channel_id: str,  # This is the recipient email address
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email message."""
        try:
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = channel_id
            message["Subject"] = metadata.get("subject", "AI Agent Response") if metadata else "AI Agent Response"
            
            message.attach(MIMEText(content, "plain"))
            
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True
            )
            
            return {
                "success": True,
                "message_id": f"email_{channel_id}",
                "recipient": channel_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Parse email payload into Message."""
        # Email parsing would typically come from an email webhook or IMAP
        content = payload.get("body", payload.get("text", ""))
        from_email = payload.get("from", payload.get("sender", ""))
        subject = payload.get("subject", "")
        
        message = Message(
            channel=MessageChannel.EMAIL,
            content=content,
            user_id=from_email,
            channel_id=from_email,  # Use email as channel_id
            metadata={
                "subject": subject,
                "to": payload.get("to"),
                "raw_payload": payload
            }
        )
        
        return message
    
    async def validate_config(self) -> bool:
        """Validate email configuration."""
        return all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
            self.from_email
        ])
    
    def get_channel_type(self) -> MessageChannel:
        """Get channel type."""
        return MessageChannel.EMAIL

