"""
CoDude — Cache Service (Day 06)

Redis-based caching layer for LLM responses.

Why cache LLM calls?
    - Each OpenAI API call costs money ($0.15–$0.60 per 1M tokens for gpt-4o-mini).
    - LLM calls take 2–8 seconds; cached responses return in <5ms.
    - Identical code submitted by different users (or the same user twice)
      should return the same review — no need to re-run the LLM.

Cache key design:
    sha256(code + language) → fixed-length, URL-safe, collision-resistant.
    We concatenate code and language so that the same code in different
    languages gets separate cache entries (Python vs JavaScript reviews
    should differ).

TTL (Time-To-Live):
    Default 3600s (1 hour). Code best practices evolve, so we don't want
    stale reviews lingering forever. 1 hour is a good balance between
    cost savings and freshness.

Graceful degradation:
    If Redis is unreachable (not installed, down, wrong URL), the service
    logs a warning and skips caching entirely — the app continues to work,
    just without the cache speedup. This is critical for local development
    where Redis may not be running.
"""

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Async Redis cache for LLM review responses.

    Usage:
        cache = CacheService()
        cached = await cache.get("some-key")
        await cache.set("some-key", {"data": "value"}, ttl=3600)

    If Redis is unavailable, all operations gracefully return None / no-op.
    """

    def __init__(self) -> None:
        """Initialise the Redis connection pool."""
        self._redis: Optional[redis.Redis] = None
        self._available: bool = False

        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            self._available = True
            logger.info("Redis cache initialised — URL: %s", settings.REDIS_URL)
        except Exception as exc:
            logger.warning(
                "Redis unavailable — caching disabled. Error: %s", exc
            )

    @staticmethod
    def make_key(code: str, language: str) -> str:
        """
        Generate a deterministic cache key from code + language.

        Uses SHA-256 to produce a fixed-length (64-char hex) key that is
        safe for use as a Redis key. Prefixed with 'review:' for namespacing.

        Args:
            code:     The source code string.
            language: The programming language.

        Returns:
            A string like 'review:a1b2c3d4...' (70 chars total).
        """
        raw = f"{code}|{language}"
        content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"review:{content_hash}"

    async def get(self, key: str) -> Optional[dict]:
        """
        Retrieve a cached value by key.

        Args:
            key: The cache key (from make_key).

        Returns:
            The cached dict if found, None on miss or if Redis is unavailable.
        """
        if not self._available or self._redis is None:
            return None

        try:
            data = await self._redis.get(key)
            if data is not None:
                logger.info("Cache HIT — key=%s", key[:30])
                return json.loads(data)
            logger.info("Cache MISS — key=%s", key[:30])
            return None
        except Exception as exc:
            logger.warning("Cache GET failed — key=%s, error=%s", key[:30], exc)
            return None

    async def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """
        Store a value in the cache with a TTL.

        Args:
            key:   The cache key (from make_key).
            value: The dict to cache (will be JSON-serialised).
            ttl:   Time-to-live in seconds (default: 3600 = 1 hour).
        """
        if not self._available or self._redis is None:
            return

        try:
            serialised = json.dumps(value)
            await self._redis.set(key, serialised, ex=ttl)
            logger.info("Cache SET — key=%s, ttl=%ds", key[:30], ttl)
        except Exception as exc:
            logger.warning("Cache SET failed — key=%s, error=%s", key[:30], exc)

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._redis is not None:
            await self._redis.close()
            logger.info("Redis connection closed.")
