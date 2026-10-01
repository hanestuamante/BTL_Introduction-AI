from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import BASE_MASKS, PipesProblem, orientations, rotate_mask


class PipesInputError(ValueError):
    pass


def _fail(field: str, message: str) -> None:
    raise PipesInputError(f"{field}: {message}")


def parse_pipes(data: dict[str, Any]) -> PipesProblem:
    if data.get("schema_version") != 1:
        _fail("schema_version", "must be 1")
    if data.get("puzzle") != "pipes":
        _fail("puzzle", "must be 'pipes'")
    puzzle_id = data.get("id")
    if not isinstance(puzzle_id, str) or not puzzle_id.strip():
        _fail("id", "must be a non-empty string")
    wrap = data.get("wrap", False)
    if not isinstance(wrap, bool):
        _fail("wrap", "must be a boolean")
    rows, cols = data.get("rows"), data.get("cols")
    if any(not isinstance(x, int) or isinstance(x, bool) or x < 2 for x in (rows, cols)):
        _fail("rows/cols", "must be integers >= 2")
    if wrap and (rows == 2 or cols == 2):
        _fail("wrap", "wrap is not supported when rows == 2 or cols == 2")
    tiles = data.get("tiles")
    rotations = data.get("initial_rotations")
    locked = data.get("locked")
    if not isinstance(tiles, list) or len(tiles) != rows:
        _fail("tiles", f"must contain {rows} rows")
    if not isinstance(rotations, list) or len(rotations) != rows:
        _fail("initial_rotations", f"must contain {rows} rows")
    if locked is not None and (not isinstance(locked, list) or len(locked) != rows):
        _fail("locked", f"must contain {rows} rows")
    flat_tiles: list[str] = []
    flat_rotations: list[int] = []
    flat_locked: list[int] = []
    any_locked = False
    for row in range(rows):
        if not isinstance(tiles[row], list) or len(tiles[row]) != cols:
            _fail(f"tiles[{row}]", f"must contain {cols} values")
        if not isinstance(rotations[row], list) or len(rotations[row]) != cols:
            _fail(f"initial_rotations[{row}]", f"must contain {cols} values")
        if locked is not None and (not isinstance(locked[row], list) or len(locked[row]) != cols):
            _fail(f"locked[{row}]", f"must contain {cols} values")
        for col in range(cols):
            tile = tiles[row][col]
            rotation = rotations[row][col]
            if tile not in BASE_MASKS:
                _fail(f"tiles[{row}][{col}]", f"unknown tile {tile!r}")
            if not isinstance(rotation, int) or isinstance(rotation, bool) or not 0 <= rotation <= 3:
                _fail(f"initial_rotations[{row}][{col}]", "must be an integer in 0..3")
            is_locked = False
            if locked is not None:
                is_locked = locked[row][col]
                if not isinstance(is_locked, bool):
                    _fail(f"locked[{row}][{col}]", "must be a boolean")
            flat_tiles.append(tile)
            flat_rotations.append(rotation)
            if is_locked:
                any_locked = True
                flat_locked.append(rotate_mask(BASE_MASKS[tile], rotation))
            else:
                flat_locked.append(0)
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        _fail("metadata", "must be an object")

    source_field = data.get("source")
    source: int | None
    if source_field is None:
        source = None
    elif isinstance(source_field, list):
        if len(source_field) != 2 or not all(isinstance(v, int) and not isinstance(v, bool) for v in source_field):
            _fail("source", "must be [row, col] of integers")
        source_row, source_col = source_field
        if not (0 <= source_row < rows and 0 <= source_col < cols):
            _fail("source", "is outside the grid")
        source = source_row * cols + source_col
    elif isinstance(source_field, int) and not isinstance(source_field, bool):
        if not 0 <= source_field < rows * cols:
            _fail("source", "is outside the grid")
        source = source_field
    else:
        _fail("source", "must be an integer index or [row, col]")

    problem = PipesProblem(
        puzzle_id,
        rows,
        cols,
        tuple(flat_tiles),
        tuple(flat_rotations),
        metadata,
        wrap=wrap,
        locked_mask=tuple(flat_locked) if any_locked else None,
        source=source,
    )
    if any(not problem.domain(problem.initial_state, i) for i in range(rows * cols)):
        _fail("tiles", "at least one border tile has no legal orientation")
    if not problem.is_consistent(problem.initial_state):
        _fail("locked", "locked cells conflict with each other or with the grid boundary")
    return problem


def load_pipes(path: str | Path) -> PipesProblem:
    try:
        with Path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise PipesInputError(f"JSON line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise PipesInputError(str(exc)) from exc
    if not isinstance(data, dict):
        raise PipesInputError("root: must be an object")
    return parse_pipes(data)
