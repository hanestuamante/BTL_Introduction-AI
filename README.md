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

Benchmark warm-up một lượt, chạy 10 lượt thời gian và một lượt `tracemalloc` riêng cho từng input/algorithm. Bộ nhớ được đo sau khi nạp/validate input, chỉ tính cấp phát Python trong `solve()`. Raw data lưu `memory_status`, `memory_message` và `memory_scope`; lượt memory không giải thành công để trống giá trị bộ nhớ. Mỗi lượt nằm trong process độc lập. Raw data không gộp mất timeout; bảng tổng hợp dùng median làm số chính.

## Điều khiển GUI

- Khi mở, app tự nạp đề Futoshiki 4×4 Easy để có thể chơi ngay.
- Futoshiki: bấm ô trắng rồi dùng phím số hoặc bàn phím số trên màn hình; Backspace/Xóa để xóa.
- Pipes: bấm trái để xoay thuận 90°, bấm phải để xoay ngược.
- **Kiểm tra** tô đỏ ô xung đột và xác nhận chiến thắng; **Gợi ý** điền/sửa một ô; **Hoàn tác** quay lại nước trước.
- **Run / Pause / Resume / Step / Cancel** điều khiển worker search mà không khóa event loop.
- **Back** xem lại state đã render; không thay đổi search đang chạy.
- GUI ghi “Chuyển nhánh xét” khi node được chọn không phải child của node vừa mở rộng. Đây không phải bằng chứng nhánh cũ thất bại.
- `NODE_PRUNED` là không sinh child mới: GUI tách “Ngõ cụt” (không có action hợp lệ) và “Child đã được khám phá” (child trùng). Event tạo node/goal không đặt lại bộ đếm; event kết thúc giữ depth của nghiệm.
- Slider **Speed** điều chỉnh tốc độ tiêu thụ event.
- Màu cam là ô chưa quyết định, xanh dương là state đang xét, xanh lá là nghiệm, xám là given.

## Dữ liệu

`data/benchmark_manifest.json` chứa 18 input và checksum SHA-256:

| Puzzle | Kích thước | Độ khó | Số đề |
| --- | --- | --- | ---: |
| Pipes | 6×6, 7×7, 8×8 | Tất cả Hard, nối biên | 3/kích thước |
| Futoshiki | 4×4, 5×5, 6×6 | Easy, Medium, Hard | 3/mức |

Sinh lại byte-identical dataset:

```bash
python scripts/generate_inputs.py
```

Generator Futoshiki xóa given nhưng chỉ giữ thay đổi nếu còn đúng một nghiệm. Pipes v3 sinh cây khung bằng Kruskal, kiểm tra nghiệm duy nhất và chọn Hard trong 24 ứng viên theo effort thực tế của cả DFS/GBFS sau khi xáo ô. Điểm là `min(nodes_expanded) + sum(nodes_expanded)/10`; mỗi lượt chấm bị giới hạn 2.000 node, nên ứng viên chạm giới hạn chỉ có số đo cận dưới. Metadata lưu effort, ngân sách, số khóa thực tế và seed. Hard là mức tương đối trong tập ứng viên, không phải bảo đảm về thời gian chạy.

Chỉ thay bộ Pipes và giữ nguyên Futoshiki:

```bash
python scripts/generate_inputs.py --pipes-only
```

Bảng tổng hợp tách theo puzzle, kích thước, độ khó và thuật toán. Mỗi cặp đề/thuật toán chỉ có một lượt memory; giá trị này được lặp trên các dòng timing và không đại diện cho 10 phép đo memory độc lập.

### Sinh riêng dữ liệu Pipes

Script riêng mặc định sinh 3 đề Hard 6×6, không sinh Futoshiki; ghi vào `data/generated-pipes/` để giữ bộ dữ liệu gốc:

```bash
python scripts/generate_pipes_inputs.py
python scripts/generate_pipes_inputs.py --help
```

Ví dụ sinh 3 đề Pipes Hard 6×6 có nối biên và tối thiểu 15% ô khóa:

```bash
python scripts/generate_pipes_inputs.py --difficulty hard --rows 6 --cols 6 \
  --wrap --lock-ratio 0.15 --count 3 --seed 42 --output data/generated-pipes-wrap
```

Các tùy chọn: `--output`, `--difficulty` (một hoặc nhiều mức), `--count`, `--seed`, `--rows`, `--cols`, `--wrap`, `--lock-ratio`, `--candidates`, `--node-limit`, `--overwrite`. Nối biên yêu cầu cả hai chiều >= 3. Script mặc định từ chối ghi đè; chỉ dùng `--overwrite` khi muốn thay thế file trùng tên và manifest. Manifest chỉ liệt kê đợt vừa sinh; các file khác được giữ lại.

### Kết quả benchmark bộ dữ liệu chính

Chín đề Pipes Hard nối biên 6×6, 7×7 và 8×8 trong `data/pipes/` thay thế bộ Pipes cũ. Benchmark dùng manifest chính và ghi đè `results/raw/benchmark.csv`, `results/raw/benchmark.json`; bảng và biểu đồ nằm ở `results/tables/summary.csv` và `results/charts/`. Các results riêng `pipes-wrap-6x6` đã được xóa; bộ sinh thử `data/generated-pipes-wrap-1/` đã được xóa.

Mỗi kích thước Pipes có 3 đề × 10 lượt = 30 lượt timing cho mỗi thuật toán. Số liệu dưới đây lấy từ lần chạy mới trong raw results; thời gian là median, memory là median của các lượt memory thành công riêng biệt.

| Kích thước | Thuật toán | Solved / lượt | Median thời gian (ms) | Median memory (KiB) | Median node mở rộng |
| --- | --- | ---: | ---: | ---: | ---: |
| 6x6 | DFS | 30/30 | 861.29 | 252.32 | 420 |
| 6x6 | GBFS | 30/30 | 932.91 | 269.10 | 434 |
| 7x7 | DFS | 30/30 | 2667.55 | 701.83 | 1098 |
| 7x7 | GBFS | 30/30 | 3843.91 | 1028.31 | 1421 |
| 8x8 | DFS | 30/30 | 6956.70 | 1505.78 | 1904 |
| 8x8 | GBFS | 30/30 | 11247.38 | 2131.80 | 2689 |

Kết quả phụ thuộc máy và phiên bản Python ghi trong raw data. So sánh thuật toán theo từng kích thước; GBFS không mặc nhiên nhanh hơn DFS. Các node mở rộng phản ánh lượng tìm kiếm, không phải số lần chuyển nhánh/quay lui.

### Ý nghĩa event và số đo tìm kiếm

`MetricsPanel.update_event()` chỉ cập nhật giao diện, không tham gia tính số đo benchmark. Khi hai node mở rộng liên tiếp không có quan hệ cha–con, GUI hiển thị “Chuyển nhánh xét”, nhưng không tích lũy số lần chuyển nhánh. Benchmark chạy `solve()` không có callback và tắt detailed events; các số đo vẫn được solver tính trực tiếp.

`nodes_pruned` đếm node đã mở rộng nhưng không sinh được child mới (không có action hợp lệ hoặc mọi child đã được khám phá). **Không dùng chỉ số này làm số lần quay lui hoặc số nhánh sai.** GBFS có thể rời một node nằm trên đường nghiệm để xét nhánh khác vì thứ tự heuristic, rồi tiếp tục đường nghiệm sau đó; chuyển nhánh như vậy không làm tăng `nodes_pruned`. Ví dụ test mở rộng `A → B → C → E → D → G`, còn đường nghiệm là `A → B → D → G`: rời `B` để xét `C` không chứng minh `B` thất bại. Hiện CSV/JSON chưa có chỉ số đếm chuyển nhánh hay số bước quay về tổ tiên.

## Kiểm thử và quality gate

```bash
python -m compileall src
pytest -q
python scripts/validate_submission.py
```

Hai file unit test mới:

- `tests/unit/test_metrics_panel.py`: dùng biến giả để kiểm tra event tạo node/goal không xóa bộ đếm, event kết thúc giữ độ sâu nghiệm, và chuyển nhánh hiển thị đúng mà không gán nhánh cũ là thất bại. Không cần mở cửa sổ GUI, nhưng import vẫn cần Tkinter.
- `tests/unit/test_summary.py`: kiểm tra bảng tổng hợp tách kích thước 6×6/7×7 và chỉ tính một mẫu memory cho mỗi đề, dù giá trị lặp trên nhiều dòng timing.

`tests/unit/test_search.py` được bổ sung test chuyển nhánh GBFS từ tổ tiên của nghiệm và lý do prune child trùng; `tests/unit/test_pipes.py` bổ sung kiểm tra generator Hard và tính tái lập.

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

- Pipes hỗ trợ non-wrap, nối biên và ô khóa; nối biên yêu cầu cả hai chiều >= 3.
- GBFS không đảm bảo đường đi tối ưu.
- Peak memory là Python allocations do `tracemalloc`, không phải toàn bộ RSS.
- File PDF/PPTX cuối cần nhóm điền thành viên, thông tin môn học và số liệu benchmark chính thức trước khi nộp.
