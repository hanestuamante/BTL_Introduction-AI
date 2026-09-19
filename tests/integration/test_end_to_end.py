from pathlib import Path

import pytest

from logic_search.io import load_problem
from logic_search.search.solver import solve

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("relative", ["data/futoshiki/futoshiki-4x4-easy-seed-201.json", "data/pipes/pipes-3x3-easy-seed-101.json"])
@pytest.mark.parametrize("algorithm", ["dfs", "gbfs"])
def test_solver_handles_sample_inputs(relative, algorithm):
    problem = load_problem(ROOT / relative)
    result = solve(problem, algorithm, timeout=10)
    assert result.status == "solved", result.message
    assert problem.is_goal(result.path[-1])
    assert len(result.actions) == len(result.path) - 1
