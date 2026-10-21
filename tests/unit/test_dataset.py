import hashlib
import json
from pathlib import Path

import pytest

from logic_search.io import load_problem
from logic_search.puzzles.pipes.generator import count_solutions


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("seed", [501, 502, 503])
def test_five_by_five_pipes_are_registered_and_uniquely_solvable(seed):
    manifest = json.loads((ROOT / "data/benchmark_manifest.json").read_text())
    relative = f"pipes/pipes-5x5-hard-wrap-seed-{seed}.json"
    entries = [entry for entry in manifest["inputs"] if entry["path"] == relative]
    assert len(entries) == 1
    path = ROOT / "data" / relative
    assert entries[0]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    problem = load_problem(path)
    assert (problem.rows, problem.cols, problem.wrap, problem.source_index) == (5, 5, True, 0)
    assert problem.metadata["difficulty"] == "hard"
    assert problem.metadata["seed"] == seed
    assert problem.metadata["requested_lock_ratio"] == 0.0
    assert problem.metadata["candidates"] == 24
    assert problem.metadata["node_limit"] == 20000
    assert count_solutions(problem, 2) == 1
