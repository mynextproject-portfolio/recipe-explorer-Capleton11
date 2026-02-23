"""
Lightweight in-memory performance metrics collector.

Usage
-----
# Time a block and record it against a named source:
with Timer("internal") as t:
    results = storage.search(...)
print(t.duration_ms)   # elapsed milliseconds

# Read accumulated stats:
from app.services.metrics import collector
collector.get_stats()   # {"internal": {...}, "external": {...}}
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Per-source stats
# ---------------------------------------------------------------------------


@dataclass
class SourceStats:
    total_calls: int = 0
    total_duration_ms: float = 0.0
    _min: float = field(default=float("inf"), repr=False)
    _max: float = field(default=0.0, repr=False)

    def record(self, duration_ms: float) -> None:
        self.total_calls += 1
        self.total_duration_ms += duration_ms
        if duration_ms < self._min:
            self._min = duration_ms
        if duration_ms > self._max:
            self._max = duration_ms

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.total_calls if self.total_calls else 0.0

    @property
    def min_duration_ms(self) -> Optional[float]:
        return round(self._min, 3) if self.total_calls else None

    @property
    def max_duration_ms(self) -> Optional[float]:
        return round(self._max, 3) if self.total_calls else None

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "total_duration_ms": round(self.total_duration_ms, 3),
            "avg_duration_ms": round(self.avg_duration_ms, 3),
            "min_duration_ms": self.min_duration_ms,
            "max_duration_ms": self.max_duration_ms,
        }


# ---------------------------------------------------------------------------
# Collector (singleton)
# ---------------------------------------------------------------------------


class MetricsCollector:
    def __init__(self) -> None:
        self._data: Dict[str, SourceStats] = {}

    def record(self, source: str, duration_ms: float) -> None:
        if source not in self._data:
            self._data[source] = SourceStats()
        self._data[source].record(duration_ms)

    def get_stats(self) -> dict:
        return {source: stats.to_dict() for source, stats in self._data.items()}

    def reset(self) -> None:
        self._data.clear()


# Global singleton used by routes and services
collector = MetricsCollector()


# ---------------------------------------------------------------------------
# Timer context manager
# ---------------------------------------------------------------------------


class Timer:
    """Sync context manager that measures elapsed wall-clock time and records
    it against the named source in a ``MetricsCollector``.

    When *metrics* is ``None`` (the default) the global ``collector``
    singleton is used, keeping backward compatibility with any code that
    creates a ``Timer`` without going through dependency injection.

    Example — direct use (uses global collector)::

        with Timer("internal") as t:
            results = storage.search(query)

    Example — injected collector (used by route handlers)::

        with Timer("internal", metrics) as t:
            results = storage.search(query)
    """

    def __init__(
        self, source: str, metrics: Optional["MetricsCollector"] = None
    ) -> None:
        self.source = source
        self.duration_ms: float = 0.0
        self._start: float = 0.0
        self._metrics = metrics if metrics is not None else collector

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_) -> None:
        self.duration_ms = (time.perf_counter() - self._start) * 1000
        self._metrics.record(self.source, self.duration_ms)
