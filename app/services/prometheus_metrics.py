"""
Prometheus custom metric definitions — module-level singletons.

All metric objects are defined here to prevent duplicate-registration errors
if either consumer module (mealdb.py, api.py) is reimported during tests.

These are entirely independent from the existing MetricsCollector which
powers /api/metrics. Both systems coexist without interfering.
"""

from prometheus_client import Counter, Histogram

# ---------------------------------------------------------------------------
# Cache metrics
# ---------------------------------------------------------------------------

CACHE_HITS = Counter(
    "cache_hits_total",
    "Number of Redis cache hits",
    ["operation"],  # "search" | "meal_lookup"
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Number of Redis cache misses (live API call follows)",
    ["operation"],
)

# ---------------------------------------------------------------------------
# MealDB API metrics
# ---------------------------------------------------------------------------

MEALDB_REQUESTS = Counter(
    "mealdb_api_requests_total",
    "Total HTTP requests to TheMealDB API",
    [
        "operation",
        "status",
    ],  # operation: "search"|"meal_lookup", status: "success"|"error"
)

MEALDB_DURATION = Histogram(
    "mealdb_api_duration_seconds",
    "Duration of TheMealDB HTTP calls in seconds",
    ["operation"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ---------------------------------------------------------------------------
# Search popularity
# ---------------------------------------------------------------------------

RECIPE_SEARCHES = Counter(
    "recipe_searches_total",
    "Recipe searches by query term. NOTE: unbounded label cardinality — "
    "acceptable for a startup, review before production scale.",
    ["query"],  # normalised to lowercase by callers
)
