from __future__ import annotations

from logic_search.puzzles.pipes.model import BASE_MASKS, DIRECTIONS, rotate_mask


def initial_play_state(problem) -> tuple[int, ...]:
    if hasattr(problem, "size"):
        return problem.givens
    return tuple(
        rotate_mask(BASE_MASKS[tile], rotation)
        for tile, rotation in zip(problem.tiles, problem.initial_rotations)
    )


def set_futoshiki_value(problem, state: tuple[int, ...], index: int, value: int) -> tuple[int, ...]:
    if not 0 <= index < len(state):
        return state
    if problem.givens[index] or not 0 <= value <= problem.size:
        return state
    values = list(state)
    values[index] = value
    return tuple(values)


def rotate_pipe(problem, state: tuple[int, ...], index: int, turns: int = 1) -> tuple[int, ...]:
    if not 0 <= index < len(state):
        return state
    values = list(state)
    values[index] = rotate_mask(values[index], turns)
    return tuple(values)


def futoshiki_conflicts(problem, state: tuple[int, ...]) -> set[int]:
    conflicts: set[int] = set()
    n = problem.size
    for row in range(n):
        positions: dict[int, list[int]] = {}
        for index in range(row * n, (row + 1) * n):
            if state[index]:
                positions.setdefault(state[index], []).append(index)
        conflicts.update(i for group in positions.values() if len(group) > 1 for i in group)
    for col in range(n):
        positions = {}
        for index in range(col, n * n, n):
            if state[index]:
                positions.setdefault(state[index], []).append(index)
        conflicts.update(i for group in positions.values() if len(group) > 1 for i in group)
    for left, op, right in problem.inequalities:
        a, b = state[left], state[right]
        if a and b and not (a < b if op == "<" else a > b):
            conflicts.update((left, right))
    return conflicts


def pipes_conflicts(problem, state: tuple[int, ...]) -> set[int]:
    conflicts: set[int] = set()
    for index, mask in enumerate(state):
        for direction in DIRECTIONS:
            neighbor = problem.neighbor(index, direction)
            bit, opposite = direction[2], direction[3]
            if neighbor is None:
                if mask & bit:
                    conflicts.add(index)
            elif bool(mask & bit) != bool(state[neighbor] & opposite):
                conflicts.update((index, neighbor))
    if not conflicts and not problem.is_goal(state):
        conflicts.update(range(len(state)))
    return conflicts

