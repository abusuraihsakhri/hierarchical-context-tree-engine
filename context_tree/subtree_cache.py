"""
Subtree Caching for Hierarchical Context Tree Engine.
Caches resolved subtrees keyed by content hash with configurable TTL.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class CacheEntry:
    """A single cached subtree entry."""
    key: str
    subtree: Dict[str, Any]
    created_at: float
    ttl_seconds: float
    hit_count: int = 0
    last_accessed: float = 0.0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    def touch(self) -> None:
        self.hit_count += 1
        self.last_accessed = time.time()


class SubtreeCache:
    """LRU cache for resolved subtrees with TTL expiration."""

    def __init__(self, max_size: int = 256, default_ttl: float = 3600.0):
        self._cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._total_hits = 0
        self._total_misses = 0

    @staticmethod
    def compute_hash(subtree: Dict[str, Any]) -> str:
        """Compute deterministic hash of a subtree structure."""
        serialized = json.dumps(subtree, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached subtree by key."""
        entry = self._cache.get(key)
        if entry is None:
            self._total_misses += 1
            return None
        if entry.is_expired():
            del self._cache[key]
            self._total_misses += 1
            return None
        entry.touch()
        self._total_hits += 1
        return entry.subtree

    def put(self, key: str, subtree: Dict[str, Any], ttl: Optional[float] = None) -> None:
        """Cache a subtree with the given key."""
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        self._cache[key] = CacheEntry(
            key=key,
            subtree=subtree,
            created_at=time.time(),
            ttl_seconds=ttl or self.default_ttl,
            last_accessed=time.time(),
        )

    def get_or_resolve(self, key: str, resolve_fn, ttl: Optional[float] = None) -> Dict[str, Any]:
        """Get from cache or resolve and cache."""
        cached = self.get(key)
        if cached is not None:
            return cached
        subtree = resolve_fn()
        self.put(key, subtree, ttl)
        return subtree

    def invalidate(self, key: str) -> bool:
        """Remove a specific entry from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> int:
        """Clear all cached entries. Returns count of entries cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return
        lru_key = min(self._cache, key=lambda k: self._cache[k].last_accessed)
        del self._cache[lru_key]

    def metrics(self) -> Dict[str, Any]:
        """Return cache performance metrics."""
        total = self._total_hits + self._total_misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "total_hits": self._total_hits,
            "total_misses": self._total_misses,
            "hit_rate": self._total_hits / total if total > 0 else 0.0,
            "entries": [
                {
                    "key": e.key,
                    "hit_count": e.hit_count,
                    "age_seconds": time.time() - e.created_at,
                    "expired": e.is_expired(),
                }
                for e in self._cache.values()
            ],
        }

    def prune_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for k in expired_keys:
            del self._cache[k]
        return len(expired_keys)
