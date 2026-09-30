#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from logic_search.puzzles.pipes.generator import generate_pipes


def write_stable(path: Path, data: dict) -> str:
    content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate reproducible, uniquely solvable Pipes inputs.")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "generated-pipes", help="Output directory (default: repository data/generated-pipes/).")
    parser.add_argument("--difficulty", nargs="+", choices=("easy", "medium", "hard"), default=["easy", "medium", "hard"], help="Levels to generate (default: all three).")
    parser.add_argument("--count", type=int, default=3, help="Pipes inputs per difficulty (default: 3).")
    parser.add_argument("--seed", type=int, help="Base seed; add 0/100/200 for Easy/Medium/Hard (default: 101).")
    parser.add_argument("--rows", type=int, help="Override Pipes rows (default: 3/4/5 by difficulty).")
    parser.add_argument("--cols", type=int, help="Override Pipes columns (default: 3/4/5 by difficulty).")
    parser.add_argument("--wrap", action="store_true", help="Generate Pipes with wrap-around; both dimensions must be >= 3.")
    parser.add_argument("--lock-ratio", type=float, default=0.0, metavar="0..1", help="Minimum fraction of Pipes cells locked to solution orientations; additional locks may ensure uniqueness (default: 0).")
    parser.add_argument("--candidates", type=int, default=8, help="Pipes candidates ranked for each input (default: 8).")
    parser.add_argument("--node-limit", type=int, default=20000, help="Pipes uniqueness-search node budget per attempt; add locks when exceeded (default: 20000).")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing generated files and benchmark_manifest.json.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 0 <= args.lock_ratio <= 1:
        parser.error("--lock-ratio must be between 0 and 1")
    for name in ("count", "candidates", "node_limit"):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    for name in ("rows", "cols"):
        value = getattr(args, name)
        if value is not None and value < 2:
            parser.error(f"--{name.replace('_', '-')} must be >= 2")
    levels = list(dict.fromkeys(args.difficulty))
    plans = []
    base_seed = args.seed if args.seed is not None else 101
    for difficulty in levels:
        level = ("easy", "medium", "hard").index(difficulty)
        for offset in range(args.count):
            seed = base_seed + 100 * level + offset
            rows, cols = args.rows or 3 + level, args.cols or 3 + level
            if args.wrap and (rows == 2 or cols == 2):
                parser.error("--wrap requires Pipes rows and cols >= 3")
            variant = ("-wrap" if args.wrap else "") + (f"-locks-{args.lock_ratio:g}" if args.lock_ratio else "")
            name = f"pipes-{rows}x{cols}-{difficulty}{variant}-seed-{seed}"
            plans.append((Path("pipes") / f"{name}.json", (rows, cols, seed), difficulty))
    paths = [relative for relative, *_ in plans]
    if len(paths) != len(set(paths)):
        parser.error("Seed ranges overlap; reduce --count to at most 100 when generating multiple levels")
    targets = [args.output / relative for relative in paths] + [args.output / "benchmark_manifest.json"]
    existing = [str(path) for path in targets if path.exists()]
    if existing and not args.overwrite:
        parser.error("Existing output files: " + ", ".join(existing[:4]) + ". Use another --output directory or --overwrite.")
    # Generate everything before writing, so validation failures do not replace part of a dataset.
    generated = []
    for relative, positional, difficulty in plans:
        try:
            data = generate_pipes(*positional, difficulty=difficulty, wrap=args.wrap,
                                  lock_ratio=args.lock_ratio, candidates=args.candidates, node_limit=args.node_limit)
        except ValueError as exc:
            parser.error(str(exc))
        generated.append((relative, difficulty, data))
    manifest = {"schema_version": 1, "inputs": []}
    for relative, difficulty, data in generated:
        checksum = write_stable(args.output / relative, data)
        manifest["inputs"].append({"path": relative.as_posix(), "difficulty": difficulty, "sha256": checksum})
        print(args.output / relative)
    write_stable(args.output / "benchmark_manifest.json", manifest)
    print(f"Generated {len(generated)} inputs in {args.output.resolve()}")
    print("Manifest lists this batch only; other files in the output directory are retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
