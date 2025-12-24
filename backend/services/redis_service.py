"""Redis service for message queuing and caching."""

import json
from typing import Any, Dict, Optional

import redis.asyncio as redis

from ..core.config import settings


class RedisService:
    """Redis service for queuing and caching."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def enqueue_message(self, queue_name: str, message: Dict[str, Any]) -> bool:
        """Add message to queue."""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.lpush(queue_name, json.dumps(message))
            return True
        except Exception as e:
            print(f"Error enqueueing message: {e}")
            return False
    
    async def dequeue_message(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Get message from queue."""
        if not self.redis_client:
            await self.connect()
        
        try:
            result = await self.redis_client.brpop(queue_name, timeout=timeout)
            if result:
                _, data = result
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error dequeueing message: {e}")
            return None
    
    async def publish_event(self, channel: str, event: Dict[str, Any]) -> int:
        """Publish event to channel."""
        if not self.redis_client:
            await self.connect()
        
        try:
            return await self.redis_client.publish(channel, json.dumps(event))
        except Exception as e:
            print(f"Error publishing event: {e}")
            return 0
    
    async def set_cache(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cache value."""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value) if not isinstance(value, str) else value
            )
            return True
        except Exception as e:
            print(f"Error setting cache: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value."""
        if not self.redis_client:
            await self.connect()
        
        try:
            value = await self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            print(f"Error getting cache: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete cache key."""
        if not self.redis_client:
            await self.connect()
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Error deleting cache: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()

