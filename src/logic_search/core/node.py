from __future__ import annotations

from dataclasses import dataclass
from typing import Generic

from .problem import ActionT, StateT


@dataclass(slots=True)
class SearchNode(Generic[StateT, ActionT]):
    state: StateT
    parent_id: int | None
    action: ActionT | None
    depth: int
    h: float = 0.0

