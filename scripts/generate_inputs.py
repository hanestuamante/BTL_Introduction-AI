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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


def write_stable(path: Path, data: dict) -> str:
    content = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sinh đề cho Futoshiki và Pipes (mặc định sinh bộ benchmark nếu không truyền tham số tùy chỉnh).")
    parser.add_argument("--output", type=Path, default=ROOT / "data", help="Thư mục xuất file JSON")
    parser.add_argument("--pipes-only", action="store_true", help="Chỉ sinh bộ benchmark cho Pipes")
    parser.add_argument("--puzzle", choices=["all", "futoshiki", "pipes"], default=None, help="Loại puzzle cần sinh")
    parser.add_argument("--size", type=int, default=None, help="Kích thước cạnh bảng (size x size)")
    parser.add_argument("--rows", type=int, default=None, help="Số hàng (cho Pipes)")
    parser.add_argument("--cols", type=int, default=None, help="Số cột (cho Pipes)")
    parser.add_argument("--blank-ratio", type=float, default=None, help="Tỷ lệ ô trống ban đầu (0.0 đến 1.0, cho Futoshiki)")
    parser.add_argument("--relation-ratio", type=float, default=None, help="Tỷ lệ dấu bất đẳng thức (cho Futoshiki)")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default=None, help="Độ khó")
    parser.add_argument("--seed", type=int, default=None, help="Hạt giống sinh ngẫu nhiên (seed)")
    parser.add_argument("--count", type=int, default=1, help="Số lượng đề cần sinh")
    parser.add_argument("--wrap", action=argparse.BooleanOptionalAction, default=None, help="Nối biên bàn cờ (cho Pipes)")
    parser.add_argument("--lock-ratio", type=float, default=0.0, help="Tỷ lệ ô bị khóa (0.0 đến 1.0, cho Pipes)")
    args = parser.parse_args()

    # Use custom generation mode when specific options are supplied
    is_custom = (
        args.puzzle is not None
        or args.size is not None
        or args.rows is not None
        or args.cols is not None
        or args.blank_ratio is not None
        or args.seed is not None
        or args.difficulty is not None
    )

    if is_custom:
        target_puzzle = args.puzzle or ("pipes" if (args.rows or args.cols) else "futoshiki")
        if target_puzzle in {"futoshiki", "all"}:
            size = args.size or 4
            difficulty = args.difficulty or "easy"
            base_seed = args.seed if args.seed is not None else 201
            for i in range(args.count):
                cur_seed = base_seed + i
                data = generate_futoshiki(
                    size,
                    cur_seed,
                    difficulty=difficulty,
                    blank_ratio=args.blank_ratio,
                    relation_ratio=args.relation_ratio,
                )
                path = args.output / "futoshiki" / f"{data['id']}.json"
                write_stable(path, data)
                print(f"[Futoshiki] Generated {data['id']} (size={size}, blank_ratio={data['metadata'].get('blank_ratio')}) -> {path}", flush=True)

        if target_puzzle in {"pipes", "all"}:
            rows = args.rows or args.size or 6
            cols = args.cols or args.size or 6
            difficulty = args.difficulty or "hard"
            wrap = True if args.wrap is True or args.wrap is None else False
            base_seed = args.seed if args.seed is not None else 601
            for i in range(args.count):
                cur_seed = base_seed + i
                data = generate_pipes(
                    rows,
                    cols,
                    cur_seed,
                    difficulty=difficulty,
                    wrap=wrap,
                    lock_ratio=args.lock_ratio,
                )
                path = args.output / "pipes" / f"{data['id']}.json"
                write_stable(path, data)
                print(f"[Pipes] Generated {data['id']} (rows={rows}, cols={cols}, wrap={wrap}) -> {path}", flush=True)
        return 0

    # Default mode: generate the full benchmark dataset and update benchmark_manifest.json
    manifest_path = args.output / "benchmark_manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"inputs": []}
    retained = [entry for entry in previous["inputs"] if entry["path"].startswith("futoshiki/")] if args.pipes_only else []
    generated = []
    for size in (6, 7, 8):
        for offset in range(3):
            seed = size * 100 + 1 + offset
            data = generate_pipes(size, size, seed, difficulty="hard", wrap=True, candidates=24)
            relative = Path("pipes") / f"{data['id']}.json"
            generated.append((relative, "hard", data))
            print(f"Generated {data['id']}: {data['metadata']['solver_effort']}", flush=True)
    if not args.pipes_only:
        for level, difficulty in enumerate(("easy", "medium", "hard")):
            for offset in range(3):
                data = generate_futoshiki(4 + level, 201 + level * 100 + offset, difficulty=difficulty)
                generated.append((Path("futoshiki") / f"{data['id']}.json", difficulty, data))
    manifest = {"schema_version": 1, "inputs": retained}
    for relative, difficulty, data in generated:
        checksum = write_stable(args.output / relative, data)
        manifest["inputs"].append({"path": relative.as_posix(), "difficulty": difficulty, "sha256": checksum})
    write_stable(manifest_path, manifest)
    active = {entry["path"] for entry in manifest["inputs"]}
    for entry in previous["inputs"]:
        relative = Path(entry["path"])
        if relative.parts[0] == "pipes" and not relative.is_absolute() and ".." not in relative.parts and entry["path"] not in active:
            (args.output / relative).unlink(missing_ok=True)
    print(f"Wrote {len(manifest['inputs'])} inputs in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
