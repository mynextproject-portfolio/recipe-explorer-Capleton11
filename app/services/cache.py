"""
Redis cache module for external API responses.

Provides a simple async get/set interface with JSON serialization and
graceful degradation — if Redis is unavailable, every operation is a
silent no-op so the rest of the application continues unaffected.

Configuration
-------------
Set the ``REDIS_URL`` environment variable to point at your Redis
instance (default: ``redis://localhost:6379``).  In docker-compose this
should be ``redis://redis:6379`` (using the service name as hostname).
"""

import json
import os
from typing import Any, Optional

import redis.asyncio as aioredis

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL_SECONDS: int = 86400  # 24 hours

# Module-level singleton – created lazily on first use
_client: Optional[aioredis.Redis] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def get_client() -> Optional[aioredis.Redis]:
    """Return a shared Redis client, connecting lazily on first call.

    Returns ``None`` (rather than raising) when Redis is unreachable so
    that callers can degrade gracefully.
    """
    global _client
    if _client is None:
        try:
            _client = aioredis.from_url(REDIS_URL, decode_responses=True)
            await _client.ping()
        except Exception:
            _client = None
    return _client


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

async def get(key: str) -> Optional[Any]:
    """Retrieve a JSON-deserialized value from the cache.

    Returns ``None`` on a cache miss or when Redis is unavailable.
    """
    client = await get_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception:
        return None


async def set(key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    """Serialize *value* as JSON and store it in Redis with *ttl* seconds.

    Silently ignores any errors so that caching failures never surface to
    callers.
    """
    client = await get_client()
    if client is None:
        return
    try:
        await client.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass


async def close() -> None:
    """Close the Redis connection.  Call this during application shutdown."""
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception:
            pass
        finally:
            _client = None
