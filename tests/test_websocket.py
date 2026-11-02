"""Tests for WebSocket functionality."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect

from backend.api.main import app
from backend.api.websocket import ConnectionManager, manager
from backend.core.config import settings
from backend.security.sessions import encode_session
from backend.security.auth_state import session_key


@pytest.mark.websocket
class TestConnectionManager:
    """Tests for ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()

        await manager.connect(mock_websocket)

        assert mock_websocket in manager.active_connections
        mock_websocket.accept.assert_called_once()

    def test_disconnect(self):
        """Test WebSocket disconnection."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)
        manager.active_connections.append(mock_websocket)

        manager.disconnect(mock_websocket)

        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending message to specific WebSocket."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        manager.active_connections.append(mock_websocket)

        await manager.send_personal_message("Test message", mock_websocket)

        mock_websocket.send_text.assert_called_once_with("Test message")

    @pytest.mark.asyncio
    async def test_send_personal_message_error(self):
        """Test error handling when sending message."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))
        manager.active_connections.append(mock_websocket)

        await manager.send_personal_message("Test message", mock_websocket)

        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting message to all connections."""
        manager = ConnectionManager()
        mock_ws1 = MagicMock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        manager.active_connections = [mock_ws1, mock_ws2]

        await manager.broadcast("Broadcast message")

        mock_ws1.send_text.assert_called_once_with("Broadcast message")
        mock_ws2.send_text.assert_called_once_with("Broadcast message")

    @pytest.mark.asyncio
    async def test_process_message(self):
        """Test processing incoming message."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        manager.active_connections.append(mock_websocket)

        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(return_value="Agent response")
        manager._agent = mock_agent

        # Mock Redis
        with patch("backend.api.websocket.redis_service") as mock_redis:
            mock_redis.publish_event = AsyncMock()

            data = {"message": "Hello", "context": {}}
            await manager.process_message(mock_websocket, data)

            mock_agent.process.assert_called_once_with("Hello", {})
            mock_websocket.send_text.assert_called_once()
            
            # Verify response format
            call_args = mock_websocket.send_text.call_args[0][0]
            response_data = json.loads(call_args)
            assert response_data["type"] == "agent_response"
            assert response_data["response"] == "Agent response"

    @pytest.mark.asyncio
    async def test_process_message_error(self):
        """Test error handling in process_message."""
        manager = ConnectionManager()
        mock_websocket = MagicMock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        manager.active_connections.append(mock_websocket)

        # Mock agent that raises error
        mock_agent = AsyncMock()
        mock_agent.process = AsyncMock(side_effect=Exception("Processing error"))
        manager._agent = mock_agent

        data = {"message": "Hello", "context": {}}
        await manager.process_message(mock_websocket, data)

        # Verify error response was sent
        call_args = mock_websocket.send_text.call_args[0][0]
        response_data = json.loads(call_args)
        assert response_data["type"] == "error"
        assert "error" in response_data


@pytest.mark.websocket
class TestWebSocketAuthentication:
    def _configure_session(self, monkeypatch, client, fake_auth_redis):
        monkeypatch.setattr(settings, "operator_username", "test-operator")
        monkeypatch.setattr(settings, "session_secret_key", "test-session-signing-secret")
        monkeypatch.setattr(settings, "cors_allowed_origins", "http://localhost:3000")
        session_id = "test-websocket-session"
        client.cookies.set("hub_session", encode_session(
            {"username": "test-operator", "csrf": "csrf-test", "sid": session_id},
            settings.session_secret_key,
        ))
        fake_auth_redis.data[session_key(session_id)] = "test-operator"

    def test_rejects_missing_session(self, monkeypatch, fake_auth_redis):
        monkeypatch.setattr(settings, "operator_username", "test-operator")
        monkeypatch.setattr(settings, "session_secret_key", "test-session-signing-secret")
        client = TestClient(app)

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws", headers={"origin": "http://localhost:3000"}):
                pass

    def test_rejects_untrusted_origin(self, monkeypatch, fake_auth_redis):
        client = TestClient(app)
        self._configure_session(monkeypatch, client, fake_auth_redis)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws", headers={"origin": "https://attacker.example"}):
                pass

    def test_accepts_operator_session(self, monkeypatch, fake_auth_redis):
        client = TestClient(app)
        self._configure_session(monkeypatch, client, fake_auth_redis)
        with client.websocket_connect("/ws", headers={"origin": "http://localhost:3000"}) as websocket:
            websocket.send_json({"type": "ping"})
            assert websocket.receive_json() == {"type": "pong"}

    def test_rejects_revoked_session(self, monkeypatch, fake_auth_redis):
        client = TestClient(app)
        self._configure_session(monkeypatch, client, fake_auth_redis)
        fake_auth_redis.data.pop(session_key("test-websocket-session"))
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws", headers={"origin": "http://localhost:3000"}):
                pass
