"""Signed short-lived operator session helpers shared by HTTP and WebSocket."""

from typing import Any, Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_SALT = "integration-hub-session-v1"


def encode_session(claims: dict[str, Any], secret: str) -> str:
    return URLSafeTimedSerializer(secret, salt=SESSION_SALT).dumps(claims)


def decode_session(token: Optional[str], secret: Optional[str], max_age: int) -> Optional[dict[str, Any]]:
    if not token or not secret:
        return None
    try:
        claims = URLSafeTimedSerializer(secret, salt=SESSION_SALT).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return claims if isinstance(claims, dict) else None
