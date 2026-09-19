from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import FutoshikiProblem


class FutoshikiInputError(ValueError):
    pass


def _fail(field: str, message: str) -> None:
    raise FutoshikiInputError(f"{field}: {message}")


def parse_futoshiki(data: dict[str, Any]) -> FutoshikiProblem:
    if data.get("schema_version") != 1:
        _fail("schema_version", "must be 1")
    if data.get("puzzle") != "futoshiki":
        _fail("puzzle", "must be 'futoshiki'")
    puzzle_id = data.get("id")
    if not isinstance(puzzle_id, str) or not puzzle_id.strip():
        _fail("id", "must be a non-empty string")
    size = data.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size < 2:
        _fail("size", "must be an integer >= 2")
    givens = data.get("givens")
    if not isinstance(givens, list) or len(givens) != size:
        _fail("givens", f"must contain {size} rows")
    flat: list[int] = []
    for row_index, row in enumerate(givens):
        if not isinstance(row, list) or len(row) != size:
            _fail(f"givens[{row_index}]", f"must contain {size} values")
        for col_index, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= size:
                _fail(f"givens[{row_index}][{col_index}]", f"must be an integer in 0..{size}")
            flat.append(value)
    raw_inequalities = data.get("inequalities", [])
    if not isinstance(raw_inequalities, list):
        _fail("inequalities", "must be a list")
    inequalities: list[tuple[int, str, int]] = []
    seen: set[tuple[int, int]] = set()
    for i, item in enumerate(raw_inequalities):
        if not isinstance(item, dict):
            _fail(f"inequalities[{i}]", "must be an object")
        coords = []
        for name in ("left", "right"):
            coord = item.get(name)
            if not isinstance(coord, list) or len(coord) != 2 or any(
                not isinstance(x, int) or isinstance(x, bool) for x in coord
            ):
                _fail(f"inequalities[{i}].{name}", "must be [row, col]")
            row, col = coord
            if not (0 <= row < size and 0 <= col < size):
                _fail(f"inequalities[{i}].{name}", "coordinate out of range")
            coords.append(row * size + col)
        if coords[0] == coords[1]:
            _fail(f"inequalities[{i}]", "cannot reference the same cell")
        op = item.get("op")
        if op not in {"<", ">"}:
            _fail(f"inequalities[{i}].op", "must be '<' or '>'")
        if (coords[0], coords[1]) in seen:
            _fail(f"inequalities[{i}]", "duplicate relation")
        seen.add((coords[0], coords[1]))
        inequalities.append((coords[0], op, coords[1]))
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        _fail("metadata", "must be an object")
    problem = FutoshikiProblem(puzzle_id, size, tuple(flat), tuple(inequalities), metadata)
    if not problem.is_consistent(problem.initial_state):
        _fail("givens", "contains duplicate values, impossible inequality, or empty domain")
    return problem


def load_futoshiki(path: str | Path) -> FutoshikiProblem:
    try:
        with Path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise FutoshikiInputError(f"JSON line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise FutoshikiInputError(str(exc)) from exc
    if not isinstance(data, dict):
        raise FutoshikiInputError("root: must be an object")
    return parse_futoshiki(data)

