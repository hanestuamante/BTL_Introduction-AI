from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from logic_search.core.events import EventType

FutoshikiState = tuple[int, ...]
FutoshikiAction = tuple[int, int]
Inequality = tuple[int, str, int]


@dataclass(frozen=True, slots=True)
class FutoshikiProblem:
    puzzle_id: str
    size: int
    givens: FutoshikiState
    inequalities: tuple[Inequality, ...] = ()
    metadata: dict | None = None

    @property
    def initial_state(self) -> FutoshikiState:
        return self.givens

    def state_key(self, state: FutoshikiState) -> FutoshikiState:
        return state

    def _base_domain(self, state: FutoshikiState, index: int) -> set[int]:
        if state[index]:
            return {state[index]}
        row, col = divmod(index, self.size)
        used = set(state[row * self.size : (row + 1) * self.size])
        used.update(state[col :: self.size])
        used.discard(0)
        return set(range(1, self.size + 1)) - used

    def domain(self, state: FutoshikiState, index: int) -> tuple[int, ...]:
        domain = self._base_domain(state, index)
        if state[index]:
            return tuple(domain)
        for left, op, right in self.inequalities:
            if index not in (left, right):
                continue
            other = right if index == left else left
            other_domain = self._base_domain(state, other)
            if not other_domain:
                return ()
            if index == left:
                predicate = (lambda a, b: a < b) if op == "<" else (lambda a, b: a > b)
            else:
                predicate = (lambda a, b: b < a) if op == "<" else (lambda a, b: b > a)
            domain = {value for value in domain if any(predicate(value, other_value) for other_value in other_domain)}
        return tuple(sorted(domain))

    def is_consistent(self, state: FutoshikiState) -> bool:
        n = self.size
        for row in range(n):
            values = [v for v in state[row * n : (row + 1) * n] if v]
            if len(values) != len(set(values)):
                return False
        for col in range(n):
            values = [v for v in state[col::n] if v]
            if len(values) != len(set(values)):
                return False
        for left, op, right in self.inequalities:
            a, b = state[left], state[right]
            if a and b and not (a < b if op == "<" else a > b):
                return False
        return all(state[i] or self.domain(state, i) for i in range(n * n))

    def actions(self, state: FutoshikiState, emitter: Any = None, **kwargs: Any) -> Iterable[FutoshikiAction]:
        try:
            index = state.index(0)
        except ValueError:
            return ()
        domain_values = self.domain(state, index)
        r, c = divmod(index, self.size)
        if emitter is not None:
            emitter.emit(
                EventType.CELL_DOMAIN,
                state=state,
                cell=index,
                domain=domain_values,
                message=f"Xét ô hàng {r + 1}, cột {c + 1}: domain = {{{', '.join(map(str, domain_values))}}}",
                **kwargs,
            )
        if not domain_values:
            if emitter is not None:
                emitter.emit(
                    EventType.VALUE_REJECTED,
                    state=state,
                    cell=index,
                    domain=tuple(range(1, self.size + 1)),
                    reason="empty_domain",
                    message=f"Ô hàng {r + 1}, cột {c + 1} không còn số hợp lệ nào",
                    **kwargs,
                )
            return ()

        actions: list[FutoshikiAction] = []
        for value in domain_values:
            candidate = self.result(state, (index, value))
            if emitter is not None:
                emitter.emit(
                    EventType.VALUE_TRIED,
                    state=candidate,
                    cell=index,
                    value=value,
                    domain=domain_values,
                    action=(index, value),
                    message=f"Thử điền {value} vào ô hàng {r + 1}, cột {c + 1}",
                    **kwargs,
                )
            if self.is_consistent(candidate):
                actions.append((index, value))
            else:
                if emitter is not None:
                    emitter.emit(
                        EventType.VALUE_REJECTED,
                        state=state,
                        cell=index,
                        value=value,
                        domain=domain_values,
                        action=(index, value),
                        reason="conflict",
                        message=f"Loại {value} tại ô hàng {r + 1}, cột {c + 1} (vi phạm ràng buộc)",
                        **kwargs,
                    )
        return actions

    def result(self, state: FutoshikiState, action: FutoshikiAction) -> FutoshikiState:
        index, value = action
        if not 0 <= index < self.size * self.size or state[index] != 0:
            raise ValueError("Action targets a non-empty or invalid cell")
        if value not in range(1, self.size + 1):
            raise ValueError("Action value is outside the puzzle domain")
        values = list(state)
        values[index] = value
        return tuple(values)

    def is_goal(self, state: FutoshikiState) -> bool:
        if 0 in state or not self.is_consistent(state):
            return False
        expected = set(range(1, self.size + 1))
        return all(set(state[r * self.size : (r + 1) * self.size]) == expected for r in range(self.size)) and all(
            set(state[c::self.size]) == expected for c in range(self.size)
        )

    def heuristic(self, state: FutoshikiState) -> float:
        domains = [self.domain(state, i) for i, value in enumerate(state) if value == 0]
        empty = sum(not domain for domain in domains)
        risk = 0
        for left, op, right in self.inequalities:
            if state[left] and state[right]:
                continue
            left_values = self.domain(state, left) if not state[left] else (state[left],)
            right_values = self.domain(state, right) if not state[right] else (state[right],)
            feasible = sum((a < b if op == "<" else a > b) for a in left_values for b in right_values)
            risk += int(0 < feasible <= 2)
        return 1000 * empty + 10 * risk + sum(max(0, len(d) - 1) for d in domains) + len(domains)

