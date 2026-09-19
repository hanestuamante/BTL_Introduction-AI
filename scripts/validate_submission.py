#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from logic_search.io import load_problem
from logic_search.puzzles.futoshiki.generator import count_solutions as count_futoshiki
from logic_search.puzzles.pipes.generator import count_solutions as count_pipes


def main() -> int:
    errors: list[str] = []
    manifest_path = ROOT / "data/benchmark_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid manifest: {exc}", file=sys.stderr)
        return 1
    entries = manifest.get("inputs", [])
    if len(entries) < 18:
        errors.append(f"Manifest has {len(entries)} inputs; expected at least 18")
    ids: set[str] = set()
    for entry in entries:
        path = manifest_path.parent / entry["path"]
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != entry.get("sha256"):
                errors.append(f"Checksum mismatch: {path}")
            problem = load_problem(path)
            if problem.puzzle_id in ids:
                errors.append(f"Duplicate ID: {problem.puzzle_id}")
            ids.add(problem.puzzle_id)
            counter = count_futoshiki if hasattr(problem, "size") else count_pipes
            solutions = counter(problem, 2)
            if solutions != 1:
                errors.append(f"Expected one solution, got {solutions}: {path}")
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    if errors:
        print("Submission validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(entries)} unique, checksummed inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

