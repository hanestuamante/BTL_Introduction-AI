from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .model import BASE_MASKS, PipesProblem, orientations


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
    if data.get("wrap", False) is not False:
        _fail("wrap", "only false is supported")
    rows, cols = data.get("rows"), data.get("cols")
    if any(not isinstance(x, int) or isinstance(x, bool) or x < 2 for x in (rows, cols)):
        _fail("rows/cols", "must be integers >= 2")
    tiles = data.get("tiles")
    rotations = data.get("initial_rotations")
    if not isinstance(tiles, list) or len(tiles) != rows:
        _fail("tiles", f"must contain {rows} rows")
    if not isinstance(rotations, list) or len(rotations) != rows:
        _fail("initial_rotations", f"must contain {rows} rows")
    flat_tiles: list[str] = []
    flat_rotations: list[int] = []
    for row in range(rows):
        if not isinstance(tiles[row], list) or len(tiles[row]) != cols:
            _fail(f"tiles[{row}]", f"must contain {cols} values")
        if not isinstance(rotations[row], list) or len(rotations[row]) != cols:
            _fail(f"initial_rotations[{row}]", f"must contain {cols} values")
        for col in range(cols):
            tile = tiles[row][col]
            rotation = rotations[row][col]
            if tile not in BASE_MASKS:
                _fail(f"tiles[{row}][{col}]", f"unknown tile {tile!r}")
            if not isinstance(rotation, int) or isinstance(rotation, bool) or not 0 <= rotation <= 3:
                _fail(f"initial_rotations[{row}][{col}]", "must be an integer in 0..3")
            if rotation >= len(orientations(tile)) and tile in {"STRAIGHT", "CROSS"}:
                # Rotations 2/3 are legal physical turns even if equivalent; normalize below.
                pass
            flat_tiles.append(tile)
            flat_rotations.append(rotation)
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        _fail("metadata", "must be an object")
    problem = PipesProblem(puzzle_id, rows, cols, tuple(flat_tiles), tuple(flat_rotations), metadata)
    if any(not problem.domain(problem.initial_state, i) for i in range(rows * cols)):
        _fail("tiles", "at least one border tile has no legal orientation")
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

