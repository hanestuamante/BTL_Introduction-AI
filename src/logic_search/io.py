from __future__ import annotations

import json
from pathlib import Path

from logic_search.puzzles.futoshiki.parser import parse_futoshiki
from logic_search.puzzles.pipes.parser import parse_pipes


def load_problem(path: str | Path, expected_puzzle: str | None = None):
    input_path = Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(data, dict):
        raise ValueError("root: must be an object")
    puzzle = data.get("puzzle")
    if expected_puzzle and puzzle != expected_puzzle:
        raise ValueError(f"puzzle: input is {puzzle!r}, expected {expected_puzzle!r}")
    if puzzle == "futoshiki":
        return parse_futoshiki(data)
    if puzzle == "pipes":
        return parse_pipes(data)
    raise ValueError("puzzle: must be 'pipes' or 'futoshiki'")

