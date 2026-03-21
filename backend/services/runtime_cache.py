from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    expires_at: datetime


class TtlCache(Generic[T]):
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, CacheEntry[T]] = {}
        self._lock = Lock()

    def get(self, key: str) -> T | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            if entry.expires_at < datetime.now(timezone.utc):
                self._data.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: T) -> T:
        with self._lock:
            self._data[key] = CacheEntry(
                value=value,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.ttl_seconds),
            )
            return value
