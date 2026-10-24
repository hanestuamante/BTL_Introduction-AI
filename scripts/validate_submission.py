#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
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
    if len(entries) < 21:
        errors.append(f"Manifest has {len(entries)} inputs; expected at least 21")
    groups: Counter[tuple[str, int, str]] = Counter()
    ids: set[str] = set()
    for entry in entries:
        path = manifest_path.parent / entry["path"]
        try:
            raw_bytes = path.read_bytes()
            normalized_bytes = raw_bytes.replace(b"\r\n", b"\n")
            digest = hashlib.sha256(normalized_bytes).hexdigest()
            if digest != entry.get("sha256") and hashlib.sha256(raw_bytes).hexdigest() != entry.get("sha256"):
                errors.append(f"Checksum mismatch: {path}")
            problem = load_problem(path)
            puzzle = "futoshiki" if hasattr(problem, "size") else "pipes"
            size = problem.size if puzzle == "futoshiki" else problem.rows if problem.rows == problem.cols else 0
            difficulty = (problem.metadata or {}).get("difficulty", entry.get("difficulty", "unknown"))
            groups[(puzzle, size, difficulty)] += 1
            if problem.puzzle_id in ids:
                errors.append(f"Duplicate ID: {problem.puzzle_id}")
            ids.add(problem.puzzle_id)
            counter = count_futoshiki if hasattr(problem, "size") else count_pipes
            solutions = counter(problem, 2)
            if solutions != 1:
                errors.append(f"Expected one solution, got {solutions}: {path}")
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    expected = [("futoshiki", 4, "easy"), ("futoshiki", 5, "medium"), ("futoshiki", 6, "hard")]
    expected.extend(("pipes", size, "hard") for size in (5, 6, 7, 8))
    for puzzle, size, difficulty in expected:
        count = groups[(puzzle, size, difficulty)]
        if count < 3:
            errors.append(f"Expected at least 3 {puzzle} {size}x{size} {difficulty} inputs, got {count}")
    if errors:
        print("Submission validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(entries)} unique, checksummed inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

