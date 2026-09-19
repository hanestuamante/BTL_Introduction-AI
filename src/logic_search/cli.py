from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from logic_search.benchmark.export import write_csv, write_json
from logic_search.benchmark.runner import run_benchmark
from logic_search.io import load_problem
from logic_search.search.solver import solve


def _solve(args: argparse.Namespace) -> int:
    try:
        problem = load_problem(args.input, args.puzzle)
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2
    result = solve(problem, args.algorithm, timeout=args.timeout, detailed_events=False)
    payload = {
        "puzzle_id": problem.puzzle_id,
        "puzzle": args.puzzle,
        "algorithm": args.algorithm,
        **result.to_dict(),
    }
    if args.output:
        write_json(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return {"solved": 0, "unsolved": 1, "timeout": 3}.get(result.status, 4)


def _benchmark(args: argparse.Namespace) -> int:
    try:
        manifest_path = Path(args.manifest)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest["inputs"] if isinstance(manifest, dict) else manifest
        for entry in entries:
            candidate = Path(entry["path"])
            if not candidate.is_absolute():
                entry["path"] = str((manifest_path.parent / candidate).resolve())
        records = run_benchmark(entries, args.algorithms, args.repeats, args.timeout)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Benchmark error: {exc}", file=sys.stderr)
        return 2
    write_csv(args.csv, records)
    if args.json:
        write_json(args.json, records)
    print(f"Wrote {len(records)} runs to {args.csv}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="logic-search")
    subparsers = parser.add_subparsers(dest="command", required=True)
    solve_parser = subparsers.add_parser("solve", help="Solve one JSON puzzle")
    solve_parser.add_argument("--puzzle", choices=("pipes", "futoshiki"), required=True)
    solve_parser.add_argument("--input", required=True)
    solve_parser.add_argument("--algorithm", choices=("dfs", "gbfs"), default="dfs")
    solve_parser.add_argument("--timeout", type=float, default=60.0)
    solve_parser.add_argument("--output")
    solve_parser.set_defaults(handler=_solve)
    benchmark_parser = subparsers.add_parser("benchmark", help="Run a benchmark manifest")
    benchmark_parser.add_argument("--manifest", required=True)
    benchmark_parser.add_argument("--algorithms", nargs="+", choices=("dfs", "gbfs"), default=("dfs", "gbfs"))
    benchmark_parser.add_argument("--repeats", type=int, default=10)
    benchmark_parser.add_argument("--timeout", type=float, default=60.0)
    benchmark_parser.add_argument("--csv", required=True)
    benchmark_parser.add_argument("--json")
    benchmark_parser.set_defaults(handler=_benchmark)
    gui_parser = subparsers.add_parser("gui", help="Open the Tkinter visualizer")
    gui_parser.set_defaults(handler=lambda _args: _gui())
    return parser


def _gui() -> int:
    from logic_search.app import main as gui_main
    gui_main()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
