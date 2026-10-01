from pathlib import Path

from logic_search.benchmark.runner import run_isolated

ROOT = Path(__file__).resolve().parents[2]


def test_isolated_benchmark_worker_returns_metrics():
    result = run_isolated(
        ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json", "dfs", 5
    )
    assert result["status"] == "solved"
    assert result["nodes_expanded"] > 0


def test_memory_measurement_excludes_input_loading(monkeypatch):
    import queue
    import tracemalloc
    from logic_search.benchmark import runner

    original = runner.load_problem

    def load_with_temporary_allocation(path):
        allocation = bytearray(2_000_000)
        problem = original(path)
        assert len(allocation) == 2_000_000
        return problem

    monkeypatch.setattr(runner, "load_problem", load_with_temporary_allocation)
    output = queue.Queue()
    try:
        runner._worker(str(ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json"), "dfs", 5, True, output)
        result = output.get_nowait()
        assert result["status"] == "solved"
        assert 0 < result["peak_python_memory_kib"] < 500
    finally:
        tracemalloc.stop()


def test_failed_memory_run_is_not_attached_as_solved_memory(monkeypatch):
    from logic_search.benchmark import runner

    def isolated(path, algorithm, timeout, *, measure_memory=False):
        if measure_memory:
            return {"status": "timeout", "peak_python_memory_kib": 123, "message": "Memory run timed out"}
        return {"status": "solved", "runtime_ms": 1}

    monkeypatch.setattr(runner, "run_isolated", isolated)
    rows = runner.run_benchmark([{"path": ROOT / "data/futoshiki/futoshiki-4x4-easy-seed-201.json"}], ["dfs"], 1, 5)
    assert rows[0]["memory_status"] == "timeout"
    assert rows[0]["peak_python_memory_kib"] is None
    assert rows[0]["memory_scope"] == "search_python_allocations"
