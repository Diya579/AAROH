"""In-memory thread-safe caching layer for ML models and export metadata."""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional


class InferenceCache:
    """Thread-safe cache avoiding redundant disk I/O for models, configs, and metadata."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cache: Dict[str, Any] = {}
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Retrieve a cached object by key."""
        with self._lock:
            if key in self._cache:
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return default

    def put(self, key: str, value: Any) -> None:
        """Insert or replace a cached object."""
        with self._lock:
            self._cache[key] = value

    def contains(self, key: str) -> bool:
        """Check if a key exists in cache."""
        with self._lock:
            return key in self._cache

    def clear(self) -> None:
        """Empty the cache and reset statistics."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def stats(self) -> Dict[str, Any]:
        """Return cache access statistics and current size."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(hit_ratio, 4),
                "keys": list(self._cache.keys()),
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)
