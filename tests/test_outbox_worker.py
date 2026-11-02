"""Tests for durable event processing and delivery."""

from datetime import datetime, timedelta
from typing import Any, Optional

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.core.database import Base
from backend.models.events import InboxEvent, OutboxEvent
from backend.models.message import Message, MessageChannel, MessageStatus
from backend.services.outbox_worker import OutboxWorker


class FakeAgent:
    async def process(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
        return f"reply: {message}"


@pytest_asyncio.fixture
async def session_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'outbox.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def add_inbound_message(session_factory, *, max_attempts: int = 5) -> str:
    message_id = "message-1"
    async with session_factory() as session:
        message = Message(
            id=message_id,
            channel=MessageChannel.SLACK,
            content="hello",
            channel_id="channel-1",
            status=MessageStatus.PENDING,
        )
        session.add(message)
        session.add(
            InboxEvent(
                provider="slack",
                provider_event_id="event-1",
                message_id=message_id,
            )
        )
        session.add(
            OutboxEvent(
                event_type="process_message",
                aggregate_id=message_id,
                payload={"message_id": message_id},
                max_attempts=max_attempts,
            )
        )
        await session.commit()
    return message_id


@pytest.mark.asyncio
async def test_worker_processes_and_delivers_message(session_factory):
    await add_inbound_message(session_factory)
    delivered = []

    async def deliver(message: Message) -> dict[str, bool]:
        delivered.append(message.response)
        return {"success": True}

    worker = OutboxWorker(
        session_factory=session_factory,
        agent=FakeAgent(),
        delivery_handler=deliver,
    )

    assert await worker.process_one()
    async with session_factory() as session:
        message = await session.get(Message, "message-1")
        events = (await session.execute(select(OutboxEvent).order_by(OutboxEvent.event_type))).scalars().all()
        assert message.status == MessageStatus.COMPLETED
        assert message.response == "reply: hello"
        assert [event.event_type for event in events] == ["deliver_response", "process_message"]
        assert all(event.status == "completed" if event.event_type == "process_message" else event.status == "pending" for event in events)

    assert await worker.process_one()
    async with session_factory() as session:
        message = await session.get(Message, "message-1")
        delivery = await session.execute(
            select(OutboxEvent).where(OutboxEvent.event_type == "deliver_response")
        )
        assert delivered == ["reply: hello"]
        assert message.status == MessageStatus.DELIVERED
        assert delivery.scalar_one().status == "completed"


@pytest.mark.asyncio
async def test_worker_dead_letters_after_max_attempts(session_factory):
    await add_inbound_message(session_factory, max_attempts=1)

    class FailingAgent:
        async def process(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
            raise RuntimeError("model unavailable")

    worker = OutboxWorker(session_factory=session_factory, agent=FailingAgent())
    assert await worker.process_one()

    async with session_factory() as session:
        event = await session.execute(select(OutboxEvent))
        message = await session.get(Message, "message-1")
        assert event.scalar_one().status == "dead"
        assert message.status == MessageStatus.FAILED


@pytest.mark.asyncio
async def test_worker_retries_failed_event_with_backoff(session_factory):
    await add_inbound_message(session_factory)

    class FailingAgent:
        async def process(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
            raise RuntimeError("temporary failure")

    worker = OutboxWorker(session_factory=session_factory, agent=FailingAgent())
    assert await worker.process_one()

    async with session_factory() as session:
        result = await session.execute(select(OutboxEvent))
        event = result.scalar_one()
        assert event.status == "pending"
        assert event.last_error == "RuntimeError"
        assert event.available_at >= datetime.utcnow() + timedelta(milliseconds=800)
