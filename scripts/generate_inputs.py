#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from logic_search.puzzles.futoshiki.generator import generate_futoshiki
from logic_search.puzzles.pipes.generator import generate_pipes


def write_stable(path: Path, data: dict) -> str:
    content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    specs = {
        "easy": ((3, 3), 4),
        "medium": ((4, 4), 5),
        "hard": ((5, 5), 6),
    }
    manifest = {"schema_version": 1, "inputs": []}
    for level_index, (difficulty, (pipe_size, futo_size)) in enumerate(specs.items()):
        for offset in range(3):
            pipe_seed = 101 + level_index * 100 + offset
            futo_seed = 201 + level_index * 100 + offset
            datasets = (
                ("pipes", generate_pipes(*pipe_size, pipe_seed, difficulty=difficulty)),
                ("futoshiki", generate_futoshiki(futo_size, futo_seed, difficulty=difficulty)),
            )
            for folder, data in datasets:
                relative = Path(folder) / f"{data['id']}.json"
                checksum = write_stable(args.output / relative, data)
                manifest["inputs"].append({"path": str(relative), "difficulty": difficulty, "sha256": checksum})
    write_stable(args.output / "benchmark_manifest.json", manifest)
    print(f"Generated {len(manifest['inputs'])} inputs in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

