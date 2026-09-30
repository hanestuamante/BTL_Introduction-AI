from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Any, Hashable


class EventType(str, Enum):
    STARTED = "STARTED"
    NODE_GENERATED = "NODE_GENERATED"
    NODE_EXPANDED = "NODE_EXPANDED"
    NODE_PRUNED = "NODE_PRUNED"
    GOAL_FOUND = "GOAL_FOUND"
    FINISHED = "FINISHED"
    ERROR = "ERROR"
    CELL_DOMAIN = "CELL_DOMAIN"
    VALUE_TRIED = "VALUE_TRIED"
    VALUE_REJECTED = "VALUE_REJECTED"


@dataclass(slots=True, frozen=True)
class SearchEvent:
    type: EventType
    elapsed_ms: float
    state_key: Hashable | None = None
    state: Any = None
    action: Any = None
    depth: int = 0
    h: float = 0.0
    nodes_generated: int = 0
    nodes_expanded: int = 0
    nodes_pruned: int = 0
    frontier_size: int = 0
    message: str = ""
    cell: int | None = None
    value: int | None = None
    domain: tuple[int, ...] | None = None
    reason: str | None = None


class EventEmitter:
    def __init__(self, callback=None, *, detailed: bool = True) -> None:
        self.callback = callback
        self.detailed = detailed
        self.accumulated_ms = 0.0
        self.last_active = perf_counter()

    def emit(self, event_type: EventType, **kwargs: Any) -> None:
        if self.callback is None:
            return
        if not self.detailed and event_type in {
            EventType.NODE_GENERATED,
            EventType.NODE_EXPANDED,
            EventType.NODE_PRUNED,
            EventType.CELL_DOMAIN,
            EventType.VALUE_TRIED,
            EventType.VALUE_REJECTED,
        }:
            return
        now = perf_counter()
        self.accumulated_ms += (now - self.last_active) * 1000
        event = SearchEvent(event_type, self.accumulated_ms, **kwargs)
        try:
            self.callback(event)
        finally:
            self.last_active = perf_counter()

