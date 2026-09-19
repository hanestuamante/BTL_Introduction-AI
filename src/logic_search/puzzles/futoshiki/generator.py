from __future__ import annotations

import random
from typing import Any

from .model import FutoshikiProblem


def count_solutions(problem: FutoshikiProblem, limit: int = 2) -> int:
    count = 0

    def visit(state: tuple[int, ...]) -> None:
        nonlocal count
        if count >= limit:
            return
        if problem.is_goal(state):
            count += 1
            return
        empty = [i for i, value in enumerate(state) if value == 0]
        if not empty:
            return
        index = min(empty, key=lambda i: len(problem.domain(state, i)))
        for value in problem.domain(state, index):
            child = problem.result(state, (index, value))
            if problem.is_consistent(child):
                visit(child)

    visit(problem.initial_state)
    return count


def generate_futoshiki(size: int, seed: int, *, difficulty: str = "easy") -> dict[str, Any]:
    if size < 2:
        raise ValueError("size must be >= 2")
    rng = random.Random(seed)
    symbols = list(range(1, size + 1))
    rng.shuffle(symbols)
    row_order = list(range(size))
    col_order = list(range(size))
    rng.shuffle(row_order)
    rng.shuffle(col_order)
    solution = [[symbols[(row_order[r] + col_order[c]) % size] for c in range(size)] for r in range(size)]
    adjacent = []
    for row in range(size):
        for col in range(size - 1):
            adjacent.append(((row, col), (row, col + 1)))
    for row in range(size - 1):
        for col in range(size):
            adjacent.append(((row, col), (row + 1, col)))
    rng.shuffle(adjacent)
    relation_count = max(size, int(len(adjacent) * {"easy": .35, "medium": .25, "hard": .18}.get(difficulty, .25)))
    inequalities = []
    for left, right in adjacent[:relation_count]:
        a, b = solution[left[0]][left[1]], solution[right[0]][right[1]]
        inequalities.append({"left": list(left), "op": "<" if a < b else ">", "right": list(right)})
    givens = [row[:] for row in solution]
    positions = list(range(size * size))
    rng.shuffle(positions)
    target_blanks = int(size * size * {"easy": .45, "medium": .60, "hard": .72}.get(difficulty, .60))
    for position in positions:
        if sum(value == 0 for row in givens for value in row) >= target_blanks:
            break
        row, col = divmod(position, size)
        old = givens[row][col]
        givens[row][col] = 0
        candidate = {
            "schema_version": 1, "puzzle": "futoshiki", "id": "candidate", "size": size,
            "givens": givens, "inequalities": inequalities, "metadata": {},
        }
        from .parser import parse_futoshiki
        try:
            unique = count_solutions(parse_futoshiki(candidate), 2) == 1
        except ValueError:
            unique = False
        if not unique:
            givens[row][col] = old
    return {
        "schema_version": 1,
        "puzzle": "futoshiki",
        "id": f"futoshiki-{size}x{size}-{difficulty}-seed-{seed}",
        "size": size,
        "givens": givens,
        "inequalities": inequalities,
        "metadata": {"generator": "latin-square-v1", "seed": seed, "difficulty": difficulty},
    }

