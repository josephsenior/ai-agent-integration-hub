"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from backend.core.database import get_db
from backend.api.main import app
from backend.models.message import Message, MessageStatus, MessageChannel
from backend.security.auth_state import (
    CHECK_THROTTLE_SCRIPT,
    RECORD_FAILURE_SCRIPT,
    session_key,
)
from backend.services.redis_service import redis_service


class FakeAuthRedis:
    """Small shared-state fake for auth endpoint and websocket tests."""

    def __init__(self):
        self.data = {}
        self.expiries = {}
        self.available = True

    async def ping(self):
        if not self.available:
            raise ConnectionError("fake Redis unavailable")
        return True

    def pubsub(self):
        return None

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value
        return True

    async def delete(self, key):
        existed = key in self.data
        self.data.pop(key, None)
        self.expiries.pop(key, None)
        return int(existed)

    async def eval(self, script, numkeys, *args):
        key = args[0]
        if script == CHECK_THROTTLE_SCRIPT:
            count = int(self.data.get(key, 0))
            ttl = self.expiries.get(key, 900)
            return [0, ttl] if count >= int(args[1]) else [1, 0]
        if script == RECORD_FAILURE_SCRIPT:
            count = int(self.data.get(key, 0)) + 1
            self.data[key] = count
            self.expiries.setdefault(key, int(args[1]))
            return [count, self.expiries[key]]
        raise AssertionError("Unexpected Redis auth script")


@pytest.fixture
def fake_auth_redis(monkeypatch):
    fake = FakeAuthRedis()
    monkeypatch.setattr(redis_service, "redis_client", fake)
    return fake


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    mock = AsyncMock()
    
    # Mock execute for queries
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock.execute.return_value = mock_result
    
    # Mock commit and refresh
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.add = MagicMock()
    
    return mock


@pytest.fixture
def override_get_db(mock_db_session):
    """Override database dependency for testing."""
    async def _get_db() -> AsyncGenerator:
        yield mock_db_session
    
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    return Message(
        id="test-message-id",
        channel=MessageChannel.API,
        content="Test message",
        user_id="test-user",
        channel_id="test-channel",
        status=MessageStatus.PROCESSING,
    )


@pytest.fixture
def mock_agent():
    """Create a mock agent."""
    mock = AsyncMock()
    mock.process = AsyncMock(return_value="Mocked agent response")
    return mock


@pytest.fixture
def mock_redis_service():
    """Create a mock Redis service."""
    mock = AsyncMock()
    mock.publish_event = AsyncMock()
    mock.redis_client = MagicMock()
    return mock


@pytest.fixture
def auth_headers(monkeypatch, fake_auth_redis):
    """Create a signed operator session for API tests."""
    import secrets
    from itsdangerous import URLSafeTimedSerializer
    from backend.core.config import settings

    monkeypatch.setattr(settings, "operator_username", "test-operator")
    from backend.security.passwords import hash_password
    monkeypatch.setattr(settings, "operator_password_hash", hash_password("test-password"))
    monkeypatch.setattr(settings, "session_secret_key", "test-session-secret-for-tests")
    csrf = secrets.token_urlsafe(24)
    signed = URLSafeTimedSerializer(
        settings.session_secret_key, salt="integration-hub-session-v1"
    ).dumps({"username": settings.operator_username, "csrf": csrf, "sid": "test-session-id"})
    fake_auth_redis.data[session_key("test-session-id")] = settings.operator_username
    return {
        "Cookie": f"hub_session={signed}; hub_csrf={csrf}",
        "X-CSRF-Token": csrf,
    }


@pytest.fixture
def slack_payload():
    """Sample Slack webhook payload."""
    return {
        "event_id": "Ev123456",
        "type": "event_callback",
        "event": {
            "type": "message",
            "text": "Hello from Slack",
            "user": "U123456",
            "channel": "C789012",
            "ts": "1234567890.123456",
        },
    }


@pytest.fixture
def discord_payload():
    """Sample Discord webhook payload."""
    return {
        "id": "123456789012345678",
        "content": "Hello from Discord",
        "author": {"id": "123456789", "username": "testuser"},
        "channel_id": "987654321",
        "guild_id": "111222333",
    }


@pytest.fixture
def email_payload():
    """Sample email webhook payload."""
    return {
        "from": "sender@example.com",
        "to": "recipient@example.com",
        "subject": "Test Email",
        "body": "Hello from email",
        "text": "Hello from email",
    }
