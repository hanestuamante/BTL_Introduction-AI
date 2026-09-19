#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from logic_search.cli import main


def run() -> int:
    return main(["benchmark", "--manifest", str(ROOT / "data/benchmark_manifest.json"), "--algorithms", "dfs", "gbfs", "--repeats", "10", "--timeout", "60", "--csv", str(ROOT / "results/raw/benchmark.csv"), "--json", str(ROOT / "results/raw/benchmark.json")])


if __name__ == "__main__":
    raise SystemExit(run())
