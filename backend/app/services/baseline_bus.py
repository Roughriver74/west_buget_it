"""
Baseline calculation bus with in-process caching.

Provides a single entry point for baseline aggregations to:
1. Cache expensive baseline computations for a short TTL
2. De-duplicate concurrent requests for the same payload
3. Allow invalidation when expenses mutate
"""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple, TypedDict, Any

from app.core.config import settings


class BaselineData(TypedDict):
    total_amount: Any
    monthly_avg: Any
    monthly_breakdown: list
    capex_total: Any
    opex_total: Any


@dataclass
class CacheRecord:
    expires_at: float
    value: BaselineData


class BaselineCalculationBus:
    """Shared cache/dedup layer for baseline calculations."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheRecord] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._registry_lock = threading.Lock()

    def _key(self, category_id: int, year: int, department_id: int) -> str:
        return f"{category_id}:{year}:{department_id}"

    def _get_lock(self, key: str) -> threading.Lock:
        with self._registry_lock:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
            return lock

    def _get_cached(self, key: str) -> Optional[BaselineData]:
        record = self._cache.get(key)
        if not record:
            return None

        if record.expires_at <= time.time():
            # Remove stale cache entry lazily
            self._cache.pop(key, None)
            return None

        return deepcopy(record.value)

    def get_or_compute(
        self,
        *,
        category_id: int,
        base_year: int,
        department_id: int,
        loader: Callable[[], BaselineData],
    ) -> BaselineData:
        """
        Return cached baseline data or compute it using the provided loader.

        Concurrency: ensures only one loader executes per key.
        """
        key = self._key(category_id, base_year, department_id)

        # Fast path from cache
        with self._registry_lock:
            cached = self._get_cached(key)
            if cached is not None:
                return cached

        lock = self._get_lock(key)

        # Serialize concurrent loaders for the same key
        with lock:
            with self._registry_lock:
                cached = self._get_cached(key)
                if cached is not None:
                    return cached

            fresh_value = loader()
            cache_snapshot = deepcopy(fresh_value)
            expires_at = time.time() + self._ttl_seconds

            with self._registry_lock:
                self._cache[key] = CacheRecord(
                    expires_at=expires_at,
                    value=cache_snapshot,
                )

            return fresh_value

    def invalidate(
        self,
        *,
        category_id: Optional[int] = None,
        department_id: Optional[int] = None,
        year: Optional[int] = None,
    ) -> None:
        """
        Remove cached entries matching filters.

        Any filter parameter can be omitted to act as a wildcard.
        """
        to_remove = []
        with self._registry_lock:
            for key in list(self._cache.keys()):
                cat_id, yr, dept_id = self._parse_key(key)
                if category_id is not None and cat_id != category_id:
                    continue
                if department_id is not None and dept_id != department_id:
                    continue
                if year is not None and yr != year:
                    continue
                to_remove.append(key)

            for key in to_remove:
                self._cache.pop(key, None)
                self._locks.pop(key, None)

    def invalidate_for_expense(
        self,
        category_id: Optional[int],
        department_id: Optional[int],
        request_year: Optional[int],
    ) -> None:
        """Helper that invalidates cache entries affected by an expense mutation."""
        if category_id is None or department_id is None or request_year is None:
            return
        self.invalidate(
            category_id=category_id,
            department_id=department_id,
            year=request_year,
        )

    def _parse_key(self, key: str) -> Tuple[int, int, int]:
        cat_id, year, dept_id = key.split(":")
        return int(cat_id), int(year), int(dept_id)


baseline_bus = BaselineCalculationBus(
    ttl_seconds=getattr(settings, "BASELINE_CACHE_TTL_SECONDS", 300)
)
