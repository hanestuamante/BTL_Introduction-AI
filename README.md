# Logic Puzzle Search

Ứng dụng Python giải **Pipes** và **Futoshiki** bằng **Depth-First Search (DFS)** và **Greedy Best-First Search (GBFS)**. Project có CLI, GUI Tkinter chạy từng bước, generator tái lập bằng seed, 18 input benchmark, đo thời gian/bộ nhớ trong process riêng và xuất CSV/JSON/SVG.

## Cài đặt

Yêu cầu Python 3.11+ (Tkinter cần có trong bản Python nếu dùng GUI).

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Chạy nhanh

Mở giao diện:

```bash
python -m logic_search gui
```

Giải một input:

```bash
python -m logic_search solve \
  --puzzle futoshiki \
  --input data/futoshiki/futoshiki-4x4-easy-seed-201.json \
  --algorithm gbfs --timeout 60 \
  --output results/raw/example.json
```

Exit code: `0` solved, `1` unsolved, `2` input error, `3` timeout, `4` internal error.

Chạy benchmark đầy đủ và tổng hợp:

```bash
python scripts/run_benchmarks.py
python scripts/summarize_results.py
```

Benchmark warm-up một lượt, chạy 10 lượt thời gian và một lượt `tracemalloc` riêng cho từng input/algorithm. Mỗi lượt nằm trong process độc lập. Raw data không gộp mất timeout; bảng tổng hợp dùng median làm số chính.

## Điều khiển GUI

- Khi mở, app tự nạp đề Futoshiki 4×4 Easy để có thể chơi ngay.
- Futoshiki: bấm ô trắng rồi dùng phím số hoặc bàn phím số trên màn hình; Backspace/Xóa để xóa.
- Pipes: bấm trái để xoay thuận 90°, bấm phải để xoay ngược.
- **Kiểm tra** tô đỏ ô xung đột và xác nhận chiến thắng; **Gợi ý** điền/sửa một ô; **Hoàn tác** quay lại nước trước.
- **Run / Pause / Resume / Step / Cancel** điều khiển worker search mà không khóa event loop.
- **Back** xem lại state đã render; không thay đổi search đang chạy.
- Slider **Speed** điều chỉnh tốc độ tiêu thụ event.
- Màu cam là ô chưa quyết định, xanh dương là state đang xét, xanh lá là nghiệm, xám là given.

## Dữ liệu

`data/benchmark_manifest.json` chứa 18 input và checksum SHA-256:

| Puzzle | Easy | Medium | Hard | Seed/mức |
| --- | --- | --- | --- | ---: |
| Pipes | 3×3 | 4×4 | 5×5 | 3 |
| Futoshiki | 4×4 | 5×5 | 6×6 | 3 |

Sinh lại byte-identical dataset:

```bash
python scripts/generate_inputs.py
```

Generator Futoshiki xóa given nhưng chỉ giữ thay đổi nếu còn đúng một nghiệm. Pipes sinh cây khung trên lưới; validator đếm tối đa hai nghiệm trước khi nghiệm thu dataset. Seed, phiên bản generator và difficulty nằm trong metadata.

## Kiểm thử và quality gate

```bash
python -m compileall src
pytest -q
python scripts/validate_submission.py
```

Tests bao phủ bitmask/rotation, border và goal tree, domain và inequality, parser validation, deterministic DFS, priority/tie-break GBFS, cancellation và solve end-to-end cho cả hai puzzle.

## Kiến trúc

```text
src/logic_search/
├── core/          # protocol, node, result, event, cancellation
├── search/        # frontier và solver DFS/GBFS dùng chung
├── puzzles/       # Pipes, Futoshiki: model/parser/rules/heuristic/generator
├── ui/            # Tkinter canvas, metrics, worker controller
└── benchmark/     # process isolation, metadata, CSV/JSON export
```

DFS và GBFS dùng chung state, action, pruning và goal validator; chỉ khác frontier và việc GBFS tính `h`. State là tuple bất biến. DFS push child theo thứ tự đảo để khi pop vẫn giữ thứ tự action cố định. GBFS dùng `(h, depth, sequence_id)` để không so sánh object và đảm bảo tie-break tái lập.

Chi tiết quyết định nằm ở [docs/ADR-001.md](docs/ADR-001.md). Khung báo cáo và slide nằm trong `report/` và `slides/`.

## Giới hạn

- Chỉ hỗ trợ Pipes non-wrap.
- GBFS không đảm bảo đường đi tối ưu.
- Peak memory là Python allocations do `tracemalloc`, không phải toàn bộ RSS.
- File PDF/PPTX cuối cần nhóm điền thành viên, thông tin môn học và số liệu benchmark chính thức trước khi nộp.
