
import time
from threading import Lock
from typing import Any


class SearchCache:

    def __init__(
        self,
        max_size: int = 500,
        ttl_seconds: int = 300,
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

        self.cache: dict[str, tuple[float, Any]] = {}
        self.lock = Lock()

    def get(self, key: str):

        with self.lock:

            entry = self.cache.get(key)

            if entry is None:
                return None

            expires_at, value = entry

            if time.monotonic() >= expires_at:
                self.cache.pop(key, None)
                return None

            return value

    def set(self, key: str, value: Any):

        with self.lock:

            if len(self.cache) >= self.max_size:
                self._remove_expired()

            if len(self.cache) >= self.max_size:
                oldest_key = min(
                    self.cache,
                    key=lambda item: self.cache[item][0],
                )

                self.cache.pop(oldest_key, None)

            expires_at = (
                time.monotonic() + self.ttl_seconds
            )

            self.cache[key] = (
                expires_at,
                value,
            )

    def clear(self):

        with self.lock:
            self.cache.clear()

    def _remove_expired(self):

        now = time.monotonic()

        expired_keys = [
            key
            for key, (expires_at, _) in self.cache.items()
            if now >= expires_at
        ]

        for key in expired_keys:
            self.cache.pop(key, None)


search_cache = SearchCache(
    max_size=500,
    ttl_seconds=300,
)
