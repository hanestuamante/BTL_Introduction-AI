from __future__ import annotations

import random
from typing import Any

from .model import BASE_MASKS, DIRECTIONS, PipesProblem, rotate_mask

MASK_TO_TILE = {1: "END", 2: "END", 4: "END", 8: "END", 5: "STRAIGHT", 10: "STRAIGHT", 3: "CORNER", 6: "CORNER", 12: "CORNER", 9: "CORNER", 7: "TEE", 14: "TEE", 13: "TEE", 11: "TEE", 15: "CROSS"}


def count_solutions(problem: PipesProblem, limit: int = 2) -> int:
    count = 0

    def visit(state: tuple[int, ...]) -> None:
        nonlocal count
        if count >= limit:
            return
        if problem.is_goal(state):
            count += 1
            return
        try:
            index = state.index(0)
        except ValueError:
            return
        for mask in problem.domain(state, index):
            child = problem.result(state, (index, mask))
            if problem.is_consistent(child):
                visit(child)

    visit(problem.initial_state)
    return count


def _tree_masks(rows: int, cols: int, rng: random.Random) -> list[int]:
    masks = [0] * (rows * cols)
    seen = {0}
    stack = [0]
    while stack:
        index = stack[-1]
        choices = []
        for direction in DIRECTIONS:
            row, col = divmod(index, cols)
            nr, nc = row + direction[0], col + direction[1]
            if 0 <= nr < rows and 0 <= nc < cols and nr * cols + nc not in seen:
                choices.append((direction, nr * cols + nc))
        if not choices:
            stack.pop()
            continue
        direction, neighbor = rng.choice(choices)
        masks[index] |= direction[2]
        masks[neighbor] |= direction[3]
        seen.add(neighbor)
        stack.append(neighbor)
    return masks


def generate_pipes(rows: int, cols: int, seed: int, *, difficulty: str = "easy") -> dict[str, Any]:
    if rows < 2 or cols < 2:
        raise ValueError("rows and cols must be >= 2")
    rng = random.Random(seed)
    masks = _tree_masks(rows, cols, rng)
    tiles = [[MASK_TO_TILE[masks[r * cols + c]] for c in range(cols)] for r in range(rows)]
    rotations = [[rng.randrange(4) for _ in range(cols)] for _ in range(rows)]
    return {
        "schema_version": 1,
        "puzzle": "pipes",
        "id": f"pipes-{rows}x{cols}-{difficulty}-seed-{seed}",
        "rows": rows,
        "cols": cols,
        "wrap": False,
        "tiles": tiles,
        "initial_rotations": rotations,
        "metadata": {"generator": "spanning-tree-v1", "seed": seed, "difficulty": difficulty},
    }

