from pathlib import Path

from logic_search.benchmark.runner import run_isolated

ROOT = Path(__file__).resolve().parents[2]


def test_isolated_benchmark_worker_returns_metrics():
    result = run_isolated(
        ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json", "dfs", 5
    )
    assert result["status"] == "solved"
    assert result["nodes_expanded"] > 0
