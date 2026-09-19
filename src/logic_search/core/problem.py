from __future__ import annotations

from typing import Hashable, Iterable, Protocol, TypeVar

StateT = TypeVar("StateT")
ActionT = TypeVar("ActionT")


class SearchProblem(Protocol[StateT, ActionT]):
    @property
    def initial_state(self) -> StateT: ...

    def state_key(self, state: StateT) -> Hashable: ...

    def is_goal(self, state: StateT) -> bool: ...

    def actions(self, state: StateT) -> Iterable[ActionT]: ...

    def result(self, state: StateT, action: ActionT) -> StateT: ...

    def heuristic(self, state: StateT) -> float: ...

