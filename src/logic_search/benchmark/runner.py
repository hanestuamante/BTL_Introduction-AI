from __future__ import annotations

import multiprocessing as mp
import queue
import tracemalloc
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from logic_search.io import load_problem
from logic_search.search.solver import solve

from .metrics import environment_metadata


def _worker(path: str, algorithm: str, timeout: float, measure_memory: bool, output: mp.Queue) -> None:
    try:
        if measure_memory:
            tracemalloc.start()
        problem = load_problem(path)
        result = solve(problem, algorithm, timeout=timeout, detailed_events=False)
        peak = None
        if measure_memory:
            _current, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak = peak_bytes / 1024
        record = {"status": result.status, **asdict(result.metrics), "message": result.message}
        record["peak_python_memory_kib"] = peak
        output.put(record)
    except Exception as exc:
        output.put({"status": "error", "message": str(exc)})


def run_isolated(path: str | Path, algorithm: str, timeout: float, *, measure_memory: bool = False) -> dict[str, Any]:
    context = mp.get_context("spawn")
    output: mp.Queue = context.Queue()
    process = context.Process(target=_worker, args=(str(path), algorithm, timeout, measure_memory, output))
    process.start()
    process.join(timeout + 2)
    if process.is_alive():
        process.terminate()
        process.join(2)
        return {"status": "timeout", "message": f"Process timeout after {timeout:g} seconds"}
    try:
        return output.get(timeout=1)
    except queue.Empty:
        return {"status": "error", "message": f"Worker exited with code {process.exitcode} without a result"}


def run_benchmark(
    entries: Iterable[dict[str, Any]], algorithms: Iterable[str], repeats: int, timeout: float
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    environment = environment_metadata()
    for entry in entries:
        path = entry["path"]
        problem = load_problem(path)
        for algorithm in algorithms:
            # One unrecorded warm-up in its own process.
            run_isolated(path, algorithm, timeout)
            memory = run_isolated(path, algorithm, timeout, measure_memory=True)
            for repeat in range(repeats):
                timing = run_isolated(path, algorithm, timeout)
                size = str(problem.size) if hasattr(problem, "size") else f"{problem.rows}x{problem.cols}"
                record = {
                    "puzzle_id": problem.puzzle_id,
                    "puzzle": "futoshiki" if hasattr(problem, "size") else "pipes",
                    "size": size,
                    "difficulty": (problem.metadata or {}).get("difficulty", entry.get("difficulty", "unknown")),
                    "seed": (problem.metadata or {}).get("seed", ""),
                    "algorithm": algorithm,
                    "repeat": repeat + 1,
                    **environment,
                    **timing,
                }
                record["peak_python_memory_kib"] = memory.get("peak_python_memory_kib")
                records.append(record)
    return records
