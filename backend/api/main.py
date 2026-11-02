"""FastAPI application and API routes."""

import hashlib
import hmac
import json
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional, Protocol, Union

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware import Middleware
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


# Protocol for agent interface
class AgentProtocol(Protocol):
    """Protocol for agent interface."""

    async def process(self, message: str, context: Optional[dict] = None) -> str:
        """Process a message and return response."""
        ...


from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402

from ..agents.base_agent import IntegrationAgent  # noqa: E402
from ..api.websocket import websocket_endpoint  # noqa: E402
from ..core.config import settings  # noqa: E402
from ..core.database import get_db, init_db  # noqa: E402
from ..integrations import (  # noqa: E402
    DiscordIntegration,
    EmailIntegration,
    SlackIntegration,
    WebhookIntegration,
)
from ..models.agent_request import AgentRequest, AgentResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from ..models.events import InboxEvent, OutboxEvent  # noqa: E402
from ..models.message import Message, MessageStatus  # noqa: E402
from ..security.passwords import verify_password  # noqa: E402
from ..security.sessions import decode_session, encode_session  # noqa: E402
from ..security.auth_state import (  # noqa: E402
    AuthStateUnavailable,
    check_login_throttle,
    clear_login_failures,
    record_login_failure,
    register_session,
    revoke_session,
    is_session_active,
)
from ..services.redis_service import redis_service  # noqa: E402


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
    Middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(
    title="AI Agent Integration Hub",
    description="Unified API gateway for AI agent integrations",
    version="1.0.0",
    lifespan=lifespan,
    middleware=middleware,
)

# Lazy agent initialization with safe fallback
_agent_instance: Optional[AgentProtocol] = None


def get_agent() -> AgentProtocol:
    """Get or create the agent instance (lazy initialization).

    If the real IntegrationAgent fails to initialize (e.g. missing or
    incompatible LLM dependencies), fall back to a lightweight stub agent
    that simply returns an informative error message instead of breaking
    the entire API with 500 errors. This is especially useful in dev/demo
    environments.
    """
    global _agent_instance
    if _agent_instance is None:
        try:
            _agent_instance = IntegrationAgent()
        except Exception as e:  # pragma: no cover - environment dependent
            print(f"Warning: Failed to initialize IntegrationAgent: {e}")

            class FallbackAgent:
                async def process(self, message: str, context: Optional[dict] = None) -> str:
                    return (
                        "Agent initialization error. The LLM backend is not available "
                        "or dependencies are misconfigured. Original error: "
                        f"{str(e)}"
                    )

            _agent_instance = FallbackAgent()
    return _agent_instance



class OperatorLogin(BaseModel):
    username: str
    password: str


_LOGIN_WINDOW_SECONDS = 900
_LOGIN_MAX_FAILURES = 5


async def verify_operator_session(request: Request) -> str:
    """Validate signed operator cookie and CSRF token for unsafe requests."""
    token = request.cookies.get("hub_session")
    if not token:
        raise HTTPException(status_code=401, detail="Operator login required")
    claims = decode_session(token, settings.session_secret_key, settings.session_ttl_seconds)
    if claims is None:
        raise HTTPException(status_code=401, detail="Operator session is invalid or expired")
    username = claims.get("username")
    session_id = claims.get("sid")
    if not username or username != settings.operator_username or not isinstance(session_id, str):
        raise HTTPException(status_code=401, detail="Operator session is invalid")
    try:
        if not await is_session_active(session_id, username):
            raise HTTPException(status_code=401, detail="Operator session has been revoked")
    except AuthStateUnavailable:
        raise HTTPException(status_code=503, detail="Authentication state is temporarily unavailable")
    request.state.operator_session_id = session_id

    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        csrf_cookie = request.cookies.get("hub_csrf", "")
        csrf_header = request.headers.get("X-CSRF-Token", "")
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(csrf_cookie, csrf_header):
            raise HTTPException(status_code=403, detail="CSRF validation failed")
        if not secrets.compare_digest(str(claims.get("csrf", "")), csrf_cookie):
            raise HTTPException(status_code=403, detail="CSRF validation failed")
    return username


@app.post("/api/v1/auth/login")
async def operator_login(
    credentials: OperatorLogin, request: Request, response: Response
) -> dict[str, str]:
    """Issue a short-lived, HttpOnly operator session."""
    if not settings.operator_username or not settings.operator_password_hash or not settings.session_secret_key:
        raise HTTPException(status_code=503, detail="Operator login is not configured")
    client_key = request.client.host if request.client else "unknown"
    try:
        retry_after = await check_login_throttle(client_key, _LOGIN_MAX_FAILURES)
    except AuthStateUnavailable:
        raise HTTPException(status_code=503, detail="Authentication state is temporarily unavailable")
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many failed sign-in attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    username_valid = secrets.compare_digest(credentials.username.encode(), settings.operator_username.encode())
    password_valid = verify_password(credentials.password, settings.operator_password_hash)
    if not username_valid or not password_valid:
        try:
            failures, retry_after = await record_login_failure(client_key, _LOGIN_WINDOW_SECONDS)
        except AuthStateUnavailable:
            raise HTTPException(status_code=503, detail="Authentication state is temporarily unavailable")
        if failures > _LOGIN_MAX_FAILURES:
            raise HTTPException(
                status_code=429,
                detail="Too many failed sign-in attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        await clear_login_failures(client_key)
    except AuthStateUnavailable:
        raise HTTPException(status_code=503, detail="Authentication state is temporarily unavailable")

    csrf_token = secrets.token_urlsafe(32)
    session_id = secrets.token_urlsafe(32)
    try:
        await register_session(session_id, settings.operator_username, settings.session_ttl_seconds)
    except AuthStateUnavailable:
        raise HTTPException(status_code=503, detail="Authentication state is temporarily unavailable")
    session_token = encode_session(
        {"username": settings.operator_username, "csrf": csrf_token, "sid": session_id},
        settings.session_secret_key,
    )
    cookie_options = {
        "max_age": settings.session_ttl_seconds,
        "httponly": True,
        "secure": settings.session_cookie_secure,
        "samesite": "strict",
        "path": "/",
    }
    response.set_cookie("hub_session", session_token, **cookie_options)
    response.set_cookie("hub_csrf", csrf_token, httponly=False, **{k: v for k, v in cookie_options.items() if k != "httponly"})
    return {"username": settings.operator_username}


@app.get("/api/v1/auth/me")
async def operator_me(username: str = Depends(verify_operator_session)) -> dict[str, str]:
    return {"username": username}


@app.post("/api/v1/auth/logout")
async def operator_logout(
    request: Request, response: Response, _: str = Depends(verify_operator_session)
) -> dict[str, str]:
    try:
        await revoke_session(request.state.operator_session_id)
    except AuthStateUnavailable:
        raise HTTPException(status_code=503, detail="Authentication state is temporarily unavailable")
    response.delete_cookie("hub_session", path="/")
    response.delete_cookie("hub_csrf", path="/")
    return {"status": "logged_out"}


def verify_slack_request(body: bytes, timestamp: Optional[str], signature: Optional[str]) -> bool:
    """Verify Slack's signed request and reject replayed requests."""
    secret = settings.slack_signing_secret
    if not secret or not timestamp or not signature:
        return False
    try:
        request_time = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - request_time) > 300:
        return False

    basestring = b"v0:" + timestamp.encode("ascii") + b":" + body
    expected = "v0=" + hmac.new(
        secret.encode("utf-8"), basestring, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_discord_request(
    body: bytes, timestamp: Optional[str], signature: Optional[str]
) -> bool:
    """Verify Discord's Ed25519 signature and limit replay of old requests."""
    public_key = settings.discord_public_key
    if not public_key or not timestamp or not signature:
        return False
    try:
        request_time = int(timestamp)
        if abs(time.time() - request_time) > 300:
            return False
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key))
        key.verify(bytes.fromhex(signature), timestamp.encode("ascii") + body)
        return True
    except (ValueError, InvalidSignature, UnicodeEncodeError):
        return False


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"name": "AI Agent Integration Hub", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    redis_status = "connected" if redis_service.redis_client else "disconnected"
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/v1/agents/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_operator_session),
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
            metadata=request.metadata or {},
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        # Process with agent
        context = request.context or {}
        agent = get_agent()
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
                request.channel, request.channel_id, response_text, request.user_id
            )

        # Publish event to Redis
        await redis_service.publish_event(
            "agent:response",
            {
                "message_id": message.id,
                "channel": request.channel,
                "response": response_text,
            },
        )

        return AgentResponse(
            message_id=message.id,
            response=response_text,
            status=message.status.value,
            channel=request.channel,
            metadata=message.response_metadata,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _send_response_to_channel(
    channel: str, channel_id: str, response: str, user_id: Optional[str] = None
) -> None:
    """Send response back through the integration channel."""
    try:
        integration: Optional[Union[SlackIntegration, DiscordIntegration, EmailIntegration, WebhookIntegration]] = None

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
                content=response, channel_id=channel_id, user_id=user_id
            )
    except Exception as e:
        print(f"Error sending response to channel: {e}")


@app.get("/api/v1/messages/{message_id}")
async def get_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_operator_session),
) -> dict[str, Any]:
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
    _: str = Depends(verify_operator_session),
) -> list[dict[str, Any]]:
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


@app.get("/api/v1/events")
async def list_event_status(
    message_id: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_operator_session),
) -> dict[str, Any]:
    """List durable event attempts for authenticated operators."""
    query = (
        select(OutboxEvent, InboxEvent)
        .outerjoin(InboxEvent, InboxEvent.message_id == OutboxEvent.aggregate_id)
    )
    if message_id:
        query = query.where(OutboxEvent.aggregate_id == message_id)
    if provider:
        query = query.where(InboxEvent.provider == provider)
    if status:
        query = query.where(OutboxEvent.status == status)
    query = query.order_by(OutboxEvent.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()
    return {
        "items": [
            {
                **event.to_dict(),
                "message_id": event.aggregate_id,
                "provider": inbox.provider if inbox else None,
                "provider_event_id": inbox.provider_event_id if inbox else None,
                "event_type": event.event_type,
            }
            for event, inbox in rows
        ],
        "limit": limit,
        "offset": offset,
    }


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket_endpoint(websocket)


@app.post("/api/v1/webhooks/{integration_type}")
async def receive_webhook(
    integration_type: str, request: Request, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Receive webhook from external service."""
    try:
        body = await request.body()
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Webhook body must be valid JSON")
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Webhook body must be a JSON object")

        if integration_type == "slack" and not verify_slack_request(
            body,
            request.headers.get("X-Slack-Request-Timestamp"),
            request.headers.get("X-Slack-Signature"),
        ):
            raise HTTPException(status_code=401, detail="Invalid or missing Slack signature")
        if integration_type == "discord" and not verify_discord_request(
            body,
            request.headers.get("X-Signature-Timestamp"),
            request.headers.get("X-Signature-Ed25519"),
        ):
            raise HTTPException(status_code=401, detail="Invalid or missing Discord signature")

        # Special case: Slack URL verification handshake
        # Slack sends a one-time "url_verification" request with a "challenge" field.
        # We must echo the challenge back so Slack accepts the webhook URL.
        if (
            integration_type == "slack"
            and payload.get("type") == "url_verification"
            and "challenge" in payload
        ):
            return {"challenge": payload["challenge"]}
        if integration_type == "discord" and payload.get("type") == 1:
            return {"type": 1}

        integration: Optional[Union[SlackIntegration, DiscordIntegration, WebhookIntegration]] = None

        if integration_type == "slack":
            integration = SlackIntegration({})
        elif integration_type == "discord":
            integration = DiscordIntegration({})
        elif integration_type == "webhook":
            integration = WebhookIntegration({})
            signature = request.headers.get("X-Webhook-Signature")
            if not integration.verify_request(payload, signature):
                raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown integration type: {integration_type}"
            )

        # Parse message from webhook
        message = await integration.receive_message(payload)

        if message:
            provider_event_id = {
                "slack": payload.get("event_id"),
                "discord": payload.get("id"),
                "webhook": payload.get("event_id"),
            }[integration_type]
            if not provider_event_id:
                raise HTTPException(
                    status_code=400,
                    detail="Provider event ID is required for idempotent delivery",
                )

            existing = await db.execute(
                select(InboxEvent).where(
                    InboxEvent.provider == integration_type,
                    InboxEvent.provider_event_id == str(provider_event_id),
                )
            )
            existing_event = existing.scalar_one_or_none()
            if existing_event:
                return JSONResponse(
                    status_code=202,
                    content={"status": "duplicate", "message_id": existing_event.message_id},
                )

            message.id = message.id or str(uuid.uuid4())
            message.status = MessageStatus.PENDING
            db.add(message)
            db.add(
                InboxEvent(
                    provider=integration_type,
                    provider_event_id=str(provider_event_id),
                    message_id=message.id,
                    event_type=str(payload.get("type") or payload.get("event_type") or "message"),
                )
            )
            db.add(
                OutboxEvent(
                    event_type="process_message",
                    aggregate_id=message.id,
                    payload={"message_id": message.id},
                )
            )
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                duplicate = await db.execute(
                    select(InboxEvent).where(
                        InboxEvent.provider == integration_type,
                        InboxEvent.provider_event_id == str(provider_event_id),
                    )
                )
                duplicate_event = duplicate.scalar_one_or_none()
                if duplicate_event:
                    return JSONResponse(
                        status_code=202,
                        content={"status": "duplicate", "message_id": duplicate_event.message_id},
                    )
                raise

            return JSONResponse(
                status_code=202,
                content={"status": "accepted", "message_id": message.id},
            )

        return {"status": "ignored"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
