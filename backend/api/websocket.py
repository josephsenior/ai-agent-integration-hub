"""WebSocket endpoints for real-time communication."""

import asyncio
import json
from typing import Any, Dict, List

from fastapi import WebSocket, WebSocketDisconnect

from ..agents.base_agent import IntegrationAgent
from ..services.redis_service import redis_service


# Store active WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent = IntegrationAgent()
    
    async def connect(self, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def process_message(self, websocket: WebSocket, data: Dict[str, Any]):
        """Process incoming message and send response."""
        try:
            message_text = data.get("message", "")
            context = data.get("context", {})
            
            # Process with agent
            response = await self.agent.process(message_text, context)
            
            # Send response
            response_data = {
                "type": "agent_response",
                "message": message_text,
                "response": response,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await self.send_personal_message(
                json.dumps(response_data),
                websocket
            )
            
            # Publish to Redis for other services
            await redis_service.publish_event(
                "websocket:message",
                {
                    "message": message_text,
                    "response": response
                }
            )
        
        except Exception as e:
            error_response = {
                "type": "error",
                "error": str(e)
            }
            await self.send_personal_message(
                json.dumps(error_response),
                websocket
            )


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await manager.connect(websocket)
    
    try:
        # Subscribe to Redis events
        if redis_service.redis_client:
            pubsub = redis_service.redis_client.pubsub()
            await pubsub.subscribe("agent:response")
        else:
            pubsub = None
        
        # Start listening for Redis events in background
        redis_task = None
        if pubsub:
            async def listen_redis():
                while True:
                    try:
                        message = await pubsub.get_message(ignore_subscribe_messages=True)
                        if message:
                            await manager.send_personal_message(
                                json.dumps({
                                    "type": "event",
                                    "data": json.loads(message["data"])
                                }),
                                websocket
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
                        json.dumps({"type": "pong"}),
                        websocket
                    )
            
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "error": "Invalid JSON"}),
                    websocket
                )
        
        # Cleanup
        if redis_task:
            redis_task.cancel()
        if pubsub:
            await pubsub.unsubscribe("agent:response")
            await pubsub.close()
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)

