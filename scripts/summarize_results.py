#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


NUMERIC = ("runtime_ms", "peak_python_memory_kib", "nodes_expanded")


def summarize(input_path: Path) -> list[dict[str, str]]:
    with input_path.open(encoding="utf-8", newline="") as handle:
        raw = list(csv.DictReader(handle))
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in raw:
        groups[(row["puzzle"], row["difficulty"], row["algorithm"])].append(row)
    output = []
    for (puzzle, difficulty, algorithm), rows in sorted(groups.items()):
        solved = [row for row in rows if row["status"] == "solved"]
        record = {
            "puzzle": puzzle,
            "difficulty": difficulty,
            "algorithm": algorithm,
            "runs": str(len(rows)),
            "success_rate": f"{len(solved) / len(rows):.4f}",
        }
        for field in NUMERIC:
            values = [float(row[field]) for row in solved if row.get(field) not in {None, "", "None"}]
            record[f"{field}_median"] = f"{statistics.median(values):.4f}" if values else ""
            record[f"{field}_mean"] = f"{statistics.fmean(values):.4f}" if values else ""
            record[f"{field}_stdev"] = f"{statistics.stdev(values):.4f}" if len(values) > 1 else "0.0000"
            record[f"{field}_min"] = f"{min(values):.4f}" if values else ""
            record[f"{field}_max"] = f"{max(values):.4f}" if values else ""
        output.append(record)
    return output


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)


def write_svg(path: Path, rows: list[dict[str, str]], metric: str, title: str) -> None:
    values = [float(row.get(metric) or 0) for row in rows]
    width, height, margin = 1000, 520, 70
    chart_h = height - 2 * margin
    max_value = max(values, default=1) or 1
    bar_w = (width - 2 * margin) / max(1, len(rows))
    pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<text x="{width/2}" y="30" text-anchor="middle" font-family="sans-serif" font-size="20">{title}</text>']
    pieces.append(f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="#334155"/>')
    for i, (row, value) in enumerate(zip(rows, values)):
        x = margin + i * bar_w + bar_w * .15
        h = chart_h * value / max_value
        y = height - margin - h
        color = "#2563eb" if row["algorithm"] == "dfs" else "#f59e0b"
        label = f'{row["puzzle"][:1].upper()}-{row["difficulty"][:1].upper()}-{row["algorithm"].upper()}'
        pieces.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*.7:.1f}" height="{h:.1f}" fill="{color}"/>')
        pieces.append(f'<text x="{x+bar_w*.35:.1f}" y="{height-margin+18}" text-anchor="middle" font-family="sans-serif" font-size="10">{label}</text>')
        pieces.append(f'<text x="{x+bar_w*.35:.1f}" y="{max(48,y-5):.1f}" text-anchor="middle" font-family="sans-serif" font-size="10">{value:.2f}</text>')
    pieces.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(pieces), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, nargs="?", default=Path("results/raw/benchmark.csv"))
    parser.add_argument("--table", type=Path, default=Path("results/tables/summary.csv"))
    parser.add_argument("--charts", type=Path, default=Path("results/charts"))
    args = parser.parse_args()
    rows = summarize(args.input)
    write_csv(args.table, rows)
    for metric, title, filename in (
        ("runtime_ms_median", "Median runtime (ms)", "runtime.svg"),
        ("peak_python_memory_kib_median", "Peak Python memory (KiB)", "memory.svg"),
        ("nodes_expanded_median", "Median expanded nodes", "nodes.svg"),
    ):
        write_svg(args.charts / filename, rows, metric, title)
    print(f"Wrote {args.table} and 3 SVG charts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

