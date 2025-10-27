"""
Shared caching service with Redis support and in-process fallback.

Used for caching frequently accessed reference data (справочники) with
short-lived TTL to reduce database load.
"""

from __future__ import annotations

import enum
import json
import threading
import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from app.core.config import settings

try:
    import redis  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled by feature flag
    redis = None


class _LocalCacheRecord:
    __slots__ = ("payload", "expires_at")

    def __init__(self, payload: str, expires_at: float) -> None:
        self.payload = payload
        self.expires_at = expires_at


class CacheService:
    """Simple JSON-based cache with optional Redis backend."""

    def __init__(
        self,
        ttl_seconds: int = 300,
        enable_redis: Optional[bool] = None,
        prefix: str = "itbudget:cache",
    ) -> None:
        self._enabled = ttl_seconds > 0
        self._ttl_seconds = ttl_seconds
        self._prefix = prefix
        self._lock = threading.Lock()
        self._local_cache: Dict[str, _LocalCacheRecord] = {}

        if enable_redis is None:
            enable_redis = settings.USE_REDIS

        self._use_redis = bool(enable_redis and redis is not None)
        self._redis_client: Optional["redis.Redis"] = None

        if self._use_redis:
            try:  # pragma: no branch - defensive, not hit in tests
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                )
                self._redis_client.ping()
            except Exception:
                # Fallback to local cache if Redis unavailable
                self._use_redis = False
                self._redis_client = None

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def build_key(self, *parts: Any) -> str:
        """Create deterministic cache key from arbitrary components."""
        return "|".join(self._normalize_part(part) for part in parts)

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Retrieve cached value if present and not expired."""
        if not self._enabled:
            return None

        full_key = self._compose_key(namespace, key)

        if self._use_redis and self._redis_client:
            payload = self._redis_client.get(full_key)
            if payload is None:
                return None
            return json.loads(payload)

        with self._lock:
            record = self._local_cache.get(full_key)
            if not record:
                return None
            if record.expires_at <= time.time():
                self._local_cache.pop(full_key, None)
                return None
            return json.loads(record.payload)

    def set(self, namespace: str, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value in cache."""
        if not self._enabled:
            return

        ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
        if ttl <= 0:
            return

        payload = json.dumps(value, default=self._json_serializer)
        full_key = self._compose_key(namespace, key)

        if self._use_redis and self._redis_client:
            self._redis_client.setex(full_key, ttl, payload)
            return

        expires_at = time.time() + ttl
        with self._lock:
            self._local_cache[full_key] = _LocalCacheRecord(payload, expires_at)

    def invalidate(self, namespace: str, key: str) -> None:
        """Remove specific cached item."""
        if not self._enabled:
            return

        full_key = self._compose_key(namespace, key)

        if self._use_redis and self._redis_client:
            self._redis_client.delete(full_key)

        with self._lock:
            self._local_cache.pop(full_key, None)

    def invalidate_namespace(self, namespace: str) -> None:
        """Clear all cached entries under the given namespace."""
        if not self._enabled:
            return

        prefix = self._compose_key(namespace)

        if self._use_redis and self._redis_client:
            pattern = f"{prefix}:*"
            keys = list(self._redis_client.scan_iter(match=pattern))
            if keys:
                self._redis_client.delete(*keys)

        with self._lock:
            keys_to_delete = [key for key in self._local_cache if key.startswith(f"{prefix}:")]
            for key in keys_to_delete:
                self._local_cache.pop(key, None)

    def clear(self) -> None:
        """Clear entire cache (all namespaces)."""
        if not self._enabled:
            return

        if self._use_redis and self._redis_client:
            pattern = f"{self._prefix}:*"
            keys = list(self._redis_client.scan_iter(match=pattern))
            if keys:
                self._redis_client.delete(*keys)

        with self._lock:
            self._local_cache.clear()

    def _compose_key(self, namespace: str, key: Optional[str] = None) -> str:
        base = f"{self._prefix}:{namespace}"
        return f"{base}:{key}" if key else base

    def _normalize_part(self, value: Any) -> str:
        if value is None:
            return "none"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, enum.Enum):
            return self._normalize_part(value.value)
        if isinstance(value, (list, tuple, set)):
            normalized_items = [self._normalize_part(item) for item in value]
            normalized_items.sort()
            return ",".join(normalized_items)
        if isinstance(value, dict):
            normalized_items = [
                f"{str(k)}={self._normalize_part(v)}" for k, v in value.items()
            ]
            normalized_items.sort()
            return ",".join(normalized_items)
        return str(value)

    def _json_serializer(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        raise TypeError(f"Type {type(value)} is not JSON serializable")


cache_service = CacheService(ttl_seconds=settings.CACHE_TTL_SECONDS)
