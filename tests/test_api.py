"""Tests for API endpoints."""

import hashlib
import hmac
import time

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.api.main import app, verify_discord_request, verify_slack_request
from backend.models.events import InboxEvent, OutboxEvent
from backend.models.message import Message, MessageStatus, MessageChannel
from backend.core.config import settings
from backend.security.passwords import hash_password, verify_password
import backend.api.main as api_main

client = TestClient(app)


def test_slack_signature_verification(monkeypatch):
    monkeypatch.setattr(settings, "slack_signing_secret", "test-signing-secret")
    timestamp = str(int(time.time()))
    body = b'{"type":"event_callback"}'
    basestring = b"v0:" + timestamp.encode() + b":" + body
    signature = "v0=" + hmac.new(
        b"test-signing-secret", basestring, hashlib.sha256
    ).hexdigest()

    assert verify_slack_request(body, timestamp, signature)
    assert not verify_slack_request(body, timestamp, "v0=invalid")
    assert not verify_slack_request(body, str(int(timestamp) - 301), signature)


def test_discord_signature_verification(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    monkeypatch.setattr(settings, "discord_public_key", public_key.hex())
    timestamp = str(int(time.time()))
    body = b'{"type":1}'
    signature = private_key.sign(timestamp.encode() + body).hex()

    assert verify_discord_request(body, timestamp, signature)
    assert not verify_discord_request(body, timestamp, "00" * 64)
    assert not verify_discord_request(body, str(int(timestamp) - 301), signature)


@pytest.mark.api
class TestRootEndpoints:
    """Tests for root and health endpoints."""

    def test_root(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["name"] == "AI Agent Integration Hub"

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"


class TestOperatorLogin:
    def test_password_hash_and_login_cookie(self, monkeypatch, fake_auth_redis):
        password_hash = hash_password("a-long-test-password")
        assert verify_password("a-long-test-password", password_hash)
        assert not verify_password("wrong-password", password_hash)
        monkeypatch.setattr(settings, "operator_username", "operator-test")
        monkeypatch.setattr(settings, "operator_password_hash", password_hash)
        monkeypatch.setattr(settings, "session_secret_key", "long-test-session-signing-key")
        test_client = TestClient(app)

        response = test_client.post(
            "/api/v1/auth/login",
            json={"username": "operator-test", "password": "a-long-test-password"},
        )

        assert response.status_code == 200
        assert "httponly" in response.headers["set-cookie"].lower()
        assert test_client.get("/api/v1/auth/me").json() == {"username": "operator-test"}
        second_client = TestClient(app)
        second_client.cookies.update(test_client.cookies)
        logout = test_client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": test_client.cookies["hub_csrf"]},
        )
        assert logout.status_code == 200
        assert second_client.get("/api/v1/auth/me").status_code == 401

    def test_login_throttles_repeated_failures(self, monkeypatch, fake_auth_redis):
        monkeypatch.setattr(settings, "operator_username", "operator-test")
        monkeypatch.setattr(settings, "operator_password_hash", hash_password("a-long-test-password"))
        monkeypatch.setattr(settings, "session_secret_key", "long-test-session-signing-key")
        monkeypatch.setattr(api_main, "_LOGIN_MAX_FAILURES", 2)
        test_client = TestClient(app)

        for _ in range(2):
            response = test_client.post(
                "/api/v1/auth/login",
                json={"username": "operator-test", "password": "wrong-password"},
            )
            assert response.status_code == 401
        throttled = test_client.post(
            "/api/v1/auth/login",
            json={"username": "operator-test", "password": "wrong-password"},
        )
        assert throttled.status_code == 429
        assert int(throttled.headers["retry-after"]) > 0

    def test_auth_fails_closed_when_shared_store_is_unavailable(
        self, fake_auth_redis, auth_headers
    ):
        fake_auth_redis.available = False
        response = TestClient(app).get("/api/v1/events", headers=auth_headers)
        assert response.status_code == 503


@pytest.mark.api
class TestChatEndpoint:
    """Tests for chat endpoint."""

    def test_chat_without_auth(self):
        """Test chat endpoint without authentication."""
        response = client.post(
            "/api/v1/agents/chat", json={"message": "test", "channel": "api"}
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_chat_invalid_auth(self):
        """Test chat endpoint with invalid authentication."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.post(
            "/api/v1/agents/chat",
            json={"message": "test", "channel": "api"},
            headers=headers,
        )
        assert response.status_code == 401

    @patch("backend.api.main.get_agent")
    @patch("backend.api.main.redis_service")
    def test_chat_with_auth(
        self, mock_redis, mock_get_agent, override_get_db, mock_db_session, auth_headers
    ):
        """Test chat endpoint with authentication."""
        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value="Mocked agent response")
        mock_get_agent.return_value = mock_agent

        # Mock Redis
        mock_redis.publish_event = AsyncMock()

        response = client.post(
            "/api/v1/agents/chat",
            json={
                "message": "Hello",
                "channel": "api",
                "user_id": "test_user",
                "context": {"key": "value"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "message_id" in data
        assert "status" in data
        assert data["response"] == "Mocked agent response"
        assert data["status"] == "completed"
        assert data["channel"] == "api"

    @patch("backend.api.main.get_agent")
    @patch("backend.api.main.redis_service")
    def test_chat_with_context(
        self, mock_redis, mock_get_agent, override_get_db, mock_db_session, auth_headers
    ):
        """Test chat endpoint with context."""
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value="Context-aware response")
        mock_get_agent.return_value = mock_agent
        mock_redis.publish_event = AsyncMock()

        response = client.post(
            "/api/v1/agents/chat",
            json={
                "message": "Hello",
                "channel": "slack",
                "user_id": "user123",
                "context": {"user_name": "John", "channel_name": "general"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Verify context was passed to agent
        mock_agent.process.assert_called_once()
        call_args = mock_agent.process.call_args
        assert call_args[0][0] == "Hello"
        # Context is passed as keyword argument
        assert "context" in call_args[1] or (len(call_args[0]) > 1 and isinstance(call_args[0][1], dict))


@pytest.mark.api
class TestMessagesEndpoint:
    """Tests for messages endpoints."""

    def test_get_messages_unauthorized(self):
        """Test getting messages without auth."""
        response = client.get("/api/v1/messages")
        assert response.status_code == 401

    def test_get_messages_authorized(self, override_get_db, mock_db_session, auth_headers):
        """Test getting messages with auth."""
        response = client.get("/api/v1/messages", headers=auth_headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_messages_with_filters(
        self, override_get_db, mock_db_session, auth_headers
    ):
        """Test getting messages with filters."""
        response = client.get(
            "/api/v1/messages?channel=slack&status=completed&limit=10",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_message_by_id_not_found(
        self, override_get_db, mock_db_session, auth_headers
    ):
        """Test getting non-existent message."""
        response = client.get(
            "/api/v1/messages/non-existent-id", headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_message_by_id(
        self, override_get_db, mock_db_session, auth_headers, sample_message
    ):
        """Test getting message by ID."""
        # Mock the database query to return our sample message
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_message
        mock_db_session.execute.return_value = mock_result

        response = client.get(
            f"/api/v1/messages/{sample_message.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_message.id
        assert data["channel"] == sample_message.channel.value


@pytest.mark.api
class TestWebhookEndpoint:
    """Tests for webhook endpoint."""

    @patch("backend.api.main.get_agent")
    @patch("backend.api.main._send_response_to_channel")
    @patch("backend.integrations.slack.SlackIntegration")
    def test_receive_slack_webhook(
        self, mock_slack_class, mock_send_response, mock_get_agent, override_get_db, mock_db_session, slack_payload
    ):
        """Test receiving Slack webhook."""
        # Mock integration
        mock_integration = AsyncMock()
        mock_message = Message(
            id="test-id",
            channel=MessageChannel.SLACK,
            content="Hello from Slack",
            user_id="U123456",
            channel_id="C789012",
        )
        mock_integration.receive_message = AsyncMock(return_value=mock_message)
        mock_integration.send_message = AsyncMock()
        mock_slack_class.return_value = mock_integration
        mock_send_response.return_value = None

        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value="Agent response")
        mock_get_agent.return_value = mock_agent

        with patch("backend.api.main.verify_slack_request", return_value=True):
            response = client.post(
                "/api/v1/webhooks/slack",
                json=slack_payload,
            )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert "message_id" in data
        mock_get_agent.assert_not_called()
        saved = [call.args[0] for call in mock_db_session.add.call_args_list]
        assert any(isinstance(item, InboxEvent) for item in saved)
        assert any(isinstance(item, OutboxEvent) for item in saved)

    @patch("backend.api.main.get_agent")
    @patch("backend.integrations.discord.DiscordIntegration")
    def test_receive_discord_webhook(
        self, mock_discord_class, mock_get_agent, override_get_db, mock_db_session, discord_payload
    ):
        """Test receiving Discord webhook."""
        mock_integration = AsyncMock()
        mock_message = Message(
            id="test-id",
            channel=MessageChannel.DISCORD,
            content="Hello from Discord",
            user_id="123456789",
            channel_id="987654321",
        )
        mock_integration.receive_message = AsyncMock(return_value=mock_message)
        mock_integration.send_message = AsyncMock()
        mock_discord_class.return_value = mock_integration

        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value="Agent response")
        mock_get_agent.return_value = mock_agent

        with patch("backend.api.main.verify_discord_request", return_value=True):
            response = client.post(
                "/api/v1/webhooks/discord",
                json=discord_payload,
            )

        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        mock_get_agent.assert_not_called()

    @patch("backend.integrations.slack.SlackIntegration")
    def test_duplicate_slack_event_is_not_enqueued(
        self, mock_slack_class, override_get_db, mock_db_session, slack_payload
    ):
        mock_integration = AsyncMock()
        mock_integration.receive_message = AsyncMock(
            return_value=Message(
                id="duplicate-message",
                channel=MessageChannel.SLACK,
                content="Hello from Slack",
            )
        )
        mock_slack_class.return_value = mock_integration
        existing_event = InboxEvent(
            provider="slack",
            provider_event_id=slack_payload["event_id"],
            message_id="already-accepted",
        )
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_event

        with patch("backend.api.main.verify_slack_request", return_value=True):
            response = client.post("/api/v1/webhooks/slack", json=slack_payload)

        assert response.status_code == 202
        assert response.json() == {
            "status": "duplicate",
            "message_id": "already-accepted",
        }
        mock_db_session.add.assert_not_called()

    def test_receive_webhook_invalid_type(self, override_get_db, mock_db_session):
        """Test receiving webhook with invalid type."""
        response = client.post(
            "/api/v1/webhooks/invalid-type",
            json={"message": "test"},
        )

        assert response.status_code == 400
        assert "Unknown integration type" in response.json()["detail"]

    @pytest.mark.parametrize("integration_type", ["slack", "discord", "webhook"])
    def test_receive_webhook_requires_signature(
        self, integration_type, override_get_db, mock_db_session
    ):
        response = client.post(
            f"/api/v1/webhooks/{integration_type}",
            json={"message": "unsigned"},
        )

        assert response.status_code == 401

    @patch("backend.integrations.slack.SlackIntegration")
    def test_receive_webhook_ignores_bot_messages(
        self, mock_slack_class, override_get_db, mock_db_session
    ):
        """Test that bot messages are ignored."""
        mock_integration = AsyncMock()
        mock_integration.receive_message = AsyncMock(return_value=None)
        mock_slack_class.return_value = mock_integration

        payload = {
            "event": {
                "type": "message",
                "text": "Bot message",
                "bot_id": "B123456",
            }
        }

        with patch("backend.api.main.verify_slack_request", return_value=True):
            response = client.post("/api/v1/webhooks/slack", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "ignored"
