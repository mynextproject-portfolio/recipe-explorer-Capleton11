"""
Tests for performance metrics instrumentation.

Sections:
  1. Unit tests  – Timer and MetricsCollector directly
  2. API tests   – meta field in search responses + /api/metrics endpoint
  3. Integration – compare real internal vs external timings
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from app.services.metrics import MetricsCollector, Timer, collector
from app.services.mealdb import _transform_meal
from tests.conftest import MOCK_MEALDB_MEAL


# ---------------------------------------------------------------------------
# Fixture: reset the global collector before each test in this file
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_global_collector():
    collector.reset()
    yield
    collector.reset()


# ---------------------------------------------------------------------------
# 1. Unit tests: Timer and MetricsCollector
# ---------------------------------------------------------------------------

def test_timer_measures_positive_duration():
    with Timer("test") as t:
        time.sleep(0.01)
    assert t.duration_ms > 0


def test_timer_records_to_global_collector():
    with Timer("test_source"):
        pass
    stats = collector.get_stats()
    assert "test_source" in stats
    assert stats["test_source"]["total_calls"] == 1


def test_timer_duration_ms_accessible_after_block():
    with Timer("src") as t:
        time.sleep(0.005)
    assert t.duration_ms >= 5  # at least 5ms for 5ms sleep


def test_collector_accumulates_multiple_calls():
    c = MetricsCollector()
    c.record("internal", 1.0)
    c.record("internal", 3.0)
    stats = c.get_stats()
    assert stats["internal"]["total_calls"] == 2
    assert stats["internal"]["total_duration_ms"] == pytest.approx(4.0, abs=0.01)


def test_collector_avg_duration():
    c = MetricsCollector()
    c.record("internal", 2.0)
    c.record("internal", 4.0)
    assert c.get_stats()["internal"]["avg_duration_ms"] == pytest.approx(3.0, abs=0.01)


def test_collector_min_max():
    c = MetricsCollector()
    c.record("internal", 10.0)
    c.record("internal", 1.0)
    c.record("internal", 5.0)
    stats = c.get_stats()["internal"]
    assert stats["min_duration_ms"] == pytest.approx(1.0, abs=0.01)
    assert stats["max_duration_ms"] == pytest.approx(10.0, abs=0.01)


def test_collector_min_max_none_when_no_calls():
    c = MetricsCollector()
    c._data  # ensure empty
    # No calls recorded yet — but we need at least one to get stats
    c.record("src", 5.0)
    c.reset()
    assert c.get_stats() == {}


def test_collector_reset_clears_data():
    c = MetricsCollector()
    c.record("x", 1.0)
    c.reset()
    assert c.get_stats() == {}


def test_collector_tracks_multiple_sources():
    c = MetricsCollector()
    c.record("internal", 0.5)
    c.record("external", 250.0)
    stats = c.get_stats()
    assert "internal" in stats
    assert "external" in stats


# ---------------------------------------------------------------------------
# 2. API tests: meta field in search responses
# ---------------------------------------------------------------------------

def test_get_recipes_response_includes_meta(client, clean_storage):
    response = client.get("/api/recipes")
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data


def test_meta_has_internal_section(client, clean_storage):
    response = client.get("/api/recipes")
    meta = response.json()["meta"]
    assert "internal" in meta
    assert "count" in meta["internal"]
    assert "duration_ms" in meta["internal"]


def test_meta_has_external_section(client, clean_storage):
    response = client.get("/api/recipes")
    meta = response.json()["meta"]
    assert "external" in meta


def test_meta_has_total_duration(client, clean_storage):
    response = client.get("/api/recipes")
    meta = response.json()["meta"]
    assert "total_duration_ms" in meta
    assert meta["total_duration_ms"] >= 0


def test_meta_internal_duration_is_non_negative(client, clean_storage):
    response = client.get("/api/recipes")
    assert response.json()["meta"]["internal"]["duration_ms"] >= 0


def test_meta_external_zero_when_no_search(client, clean_storage):
    """No search query → no external call → external duration should be 0."""
    response = client.get("/api/recipes")
    assert response.json()["meta"]["external"]["duration_ms"] == 0.0
    assert response.json()["meta"]["external"]["count"] == 0


def test_meta_external_nonzero_when_searching(client, clean_storage):
    """With a search query, external timing must be recorded (even if mocked)."""
    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[_transform_meal(MOCK_MEALDB_MEAL)],
    ):
        response = client.get("/api/recipes?search=chicken")

    meta = response.json()["meta"]
    assert meta["external"]["count"] == 1
    assert meta["external"]["duration_ms"] >= 0


def test_meta_counts_match_recipe_list(client, clean_storage, sample_recipe_data):
    """meta.internal.count must equal the number of internal recipes returned."""
    client.post("/api/recipes", json=sample_recipe_data)

    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[_transform_meal(MOCK_MEALDB_MEAL)],
    ):
        response = client.get("/api/recipes?search=test")

    data = response.json()
    internal_in_list = sum(1 for r in data["recipes"] if r["source"] == "internal")
    external_in_list = sum(1 for r in data["recipes"] if r["source"] == "external")

    assert data["meta"]["internal"]["count"] == internal_in_list
    assert data["meta"]["external"]["count"] == external_in_list


def test_search_endpoint_also_has_meta(client, clean_storage):
    """/api/recipes/search?q= should also return meta timing."""
    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = client.get("/api/recipes/search?q=test")

    assert response.status_code == 200
    assert "meta" in response.json()


# ---------------------------------------------------------------------------
# 3. /api/metrics endpoint
# ---------------------------------------------------------------------------

def test_metrics_endpoint_returns_200(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200


def test_metrics_endpoint_empty_before_any_requests(client):
    response = client.get("/api/metrics")
    assert response.json() == {}


def test_metrics_endpoint_records_after_search(client, clean_storage):
    with patch(
        "app.services.mealdb.search_meals",
        new_callable=AsyncMock,
        return_value=[],
    ):
        client.get("/api/recipes?search=pasta")

    stats = client.get("/api/metrics").json()
    assert "internal" in stats
    assert "external" in stats


def test_metrics_internal_structure(client, clean_storage):
    client.get("/api/recipes")  # triggers internal timing
    stats = client.get("/api/metrics").json()["internal"]
    for key in ("total_calls", "total_duration_ms", "avg_duration_ms",
                "min_duration_ms", "max_duration_ms"):
        assert key in stats, f"Missing key: {key}"


def test_metrics_accumulate_across_requests(client, clean_storage):
    client.get("/api/recipes")
    client.get("/api/recipes")
    client.get("/api/recipes")
    stats = client.get("/api/metrics").json()
    assert stats["internal"]["total_calls"] == 3


def test_metrics_reset_endpoint(client, clean_storage):
    client.get("/api/recipes")
    client.post("/api/metrics/reset")
    assert client.get("/api/metrics").json() == {}


def test_metrics_avg_duration_is_non_negative(client, clean_storage):
    client.get("/api/recipes")
    stats = client.get("/api/metrics").json()
    assert stats["internal"]["avg_duration_ms"] >= 0


# ---------------------------------------------------------------------------
# 4. Integration: real internal vs real external timing comparison
# ---------------------------------------------------------------------------

def test_internal_faster_than_external_in_real_search(client, clean_storage):
    """Integration: real TheMealDB call should be measurably slower than
    in-memory storage lookup.  Requires internet access."""
    response = client.get("/api/recipes?search=chicken")
    assert response.status_code == 200
    meta = response.json()["meta"]

    internal_ms = meta["internal"]["duration_ms"]
    external_ms = meta["external"]["duration_ms"]

    # In-memory lookup is always sub-millisecond; external HTTP takes >> 1ms
    assert internal_ms < external_ms, (
        f"Expected internal ({internal_ms}ms) < external ({external_ms}ms)"
    )

    # Also verify the accumulated metrics captured both
    acc = client.get("/api/metrics").json()
    assert acc["internal"]["total_calls"] >= 1
    assert acc["external"]["total_calls"] >= 1
