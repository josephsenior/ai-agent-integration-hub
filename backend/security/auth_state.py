"""Shared operator authentication state backed by Redis."""

import hashlib
import hmac
from typing import Optional

from ..core.config import settings
from ..services.redis_service import redis_service

CHECK_THROTTLE_SCRIPT = """
local count = tonumber(redis.call('GET', KEYS[1]) or '0')
if count >= tonumber(ARGV[1]) then
  return {0, redis.call('TTL', KEYS[1])}
end
return {1, 0}
"""

RECORD_FAILURE_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return {count, redis.call('TTL', KEYS[1])}
"""


class AuthStateUnavailable(Exception):
    """Raised when shared auth state cannot be read or written."""


async def _client():
    try:
        if redis_service.redis_client is None:
            await redis_service.connect()
        client = redis_service.redis_client
        if client is None:
            raise RuntimeError("Redis client did not initialize")
        await client.ping()
        return client
    except Exception as exc:
        raise AuthStateUnavailable("Redis auth state is unavailable") from exc


async def _execute(operation):
    try:
        return await operation
    except Exception as exc:
        raise AuthStateUnavailable("Redis auth state is unavailable") from exc


def login_throttle_key(client_identity: str) -> str:
    secret = settings.session_secret_key or "missing-session-secret"
    digest = hmac.new(secret.encode(), client_identity.encode(), hashlib.sha256).hexdigest()
    return f"integration_hub:auth:login:{digest}"


def session_key(session_id: str) -> str:
    return f"integration_hub:auth:session:{session_id}"


async def check_login_throttle(client_identity: str, maximum: int) -> Optional[int]:
    client = await _client()
    result = await _execute(
        client.eval(CHECK_THROTTLE_SCRIPT, 1, login_throttle_key(client_identity), maximum)
    )
    if int(result[0]) == 0:
        return max(1, int(result[1]))
    return None


async def record_login_failure(client_identity: str, window_seconds: int) -> tuple[int, int]:
    client = await _client()
    result = await _execute(
        client.eval(
            RECORD_FAILURE_SCRIPT,
            1,
            login_throttle_key(client_identity),
            window_seconds,
        )
    )
    return int(result[0]), max(1, int(result[1]))


async def clear_login_failures(client_identity: str) -> None:
    client = await _client()
    await _execute(client.delete(login_throttle_key(client_identity)))


async def register_session(session_id: str, username: str, ttl_seconds: int) -> None:
    client = await _client()
    await _execute(client.set(session_key(session_id), username, ex=ttl_seconds))


async def is_session_active(session_id: str, username: str) -> bool:
    client = await _client()
    value = await _execute(client.get(session_key(session_id)))
    return value == username


async def revoke_session(session_id: str) -> None:
    client = await _client()
    await _execute(client.delete(session_key(session_id)))
