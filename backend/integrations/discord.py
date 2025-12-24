"""Discord integration adapter."""

from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from ..core.config import settings
from ..models.message import Message, MessageChannel
from .base import BaseIntegration

# Check if discord.py is available
try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False


class DiscordIntegration(BaseIntegration):
    """Discord integration adapter."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not DISCORD_AVAILABLE:
            raise ImportError("discord.py is not installed. Install it with: pip install discord.py")
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(
            command_prefix=config.get("command_prefix", "!"),
            intents=intents
        )
        self.token = config.get("bot_token") or settings.discord_bot_token
    
    async def send_message(
        self,
        content: str,
        channel_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send message to Discord channel."""
        try:
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return {
                    "success": False,
                    "error": f"Channel {channel_id} not found"
                }
            
            message = await channel.send(content)
            
            return {
                "success": True,
                "message_id": str(message.id),
                "channel_id": str(channel.id),
                "data": {
                    "content": message.content,
                    "created_at": message.created_at.isoformat()
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Parse Discord message payload into Message."""
        # Discord messages come through bot events, not direct payloads
        # This would be called from bot event handlers
        content = payload.get("content", "")
        user_id = payload.get("author", {}).get("id")
        channel_id = payload.get("channel_id")
        
        message = Message(
            channel=MessageChannel.DISCORD,
            content=content,
            user_id=str(user_id) if user_id else None,
            channel_id=str(channel_id) if channel_id else None,
            metadata={
                "guild_id": payload.get("guild_id"),
                "message_id": payload.get("id"),
                "raw_payload": payload
            }
        )
        
        return message
    
    async def validate_config(self) -> bool:
        """Validate Discord configuration."""
        return self.token is not None and len(self.token) > 0
    
    def get_channel_type(self) -> MessageChannel:
        """Get channel type."""
        return MessageChannel.DISCORD
    
    async def start_bot(self):
        """Start Discord bot."""
        if self.token:
            await self.bot.start(self.token)
