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
    parser.add_argument("--pipes-only", action="store_true")
    args = parser.parse_args()
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
