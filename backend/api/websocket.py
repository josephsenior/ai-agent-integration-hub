"""WebSocket endpoints for real-time communication."""

import asyncio
import json
from typing import Any, Dict, List, Optional, Protocol

from fastapi import WebSocket, WebSocketDisconnect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis.asyncio as redis

from ..agents.base_agent import IntegrationAgent
from ..core.config import settings
from ..security.sessions import decode_session
from ..security.auth_state import AuthStateUnavailable, is_session_active
from ..services.redis_service import redis_service


# Protocol for agent interface
class AgentProtocol(Protocol):
    """Protocol for agent interface."""

    async def process(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
        """Process a message and return response."""
        ...


# Store active WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._agent: Optional[AgentProtocol] = None

    @property
    def agent(self) -> AgentProtocol:
        """Lazy initialization of agent."""
        if self._agent is None:
            try:
                self._agent = IntegrationAgent()
            except Exception as e:
                # If agent initialization fails, create a dummy agent that returns error messages
                print(f"Warning: Failed to initialize agent: {e}")
                # Create a simple fallback agent
                class FallbackAgent:
                    async def process(self, message: str, context: Optional[dict[str, Any]] = None) -> str:
                        return f"Agent initialization error: {str(e)}. Please check your GEMINI_API_KEY and dependencies."
                self._agent = FallbackAgent()
        return self._agent

    async def connect(self, websocket: WebSocket) -> None:
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """Broadcast message to all connected clients."""
        disconnected: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def process_message(self, websocket: WebSocket, data: Dict[str, Any]) -> None:
        """Process incoming message and send response."""
        try:
            message_text = data.get("message", "")
            context: dict[str, Any] = data.get("context", {})

            # Process with agent
            response = await self.agent.process(message_text, context)

            # Send response
            response_data = {
                "type": "agent_response",
                "message": message_text,
                "response": response,
                "timestamp": asyncio.get_event_loop().time(),
            }

            await self.send_personal_message(json.dumps(response_data), websocket)

            # Publish to Redis for other services
            await redis_service.publish_event(
                "websocket:message", {"message": message_text, "response": response}
            )

        except Exception as e:
            error_response = {"type": "error", "error": str(e)}
            await self.send_personal_message(json.dumps(error_response), websocket)


# Lazy initialization - only create manager when needed
_manager: Optional[ConnectionManager] = None

def get_manager() -> ConnectionManager:
    """Get or create the connection manager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager

manager = get_manager()


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Authenticate the browser WebSocket with its operator session cookie."""
    allowed_origins = {
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    }
    origin = websocket.headers.get("origin")
    if not origin or origin not in allowed_origins:
        await websocket.close(code=4403, reason="Origin not allowed")
        return
    claims = decode_session(
        websocket.cookies.get("hub_session"),
        settings.session_secret_key,
        settings.session_ttl_seconds,
    )
    if not claims or claims.get("username") != settings.operator_username:
        await websocket.close(code=4401, reason="Operator login required")
        return
    session_id = claims.get("sid")
    if not isinstance(session_id, str):
        await websocket.close(code=4401, reason="Operator session is invalid")
        return
    try:
        if not await is_session_active(session_id, settings.operator_username or ""):
            await websocket.close(code=4401, reason="Operator session has been revoked")
            return
    except AuthStateUnavailable:
        await websocket.close(code=1013, reason="Authentication state unavailable")
        return

    await websocket.accept()
    manager.active_connections.append(websocket)

    try:
        # Subscribe to Redis events
        pubsub: Any = None
        if redis_service.redis_client:
            candidate = redis_service.redis_client.pubsub()
            if candidate is not None:
                pubsub = candidate
                await pubsub.subscribe("agent:response")

        # Start listening for Redis events in background
        redis_task: Optional[asyncio.Task[None]] = None
        if pubsub:

            async def listen_redis() -> None:
                while True:
                    try:
                        message = await pubsub.get_message(
                            ignore_subscribe_messages=True
                        )
                        if message:
                            await manager.send_personal_message(
                                json.dumps(
                                    {
                                        "type": "event",
                                        "data": json.loads(message["data"]),
                                    }
                                ),
                                websocket,
                            )
                    except Exception as e:
                        print(f"Redis listener error: {e}")
                        break

            # Start Redis listener
            redis_task = asyncio.create_task(listen_redis())

        # Listen for WebSocket messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                if message_data.get("type") == "message":
                    await manager.process_message(websocket, message_data)
                elif message_data.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}), websocket
                    )

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "error": "Invalid JSON"}), websocket
                )

        # Cleanup
        if redis_task:
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
        if pubsub:
            await pubsub.unsubscribe("agent:response")
            await pubsub.close()

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
