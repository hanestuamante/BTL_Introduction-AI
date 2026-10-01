from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

N, E, S, W = 1, 2, 4, 8
DIRECTIONS = ((-1, 0, N, S), (0, 1, E, W), (1, 0, S, N), (0, -1, W, E))
BASE_MASKS = {"END": N, "STRAIGHT": N | S, "CORNER": N | E, "TEE": N | E | S, "CROSS": N | E | S | W}

PipesState = tuple[int, ...]
PipesAction = tuple[int, int]


def rotate_mask(mask: int, turns: int = 1) -> int:
    turns %= 4
    for _ in range(turns):
        mask = ((mask << 1) & 0b1111) | ((mask >> 3) & 1)
    return mask


def orientations(tile: str) -> tuple[int, ...]:
    base = BASE_MASKS[tile]
    return tuple(dict.fromkeys(rotate_mask(base, turns) for turns in range(4)))


@dataclass(frozen=True, slots=True)
class PipesProblem:
    puzzle_id: str
    rows: int
    cols: int
    tiles: tuple[str, ...]
    initial_rotations: tuple[int, ...]
    metadata: dict | None = None
    wrap: bool = False
    locked_mask: tuple[int, ...] | None = None
    source: int | None = None

    @property
    def source_index(self) -> int:
        if self.source is not None:
            return self.source
        return (self.rows // 2) * self.cols + (self.cols // 2)

    @property
    def initial_state(self) -> PipesState:
        if self.locked_mask is None:
            return (0,) * (self.rows * self.cols)
        return self.locked_mask

    def state_key(self, state: PipesState) -> PipesState:
        return state

    def is_locked(self, index: int) -> bool:
        return self.locked_mask is not None and self.locked_mask[index] != 0

    def neighbor(self, index: int, direction: tuple[int, int, int, int]) -> int | None:
        row, col = divmod(index, self.cols)
        dr, dc, _bit, _opposite = direction
        nr, nc = row + dr, col + dc
        if self.wrap:
            nr %= self.rows
            nc %= self.cols
            return nr * self.cols + nc
        return nr * self.cols + nc if 0 <= nr < self.rows and 0 <= nc < self.cols else None

    def _locally_valid(self, state: PipesState, index: int, mask: int) -> bool:
        for direction in DIRECTIONS:
            _dr, _dc, bit, opposite = direction
            neighbor = self.neighbor(index, direction)
            if neighbor is None:
                if mask & bit:
                    return False
                continue
            neighbor_mask = state[neighbor]
            if neighbor_mask and bool(mask & bit) != bool(neighbor_mask & opposite):
                return False
        return True

    def domain(self, state: PipesState, index: int) -> tuple[int, ...]:
        if state[index]:
            return (state[index],)
        values = list(orientations(self.tiles[index]))
        preferred = rotate_mask(BASE_MASKS[self.tiles[index]], self.initial_rotations[index])
        values.sort(key=lambda value: (value != preferred, value))
        return tuple(mask for mask in values if self._locally_valid(state, index, mask))

    def _has_assigned_cycle(self, state: PipesState) -> bool:
        parent = list(range(len(state)))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> bool:
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            parent[ra] = rb
            return True

        seen_edges: set[frozenset[int]] = set()
        for index, mask in enumerate(state):
            if not mask:
                continue
            for direction in DIRECTIONS:
                neighbor = self.neighbor(index, direction)
                bit, opposite = direction[2], direction[3]
                if neighbor is None or not (mask & bit) or not state[neighbor] or not (state[neighbor] & opposite):
                    continue
                edge = frozenset((index, neighbor))
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                if not union(index, neighbor):
                    return True
        return False

    def is_consistent(self, state: PipesState) -> bool:
        if len(state) != self.rows * self.cols:
            return False
        for index, mask in enumerate(state):
            if mask and (mask not in orientations(self.tiles[index]) or not self._locally_valid(state, index, mask)):
                return False
            if self.is_locked(index) and mask != self.locked_mask[index]:
                return False
        if self._has_assigned_cycle(state):
            return False
        # Forward-check both ends of every undecided adjacency.
        for index, mask in enumerate(state):
            if not mask and not self.domain(state, index):
                return False
        for index, mask in enumerate(state):
            if mask:
                continue
            for direction in DIRECTIONS:
                neighbor = self.neighbor(index, direction)
                if neighbor is None or state[neighbor]:
                    continue
                bit, opposite = direction[2], direction[3]
                if not any(bool(a & bit) == bool(b & opposite) for a in self.domain(state, index) for b in self.domain(state, neighbor)):
                    return False
        return True

    def actions(self, state: PipesState) -> Iterable[PipesAction]:
        try:
            index = state.index(0)
        except ValueError:
            return ()
        valid: list[PipesAction] = []
        for mask in self.domain(state, index):
            child = self.result(state, (index, mask))
            if self.is_consistent(child):
                valid.append((index, mask))
        return valid

    def result(self, state: PipesState, action: PipesAction) -> PipesState:
        index, mask = action
        if not 0 <= index < len(state) or state[index]:
            raise ValueError("Action targets a non-empty or invalid cell")
        if mask not in orientations(self.tiles[index]):
            raise ValueError("Mask is not an orientation of this tile")
        if self.is_locked(index) and mask != self.locked_mask[index]:
            raise ValueError("Action targets a locked cell with a different mask")
        values = list(state)
        values[index] = mask
        return tuple(values)

    def is_goal(self, state: PipesState) -> bool:
        if 0 in state or not self.is_consistent(state):
            return False
        seen = {0}
        stack = [0]
        edges = 0
        while stack:
            index = stack.pop()
            mask = state[index]
            for direction in DIRECTIONS:
                neighbor = self.neighbor(index, direction)
                bit, opposite = direction[2], direction[3]
                if mask & bit:
                    if neighbor is None or not state[neighbor] & opposite:
                        return False
                    if neighbor > index:
                        edges += 1
                    if neighbor not in seen:
                        seen.add(neighbor)
                        stack.append(neighbor)
        return len(seen) == len(state) and edges == len(state) - 1

    def heuristic(self, state: PipesState) -> float:
        unassigned = [i for i, value in enumerate(state) if not value]
        domains = [self.domain(state, i) for i in unassigned]
        dead = sum(not domain for domain in domains)
        assigned = {i for i, value in enumerate(state) if value}
        components = 0
        while assigned:
            components += 1
            stack = [assigned.pop()]
            while stack:
                index = stack.pop()
                for direction in DIRECTIONS:
                    neighbor = self.neighbor(index, direction)
                    if neighbor in assigned and state[index] & direction[2] and state[neighbor] & direction[3]:
                        assigned.remove(neighbor)
                        stack.append(neighbor)
        return 1000 * dead + 5 * max(0, components - 1) + sum(max(0, len(d) - 1) for d in domains) + len(unassigned)
