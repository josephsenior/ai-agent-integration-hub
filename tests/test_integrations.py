"""Tests for integration adapters."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.integrations.slack import SlackIntegration
from backend.integrations.discord import DiscordIntegration
from backend.integrations.email import EmailIntegration
from backend.integrations.webhook import WebhookIntegration
from backend.models.message import MessageChannel


@pytest.mark.integration_adapter
class TestSlackIntegration:
    """Tests for SlackIntegration."""

    @patch("backend.integrations.slack.WebClient")
    def test_slack_integration_initialization(self, mock_webclient):
        """Test SlackIntegration initialization."""
        config = {"bot_token": "xoxb-test-token"}
        integration = SlackIntegration(config)

        assert integration.config == config
        mock_webclient.assert_called_once()

    @patch("backend.integrations.slack.WebClient")
    @pytest.mark.asyncio
    async def test_slack_send_message(self, mock_webclient):
        """Test sending message via Slack."""
        # Create a mock response that supports both dict access and .data attribute
        class MockSlackResponse:
            def __init__(self):
                self._dict = {"ts": "1234567890.123456", "channel": "C789012"}
                self.data = {}
            
            def __getitem__(self, key):
                return self._dict[key]
        
        mock_client = MagicMock()
        mock_response = MockSlackResponse()
        mock_client.chat_postMessage.return_value = mock_response
        mock_webclient.return_value = mock_client

        integration = SlackIntegration({"bot_token": "xoxb-test"})
        result = await integration.send_message(
            content="Test message", channel_id="C789012"
        )

        assert result["success"] is True
        assert "message_id" in result
        mock_client.chat_postMessage.assert_called_once()

    @patch("backend.integrations.slack.WebClient")
    @pytest.mark.asyncio
    async def test_slack_receive_message(self, mock_webclient):
        """Test receiving message from Slack."""
        payload = {
            "event": {
                "type": "message",
                "text": "Hello from Slack",
                "user": "U123456",
                "channel": "C789012",
                "ts": "1234567890.123456",
            }
        }

        integration = SlackIntegration({})
        message = await integration.receive_message(payload)

        assert message is not None
        assert message.channel == MessageChannel.SLACK
        assert message.content == "Hello from Slack"
        assert message.user_id == "U123456"
        assert message.channel_id == "C789012"

    @patch("backend.integrations.slack.WebClient")
    @pytest.mark.asyncio
    async def test_slack_receive_message_skips_bot(self, mock_webclient):
        """Test that bot messages are skipped."""
        payload = {
            "event": {
                "type": "message",
                "text": "Bot message",
                "bot_id": "B123456",
            }
        }

        integration = SlackIntegration({})
        message = await integration.receive_message(payload)

        assert message is None

    @patch("backend.integrations.slack.WebClient")
    @pytest.mark.asyncio
    async def test_slack_validate_config(self, mock_webclient):
        """Test Slack configuration validation."""
        mock_client = MagicMock()
        mock_client.auth_test.return_value = {"ok": True}
        mock_webclient.return_value = mock_client

        integration = SlackIntegration({})
        result = await integration.validate_config()

        assert result is True
        mock_client.auth_test.assert_called_once()


@pytest.mark.integration_adapter
class TestDiscordIntegration:
    """Tests for DiscordIntegration."""

    @patch("backend.integrations.discord.commands.Bot")
    def test_discord_integration_initialization(self, mock_bot):
        """Test DiscordIntegration initialization."""
        config = {"bot_token": "discord-test-token"}
        integration = DiscordIntegration(config)

        assert integration.config == config
        assert integration.token == "discord-test-token"

    @pytest.mark.asyncio
    async def test_discord_receive_message(self):
        """Test receiving message from Discord."""
        payload = {
            "content": "Hello from Discord",
            "author": {"id": "123456789", "username": "testuser"},
            "channel_id": "987654321",
        }

        integration = DiscordIntegration({"bot_token": "test-token"})
        message = await integration.receive_message(payload)

        assert message is not None
        assert message.channel == MessageChannel.DISCORD
        assert message.content == "Hello from Discord"
        assert message.user_id == "123456789"


@pytest.mark.integration_adapter
class TestEmailIntegration:
    """Tests for EmailIntegration."""

    @patch("backend.integrations.email.aiosmtplib.send")
    @pytest.mark.asyncio
    async def test_email_send_message(self, mock_send):
        """Test sending email."""
        mock_send.return_value = None  # aiosmtplib.send doesn't return anything on success
        
        config = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@example.com",
            "smtp_password": "password",
            "from_email": "test@example.com",
        }

        integration = EmailIntegration(config)
        result = await integration.send_message(
            content="Test email body",
            channel_id="recipient@example.com",
            metadata={"subject": "Test Subject"},
        )

        assert result["success"] is True
        assert "recipient" in result
        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_receive_message(self):
        """Test receiving email."""
        payload = {
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "Email content",
            "text": "Email content",
        }

        integration = EmailIntegration({})
        message = await integration.receive_message(payload)

        assert message is not None
        assert message.channel == MessageChannel.EMAIL
        assert message.content == "Email content"
        assert message.user_id == "sender@example.com"


@pytest.mark.integration_adapter
class TestWebhookIntegration:
    """Tests for WebhookIntegration."""

    @pytest.mark.asyncio
    async def test_webhook_receive_message(self):
        """Test receiving webhook."""
        payload = {
            "message": "Webhook message",
            "user_id": "webhook-user",
            "channel_id": "webhook-channel",
        }

        integration = WebhookIntegration({})
        message = await integration.receive_message(payload)

        assert message is not None
        assert message.channel == MessageChannel.WEBHOOK
        assert message.content == "Webhook message"

    @patch("backend.integrations.webhook.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_webhook_send_message(self, mock_httpx):
        """Test sending webhook."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_httpx.return_value.__aenter__.return_value = mock_client

        integration = WebhookIntegration({})
        result = await integration.send_message(
            content="Webhook payload",
            channel_id="https://example.com/webhook",
        )

        assert result["success"] is True
        mock_client.post.assert_called_once()
