import csv
import runpy
from pathlib import Path


summarize = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/summarize_results.py"))["summarize"]


def test_summary_separates_sizes_and_counts_memory_once_per_input(tmp_path):
    path = tmp_path / "raw.csv"
    rows = [
        {"puzzle_id": f"p{size}", "puzzle": "pipes", "size": size, "difficulty": "hard", "algorithm": "dfs", "status": "solved", "runtime_ms": repeat, "nodes_expanded": 10, "peak_python_memory_kib": 100, "memory_status": "solved"}
        for size in ("6x6", "7x7") for repeat in (1, 2)
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = summarize(path)
    assert [row["size"] for row in result] == ["6x6", "7x7"]
    assert all(row["runs"] == "2" and row["memory_samples"] == "1" for row in result)
