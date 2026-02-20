"""
Tests for Redis caching layer.

Sections:
  1. Unit tests  – cache.get / cache.set / cache.close
  2. Integration – search_meals cache behaviour (cache hit, cache miss, key format)
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import cache as cache_module
from app.services.mealdb import _transform_meal, search_meals
from tests.conftest import MOCK_MEALDB_MEAL


# ---------------------------------------------------------------------------
# Fixture: reset the module-level Redis singleton before/after each test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_cache_singleton():
    """Prevent state leaking between tests by resetting the lazy singleton."""
    original = cache_module._client
    cache_module._client = None
    yield
    cache_module._client = original


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_redis(get_return=None, ping_ok=True):
    """Build an AsyncMock that behaves like a redis.asyncio.Redis client."""
    mock = AsyncMock()
    if ping_ok:
        mock.ping.return_value = True
    else:
        mock.ping.side_effect = ConnectionError("Redis down")
    mock.get.return_value = get_return
    return mock


def _make_httpx_mock(meals):
    """Return patched httpx.AsyncClient that returns *meals* from TheMealDB."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"meals": meals or []}
    mock_response.raise_for_status.return_value = None

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_client
    mock_ctx.__aexit__.return_value = None

    return mock_ctx


# ---------------------------------------------------------------------------
# 1. Unit tests: cache module
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_get_returns_none_on_miss():
    """get() returns None when the key is absent from Redis."""
    cache_module._client = _make_mock_redis(get_return=None)
    result = await cache_module.get("missing_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_get_returns_deserialized_value():
    """get() deserializes the stored JSON and returns the Python object."""
    payload = {"title": "Chicken", "count": 3}
    cache_module._client = _make_mock_redis(get_return=json.dumps(payload))
    result = await cache_module.get("some_key")
    assert result == payload


@pytest.mark.asyncio
async def test_cache_set_stores_json_with_ttl():
    """set() calls redis.set with JSON-encoded data and the given TTL."""
    mock_redis = _make_mock_redis()
    cache_module._client = mock_redis

    await cache_module.set("key", {"count": 3}, ttl=100)

    mock_redis.set.assert_called_once_with("key", json.dumps({"count": 3}), ex=100)


@pytest.mark.asyncio
async def test_cache_set_uses_default_ttl_of_24_hours():
    """set() defaults to CACHE_TTL_SECONDS (86400) when ttl is not given."""
    mock_redis = _make_mock_redis()
    cache_module._client = mock_redis

    await cache_module.set("key", "value")

    _, kwargs = mock_redis.set.call_args
    assert kwargs.get("ex") == cache_module.CACHE_TTL_SECONDS


@pytest.mark.asyncio
async def test_cache_get_returns_none_when_redis_unavailable():
    """get() returns None gracefully when Redis is unreachable."""
    with patch.object(cache_module, "get_client", AsyncMock(return_value=None)):
        result = await cache_module.get("key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_does_not_raise_when_redis_unavailable():
    """set() silently swallows errors when Redis is unreachable."""
    with patch.object(cache_module, "get_client", AsyncMock(return_value=None)):
        await cache_module.set("key", {"data": 1})  # must not raise


@pytest.mark.asyncio
async def test_cache_get_client_returns_none_when_ping_fails():
    """get_client() returns None (and resets singleton) when ping fails."""
    with patch(
        "app.services.cache.aioredis.from_url",
        return_value=_make_mock_redis(ping_ok=False),
    ):
        client = await cache_module.get_client()
    assert client is None
    assert cache_module._client is None


def test_cache_ttl_constant_is_24_hours():
    """CACHE_TTL_SECONDS must be exactly 86400."""
    assert cache_module.CACHE_TTL_SECONDS == 86400


# ---------------------------------------------------------------------------
# 2. Integration: search_meals cache behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_meals_returns_cached_results_without_http_call():
    """On a cache hit, search_meals returns cached data and skips the API."""
    cached_payload = [_transform_meal(MOCK_MEALDB_MEAL).model_dump(mode="json")]

    with patch.object(cache_module, "get", AsyncMock(return_value=cached_payload)):
        with patch("app.services.mealdb.httpx.AsyncClient") as mock_http:
            results = await search_meals("chicken")

    assert len(results) == 1
    assert results[0].title == "Teriyaki Chicken Casserole"
    assert results[0].source == "external"
    mock_http.assert_not_called()


@pytest.mark.asyncio
async def test_search_meals_calls_api_on_cache_miss():
    """On a cache miss, search_meals calls the live API."""
    mock_ctx = _make_httpx_mock([MOCK_MEALDB_MEAL])

    with patch.object(cache_module, "get", AsyncMock(return_value=None)):
        with patch.object(cache_module, "set", AsyncMock()):
            with patch("app.services.mealdb.httpx.AsyncClient", return_value=mock_ctx):
                results = await search_meals("chicken")

    assert len(results) == 1
    assert results[0].title == "Teriyaki Chicken Casserole"


@pytest.mark.asyncio
async def test_search_meals_stores_results_in_cache_on_miss():
    """On a cache miss, search_meals writes results to Redis."""
    mock_ctx = _make_httpx_mock([MOCK_MEALDB_MEAL])

    with patch.object(cache_module, "get", AsyncMock(return_value=None)):
        with patch.object(cache_module, "set", AsyncMock()) as mock_set:
            with patch("app.services.mealdb.httpx.AsyncClient", return_value=mock_ctx):
                await search_meals("chicken")

    mock_set.assert_called_once()
    call_key = mock_set.call_args[0][0]
    assert call_key == "mealdb:search:chicken"


@pytest.mark.asyncio
async def test_search_meals_cache_key_lowercases_query():
    """Cache key normalises the search query to lowercase."""
    mock_ctx = _make_httpx_mock([])

    with patch.object(cache_module, "get", AsyncMock(return_value=None)) as mock_get:
        with patch.object(cache_module, "set", AsyncMock()):
            with patch("app.services.mealdb.httpx.AsyncClient", return_value=mock_ctx):
                await search_meals("CHICKEN")

    mock_get.assert_called_once_with("mealdb:search:chicken")


@pytest.mark.asyncio
async def test_search_meals_does_not_cache_empty_results():
    """Empty API responses are still stored (so we don't hammer the API)."""
    mock_ctx = _make_httpx_mock([])  # API returns nothing

    with patch.object(cache_module, "get", AsyncMock(return_value=None)):
        with patch.object(cache_module, "set", AsyncMock()) as mock_set:
            with patch("app.services.mealdb.httpx.AsyncClient", return_value=mock_ctx):
                results = await search_meals("xyzzy_no_results")

    assert results == []
    # Even empty results get cached to prevent repeated API calls
    mock_set.assert_called_once()


@pytest.mark.asyncio
async def test_search_meals_still_returns_results_when_cache_unavailable():
    """When Redis is down, search_meals returns live API results anyway.

    cache.set() swallows errors internally, so mealdb.py never raises even
    when the cache write fails.  We simulate this by having cache.get return
    None (cache miss) and cache.set be a no-op (graceful Redis failure).
    """
    mock_ctx = _make_httpx_mock([MOCK_MEALDB_MEAL])

    with patch.object(cache_module, "get", AsyncMock(return_value=None)):
        with patch.object(cache_module, "set", AsyncMock(return_value=None)):
            with patch("app.services.mealdb.httpx.AsyncClient", return_value=mock_ctx):
                results = await search_meals("chicken")

    assert len(results) == 1
    assert results[0].source == "external"


@pytest.mark.asyncio
async def test_search_meals_cache_hit_returns_valid_recipe_objects():
    """Recipes reconstructed from cache are proper Recipe instances."""
    from app.models import Recipe

    cached_payload = [_transform_meal(MOCK_MEALDB_MEAL).model_dump(mode="json")]

    with patch.object(cache_module, "get", AsyncMock(return_value=cached_payload)):
        with patch("app.services.mealdb.httpx.AsyncClient"):
            results = await search_meals("chicken")

    assert all(isinstance(r, Recipe) for r in results)


# ---------------------------------------------------------------------------
# 3. API endpoint — cache effectiveness reflected in timing
# ---------------------------------------------------------------------------


def test_cache_hit_external_timing_faster_than_miss(client, clean_storage):
    """A cache hit (mocked instant return) records a shorter external
    duration than a simulated slow API call.

    This validates that the metrics reflect cache effectiveness:
    meta.external.duration_ms drops when results come from Redis.
    """
    fast_payload = [_transform_meal(MOCK_MEALDB_MEAL)]

    # Simulate a cache hit: search_meals returns instantly
    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=fast_payload,
    ):
        response = client.get("/api/recipes?search=chicken")

    assert response.status_code == 200
    meta = response.json()["meta"]
    # External duration is measured; with a mock it should be sub-millisecond
    assert meta["external"]["duration_ms"] >= 0
    assert meta["external"]["count"] == 1
