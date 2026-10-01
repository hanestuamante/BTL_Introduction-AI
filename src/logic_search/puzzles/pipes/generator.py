from __future__ import annotations

import random
from typing import Any

from logic_search.core.cancellation import CancellationToken
from logic_search.core.events import EventType
from logic_search.search.solver import solve

from .model import BASE_MASKS, DIRECTIONS, PipesProblem, orientations, rotate_mask

MASK_TO_TILE = {1: "END", 2: "END", 4: "END", 8: "END", 5: "STRAIGHT", 10: "STRAIGHT", 3: "CORNER", 6: "CORNER", 12: "CORNER", 9: "CORNER", 7: "TEE", 14: "TEE", 13: "TEE", 11: "TEE", 15: "CROSS"}


def _solutions(problem: PipesProblem, limit: int = 2, *, node_limit: int | None = None):
    solutions: list[tuple[int, ...]] = []
    nodes = 0

    def visit(state: tuple[int, ...]) -> None:
        nonlocal nodes
        if len(solutions) >= limit:
            return
        nodes += 1
        if node_limit is not None and nodes > node_limit:
            raise ValueError("Generation search budget exceeded; try a smaller grid or more locks")
        empty = [i for i, value in enumerate(state) if not value]
        if not empty:
            if problem.is_goal(state):
                solutions.append(state)
            return
        index = min(empty, key=lambda i: (len(problem.domain(state, i)), i))
        for mask in problem.domain(state, index):
            child = problem.result(state, (index, mask))
            if problem.is_consistent(child):
                visit(child)

    visit(problem.initial_state)
    return solutions, nodes


def count_solutions(problem: PipesProblem, limit: int = 2) -> int:
    return len(_solutions(problem, limit)[0])


def _neighbor(index, direction, rows, cols, wrap):
    row, col = divmod(index, cols)
    nr, nc = row + direction[0], col + direction[1]
    if wrap:
        return (nr % rows) * cols + nc % cols
    return nr * cols + nc if 0 <= nr < rows and 0 <= nc < cols else None


def _tree_masks(rows: int, cols: int, rng: random.Random, *, wrap: bool = False) -> list[int]:
    edges = []
    for index in range(rows * cols):
        row, col = divmod(index, cols)
        for direction in (DIRECTIONS[1], DIRECTIONS[2]):
            neighbor = _neighbor(index, direction, rows, cols, wrap)
            if neighbor is not None:
                seam = col == cols - 1 if direction[2] == 2 else row == rows - 1
                edges.append((index, neighbor, direction[2], direction[3], seam))
    rng.shuffle(edges)
    if wrap:
        seam = next(edge for edge in edges if edge[4])
        edges.remove(seam)
        edges.insert(0, seam)
    parent = list(range(rows * cols))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    masks = [0] * (rows * cols)
    for a, b, bit, opposite, _seam in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            masks[a] |= bit
            masks[b] |= opposite
    return masks


def _rotation_for_mask(tile: str, mask: int) -> int:
    return next(turns for turns in range(4) if rotate_mask(BASE_MASKS[tile], turns) == mask)


def _search_effort(problem: PipesProblem, algorithm: str, budget: int) -> dict[str, Any]:
    token = CancellationToken()

    def observe(event):
        if event.type == EventType.NODE_EXPANDED and event.nodes_expanded >= budget:
            token.cancel()

    result = solve(problem, algorithm, timeout=None, cancellation=token, on_event=observe)
    return {
        "status": result.status,
        "nodes_expanded": result.metrics.nodes_expanded,
        "nodes_pruned": result.metrics.nodes_pruned,
        "max_frontier_size": result.metrics.max_frontier_size,
        "solution_depth": result.metrics.solution_depth,
    }


def generate_pipes(
    rows: int,
    cols: int,
    seed: int,
    *,
    difficulty: str = "hard",
    wrap: bool = False,
    lock_ratio: float = 0.0,
    candidates: int = 24,
    node_limit: int = 20000,
) -> dict[str, Any]:
    if rows < 2 or cols < 2:
        raise ValueError("rows and cols must be >= 2")
    if wrap and (rows == 2 or cols == 2):
        raise ValueError("wrap is not supported when rows == 2 or cols == 2")
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium or hard")
    if not 0 <= lock_ratio <= 1:
        raise ValueError("lock_ratio must be between 0 and 1")
    if candidates < 1 or node_limit < 1:
        raise ValueError("candidates and node_limit must be positive")
    rng = random.Random(seed)
    pool = []
    size = rows * cols
    for candidate in range(candidates):
        masks = _tree_masks(rows, cols, rng, wrap=wrap)
        tiles = tuple(MASK_TO_TILE[mask] for mask in masks)
        rotations = [rng.randrange(4) for _ in masks]
        locked = set(rng.sample(range(size), round(lock_ratio * size)))
        requested = len(locked)
        while True:
            problem = PipesProblem("candidate", rows, cols, tiles, tuple(rotations), wrap=wrap,
                                   locked_mask=tuple(masks[i] if i in locked else 0 for i in range(size)))
            try:
                solutions, effort = _solutions(problem, node_limit=node_limit)
            except ValueError:
                unlocked = [i for i in range(size) if i not in locked]
                locked.add(rng.choice(unlocked))
                continue
            if len(solutions) == 1:
                break
            alternate = next(state for state in solutions if state != tuple(masks))
            choices = [i for i in range(size) if alternate[i] != masks[i] and i not in locked]
            locked.add(rng.choice(choices))
        scramble_ratio = {"easy": 0.45, "medium": 0.7, "hard": 1.0}[difficulty]
        movable = [i for i in range(size) if i not in locked and len(orientations(tiles[i])) > 1]
        scrambled = set(rng.sample(movable, round(len(movable) * scramble_ratio)))
        for i in range(size):
            target = rng.choice([mask for mask in orientations(tiles[i]) if mask != masks[i]]) if i in scrambled else masks[i]
            rotations[i] = _rotation_for_mask(tiles[i], target)
        problem = PipesProblem("candidate", rows, cols, tiles, tuple(rotations), wrap=wrap,
                               locked_mask=tuple(masks[i] if i in locked else 0 for i in range(size)))
        ambiguity = sum(max(0, len(problem.domain(problem.initial_state, i)) - 1)
                        for i in range(size) if i not in locked)
        search_budget = min(node_limit, 2000)
        solver_effort = {algorithm: _search_effort(problem, algorithm, search_budget) for algorithm in ("dfs", "gbfs")}
        expanded = [metrics["nodes_expanded"] for metrics in solver_effort.values()]
        score = min(expanded) + sum(expanded) / 10
        pool.append((score, candidate, masks, tiles, rotations, locked, requested, effort, ambiguity, scrambled, solver_effort))
    pool.sort(key=lambda item: (item[0], item[1]))
    rank = {"easy": 0, "medium": len(pool) // 2, "hard": len(pool) - 1}[difficulty]
    score, _, masks, tiles, rotations, locked, requested, effort, ambiguity, scrambled, solver_effort = pool[rank]
    variant = ("-wrap" if wrap else "") + (f"-locks-{lock_ratio:g}" if lock_ratio else "")
    result: dict[str, Any] = {
        "schema_version": 1,
        "puzzle": "pipes",
        "id": f"pipes-{rows}x{cols}-{difficulty}{variant}-seed-{seed}",
        "rows": rows, "cols": cols, "wrap": wrap,
        "tiles": [list(tiles[r * cols:(r + 1) * cols]) for r in range(rows)],
        "initial_rotations": [rotations[r * cols:(r + 1) * cols] for r in range(rows)],
        "metadata": {
            "generator": "kruskal-solver-ranked-unique-v3", "seed": seed, "difficulty": difficulty,
            "candidates": candidates, "node_limit": node_limit, "difficulty_score": score,
            "solver_effort": solver_effort, "solver_node_budget": search_budget,
            "difficulty_method": "min_expanded_plus_total_expanded_div_10",
            "uniqueness_nodes": effort, "initial_ambiguity": ambiguity,
            "scrambled_cells": len(scrambled), "scramble_ratio": scramble_ratio,
            "requested_lock_ratio": lock_ratio, "requested_locked_count": requested,
            "actual_locked_count": len(locked), "unique_solution": True,
        },
    }
    if locked:
        result["locked"] = [[r * cols + c in locked for c in range(cols)] for r in range(rows)]
        result["metadata"]["locked_cells"] = [list(divmod(i, cols)) for i in sorted(locked)]
    return result
