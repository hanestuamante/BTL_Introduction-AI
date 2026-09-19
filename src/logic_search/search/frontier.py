from __future__ import annotations

import heapq
from itertools import count
from typing import Generic, TypeVar

T = TypeVar("T")


class StackFrontier(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def __len__(self) -> int:
        return len(self._items)


class PriorityFrontier(Generic[T]):
    def __init__(self) -> None:
        self._items: list[tuple[float, int, int, T]] = []
        self._sequence = count()

    def push(self, item: T, priority: float, depth: int = 0) -> None:
        heapq.heappush(self._items, (priority, depth, next(self._sequence), item))

    def pop(self) -> tuple[float, T]:
        priority, _depth, _sequence, item = heapq.heappop(self._items)
        return priority, item

    def __len__(self) -> int:
        return len(self._items)

