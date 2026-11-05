from __future__ import annotations

from collections import OrderedDict
from collections.abc import Hashable
from typing import Generic, TypeVar

Key = TypeVar("Key", bound=Hashable)
Value = TypeVar("Value")


class LruCache(Generic[Key, Value]):
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError(f"Cache capacity must be at least 1: {capacity}")
        self._capacity = capacity
        self._entries: OrderedDict[Key, Value] = OrderedDict()

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, key: object) -> bool:
        return key in self._entries

    @property
    def capacity(self) -> int:
        return self._capacity

    def keys(self) -> list[Key]:
        return list(self._entries)

    def get(self, key: Key) -> Value | None:
        if key not in self._entries:
            return None
        self._entries.move_to_end(key)
        return self._entries[key]

    def put(self, key: Key, value: Value) -> list[Key]:
        self._entries[key] = value
        self._entries.move_to_end(key)
        return self._evict_overflow()

    def clear(self) -> None:
        self._entries.clear()

    def _evict_overflow(self) -> list[Key]:
        evicted: list[Key] = []
        while len(self._entries) > self._capacity:
            key, _value = self._entries.popitem(last=False)
            evicted.append(key)
        return evicted
