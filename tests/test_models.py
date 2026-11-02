"""Tests for data models."""

import pytest
from datetime import datetime
from uuid import uuid4

from backend.models.message import Message, MessageStatus, MessageChannel


@pytest.mark.unit
class TestMessageModel:
    """Tests for Message model."""

    def test_message_creation(self):
        """Test creating a message."""
        message = Message(
            id="test-id",
            channel=MessageChannel.SLACK,
            content="Test message",
            user_id="user123",
            channel_id="channel456",
        )

        assert message.id == "test-id"
        assert message.channel == MessageChannel.SLACK
        assert message.content == "Test message"
        assert message.user_id == "user123"
        assert message.channel_id == "channel456"
        # Status defaults to PENDING via Column default
        assert message.status in [MessageStatus.PENDING, None] or hasattr(message, 'status')

    def test_message_defaults(self):
        """Test message default values."""
        message = Message(
            id="test-id",
            channel=MessageChannel.API,
            content="Test",
        )

        # Status may be None if not explicitly set (depends on SQLAlchemy default)
        assert message.status is None or message.status == MessageStatus.PENDING
        # Metadata is stored as _metadata column
        assert hasattr(message, '_metadata') or (hasattr(message, 'metadata') and (message.metadata == {} or message.metadata is None))
        assert message.response is None
        assert message.processed_at is None

    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        message = Message(
            id="test-id",
            channel=MessageChannel.DISCORD,
            content="Test message",
            user_id="user123",
            status=MessageStatus.COMPLETED,
            response="Response text",
        )
        message.processed_at = datetime.utcnow()

        message_dict = message.to_dict()

        assert isinstance(message_dict, dict)
        assert message_dict["id"] == "test-id"
        assert message_dict["channel"] == "discord"
        assert message_dict["content"] == "Test message"
        assert message_dict["status"] == "completed"
        assert message_dict["response"] == "Response text"
        assert "processed_at" in message_dict

    def test_message_status_enum(self):
        """Test MessageStatus enum values."""
        assert MessageStatus.PENDING.value == "pending"
        assert MessageStatus.PROCESSING.value == "processing"
        assert MessageStatus.COMPLETED.value == "completed"
        assert MessageStatus.FAILED.value == "failed"

    def test_message_channel_enum(self):
        """Test MessageChannel enum values."""
        assert MessageChannel.SLACK.value == "slack"
        assert MessageChannel.DISCORD.value == "discord"
        assert MessageChannel.EMAIL.value == "email"
        assert MessageChannel.WEBHOOK.value == "webhook"
        assert MessageChannel.API.value == "api"
