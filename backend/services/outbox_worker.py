"""Poll and execute durable outbox work."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Protocol

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..integrations import DiscordIntegration, EmailIntegration, SlackIntegration, WebhookIntegration
from ..models.events import OutboxEvent
from ..models.message import Message, MessageChannel, MessageStatus


class Agent(Protocol):
    async def process(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
        """Generate a response for an accepted message."""


class OutboxWorker:
    """A lease-based worker with bounded retry and dead-letter handling."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
        agent: Optional[Agent] = None,
        delivery_handler: Optional[Callable[[Message], Any]] = None,
        poll_interval: float = 1.0,
        lease_seconds: int = 120,
    ) -> None:
        self.session_factory = session_factory
        self.agent = agent
        self.delivery_handler = delivery_handler
        self.poll_interval = poll_interval
        self.lease_seconds = lease_seconds

    async def process_one(self) -> bool:
        """Claim and process one eligible event; return whether work was found."""
        event_id = await self._claim_one()
        if event_id is None:
            return False

        try:
            await self._execute(event_id)
        except Exception as exc:
            await self._schedule_retry(event_id, exc)
        return True

    async def run_forever(self) -> None:
        """Poll until the process is cancelled."""
        while True:
            if not await self.process_one():
                await asyncio.sleep(self.poll_interval)

    async def _claim_one(self) -> Optional[str]:
        now = datetime.utcnow()
        eligible = or_(
            and_(OutboxEvent.status == "pending", OutboxEvent.available_at <= now),
            and_(
                OutboxEvent.status == "processing",
                OutboxEvent.locked_until.is_not(None),
                OutboxEvent.locked_until <= now,
            ),
        )

        async with self.session_factory() as session:
            result = await session.execute(
                select(OutboxEvent.id, OutboxEvent.status)
                .where(eligible)
                .order_by(OutboxEvent.available_at, OutboxEvent.created_at)
                .limit(1)
            )
            candidate = result.first()
            if candidate is None:
                return None

            claim = await session.execute(
                update(OutboxEvent)
                .where(OutboxEvent.id == candidate.id, eligible)
                .values(
                    status="processing",
                    attempts=OutboxEvent.attempts + 1,
                    locked_until=now + timedelta(seconds=self.lease_seconds),
                )
            )
            if claim.rowcount != 1:
                await session.rollback()
                return None
            await session.commit()
            return candidate.id

    async def _execute(self, event_id: str) -> None:
        async with self.session_factory() as session:
            event = await session.get(OutboxEvent, event_id)
            if event is None:
                return
            event_type = event.event_type
            message = await session.get(Message, event.aggregate_id)
            if message is None:
                raise LookupError("outbox message no longer exists")
            message_id = message.id
            content = message.content
            channel = message.channel
            channel_id = message.channel_id
            user_id = message.user_id
            metadata = message._metadata or {}
            existing_response = message.response

        if event_type == "process_message":
            if existing_response is None:
                agent = self.agent
                if agent is None:
                    from ..agents.base_agent import IntegrationAgent

                    agent = IntegrationAgent()
                response = await agent.process(content)
            else:
                response = existing_response

            async with self.session_factory() as session:
                event = await session.get(OutboxEvent, event_id)
                message = await session.get(Message, message_id)
                if event is None or message is None:
                    raise LookupError("outbox message no longer exists")
                message.status = MessageStatus.COMPLETED
                message.response = response
                message.processed_at = datetime.utcnow()
                message.response_metadata = {"model": settings.GEMINI_MODEL}
                event.status = "completed"
                event.locked_until = None
                event.processed_at = datetime.utcnow()
                if channel not in (MessageChannel.API, MessageChannel.WEBSOCKET) and channel_id:
                    session.add(
                        OutboxEvent(
                            event_type="deliver_response",
                            aggregate_id=message_id,
                            payload={"message_id": message_id},
                        )
                    )
                await session.commit()
            return

        if event_type == "deliver_response":
            if self.delivery_handler is not None:
                result = self.delivery_handler(message)
                if asyncio.iscoroutine(result):
                    result = await result
            else:
                result = await self._deliver(channel, channel_id, user_id, message.response, metadata)
            if isinstance(result, dict) and result.get("success") is False:
                raise RuntimeError("integration delivery failed")
            async with self.session_factory() as session:
                event = await session.get(OutboxEvent, event_id)
                message = await session.get(Message, message_id)
                if event is None or message is None:
                    raise LookupError("outbox message no longer exists")
                event.status = "completed"
                event.locked_until = None
                event.processed_at = datetime.utcnow()
                message.status = MessageStatus.DELIVERED
                await session.commit()
            return

        raise ValueError(f"unsupported outbox event type: {event_type}")

    async def _deliver(
        self,
        channel: Any,
        channel_id: Optional[str],
        user_id: Optional[str],
        response: Optional[str],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        if not channel_id or not response:
            return {"success": True}
        integration = None
        if channel == MessageChannel.SLACK:
            integration = SlackIntegration({})
        elif channel == MessageChannel.DISCORD:
            integration = DiscordIntegration({})
        elif channel == MessageChannel.EMAIL:
            integration = EmailIntegration({})
        elif channel == MessageChannel.WEBHOOK:
            integration = WebhookIntegration({})
        if integration is None:
            return {"success": True}
        return await integration.send_message(
            content=response,
            channel_id=channel_id,
            user_id=user_id,
            metadata=metadata,
        )

    async def _schedule_retry(self, event_id: str, exc: Exception) -> None:
        now = datetime.utcnow()
        async with self.session_factory() as session:
            event = await session.get(OutboxEvent, event_id)
            if event is None:
                return
            event.locked_until = None
            event.last_error = type(exc).__name__
            if event.attempts >= event.max_attempts:
                event.status = "dead"
                message = await session.get(Message, event.aggregate_id)
                if message is not None:
                    message.status = MessageStatus.FAILED
            else:
                event.status = "pending"
                delay = min(2 ** max(event.attempts - 1, 0), 300)
                event.available_at = now + timedelta(seconds=delay)
            await session.commit()
