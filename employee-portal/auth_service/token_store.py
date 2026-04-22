# auth_service/token_store.py
# CWE-522: Refresh tokens stored in unauthenticated Redis

import redis
import uuid
from datetime import timedelta
from auth_service.config import REDIS_URL, JWT_REFRESH_TOKEN_EXPIRE_DAYS

# Redis client — no password, no TLS, relies on network isolation only
# CWE-522 starts here
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def store_refresh_token(user_id: int, token: str) -> None:
    """
    Store refresh token in Redis with no access control.
    Any internal service or attacker on the internal network
    can read all keys and impersonate any active session.
    """
    # line 41 — INTENTIONAL VULNERABILITY: CWE-522
    redis_client.setex(
        f"refresh:{token}",
        timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        str(user_id),
    )


def get_user_id_for_token(token: str) -> str | None:
    return redis_client.get(f"refresh:{token}")


def revoke_refresh_token(token: str) -> None:
    redis_client.delete(f"refresh:{token}")


def list_all_active_tokens():
    """
    No authentication on Redis means anyone on the internal network
    can call KEYS refresh:* and enumerate all active sessions.
    """
    return redis_client.keys("refresh:*")
