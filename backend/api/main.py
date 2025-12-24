"""FastAPI application and API routes."""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from fastapi import FastAPI as _FastAPI
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from fastapi.middleware.asyncexitstack import AsyncExitStackMiddleware


# Monkeypatch FastAPI.build_middleware_stack to handle both
# 2-item (cls, options) and 3-item (cls, args, kwargs) middleware iterables
def _patched_build_middleware_stack(self) -> "ASGIApp":
    debug = self.debug
    error_handler = None
    exception_handlers = {}

    for key, value in self.exception_handlers.items():
        if key in (500, Exception):
            error_handler = value
        else:
            exception_handlers[key] = value

    middleware = (
        [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
        + self.user_middleware
        + [
            Middleware(
                ExceptionMiddleware, handlers=exception_handlers, debug=debug
            ),
            Middleware(AsyncExitStackMiddleware),
        ]
    )

    app = self.router
    for item in reversed(middleware):
        parts = tuple(item)
        if len(parts) == 2:
            cls, options = parts
            app = cls(app=app, **(options or {}))
        elif len(parts) == 3:
            cls, args, kwargs = parts
            app = cls(app=app, *args, **(kwargs or {}))
        else:
            raise ValueError("Unsupported middleware format")
    return app


_FastAPI.build_middleware_stack = _patched_build_middleware_stack
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.base_agent import IntegrationAgent
from ..api.websocket import websocket_endpoint
from ..core.config import settings
from ..core.database import get_db, init_db
from ..integrations import (
    DiscordIntegration,
    EmailIntegration,
    SlackIntegration,
    WebhookIntegration,
)
from ..models.agent_request import AgentRequest, AgentResponse
from ..models.message import Message, MessageStatus
from ..services.redis_service import redis_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    await init_db()
    await redis_service.connect()
    yield
    # Shutdown
    await redis_service.disconnect()


middleware = [
    (
        CORSMiddleware,
        {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
    )
]

app = FastAPI(
    title="AI Agent Integration Hub",
    description="Unified API gateway for AI agent integrations",
    version="1.0.0",
    lifespan=lifespan,
    middleware=middleware,
)

# Initialize agent
agent = IntegrationAgent()


def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    """Verify API key from header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    # In production, validate against database or JWT
    if token != settings.api_secret_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Agent Integration Hub",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if redis_service.redis_client else "disconnected"
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/agents/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Send a message to an agent and get a response."""
    try:
        # Create message record
        message = Message(
            id=str(uuid.uuid4()),
            channel=request.channel,
            content=request.message,
            user_id=request.user_id,
            channel_id=request.channel_id,
            status=MessageStatus.PROCESSING,
            metadata=request.metadata or {}
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        # Process with agent
        context = request.context or {}
        response_text = await agent.process(request.message, context)
        
        # Update message with response
        message.status = MessageStatus.COMPLETED
        message.response = response_text
        message.processed_at = datetime.utcnow()
        message.response_metadata = {"model": "gpt-4"}
        
        await db.commit()
        
        # Send response through integration if channel_id is provided
        if request.channel_id:
            await _send_response_to_channel(
                request.channel,
                request.channel_id,
                response_text,
                request.user_id
            )
        
        # Publish event to Redis
        await redis_service.publish_event(
            "agent:response",
            {
                "message_id": message.id,
                "channel": request.channel,
                "response": response_text
            }
        )
        
        return AgentResponse(
            message_id=message.id,
            response=response_text,
            status=message.status.value,
            channel=request.channel,
            metadata=message.response_metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _send_response_to_channel(
    channel: str,
    channel_id: str,
    response: str,
    user_id: Optional[str] = None
):
    """Send response back through the integration channel."""
    try:
        integration = None
        
        if channel == "slack":
            integration = SlackIntegration({})
        elif channel == "discord":
            integration = DiscordIntegration({})
        elif channel == "email":
            integration = EmailIntegration({})
        elif channel == "webhook":
            integration = WebhookIntegration({})
        
        if integration:
            await integration.send_message(
                content=response,
                channel_id=channel_id,
                user_id=user_id
            )
    except Exception as e:
        print(f"Error sending response to channel: {e}")


@app.get("/api/v1/messages/{message_id}")
async def get_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get message by ID."""
    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return message.to_dict()


@app.get("/api/v1/messages")
async def list_messages(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """List messages with optional filters."""
    query = select(Message)
    
    if channel:
        query = query.where(Message.channel == channel)
    if status:
        query = query.where(Message.status == status)
    
    query = query.order_by(Message.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [msg.to_dict() for msg in messages]


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket_endpoint(websocket)


@app.post("/api/v1/webhooks/{integration_type}")
async def receive_webhook(
    integration_type: str,
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Receive webhook from external service."""
    try:
        integration = None
        
        if integration_type == "slack":
            integration = SlackIntegration({})
        elif integration_type == "discord":
            integration = DiscordIntegration({})
        elif integration_type == "email":
            integration = EmailIntegration({})
        elif integration_type == "webhook":
            integration = WebhookIntegration({})
        else:
            raise HTTPException(status_code=400, detail=f"Unknown integration type: {integration_type}")
        
        # Parse message from webhook
        message = await integration.receive_message(payload)
        
        if message:
            # Save message
            db.add(message)
            await db.commit()
            await db.refresh(message)
            
            # Process with agent
            response_text = await agent.process(message.content)
            
            # Update message
            message.status = MessageStatus.COMPLETED
            message.response = response_text
            message.processed_at = datetime.utcnow()
            
            await db.commit()
            
            # Send response back
            if message.channel_id:
                await integration.send_message(
                    content=response_text,
                    channel_id=message.channel_id,
                    user_id=message.user_id
                )
            
            return {"status": "processed", "message_id": message.id}
        
        return {"status": "ignored"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

