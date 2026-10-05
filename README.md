# Logic Puzzle Search

Giải và trực quan hóa Pipes, Futoshiki bằng DFS và Greedy Best-First Search (GBFS).

## 1. Cài đặt

Yêu cầu Python 3.11 trở lên; Python cần có Tkinter để mở GUI. Chạy các lệnh dưới đây tại thư mục gốc dự án.

```bash
python -m pip install -e '.[dev]'
```

`pyproject.toml` khai báo gói, phiên bản Python, dependencies và lệnh `logic-search`. `requirements-dev.txt` cài cùng bộ dependencies phát triển qua `python -m pip install -r requirements-dev.txt`.

## 2. Kiến trúc và cách sử dụng các file

Luồng CLI: `__main__.py` → `cli.py` → `io.py` → parser của puzzle → `search/solver.py` → kết quả JSON hoặc benchmark CSV/JSON. Luồng GUI: `app.py` → `ui/main_window.py` → `ui/controller.py` → solver → event → canvas và bảng số đo.

Solver làm việc qua giao diện `SearchProblem`, dùng chung quy tắc sinh trạng thái và kiểm tra đích cho DFS/GBFS. DFS dùng stack; GBFS dùng hàng đợi ưu tiên theo `(heuristic, depth, sequence_id)`. GUI chạy tìm kiếm trên worker thread; benchmark chạy mỗi lượt trong process riêng.

Các đường dẫn dưới đây thuộc `src/logic_search/`. Các module được gọi qua CLI/GUI hoặc import khi phát triển.

| File | Chức năng / cách sử dụng |
| --- | --- |
| `__main__.py` | Điểm vào của `python -m logic_search`. |
| `cli.py` | Phân tích lệnh `solve`, `benchmark`, `gui`; điểm vào của `logic-search`. |
| `app.py` | Khởi tạo Tkinter và cửa sổ; chạy qua lệnh `gui`. |
| `io.py` | `load_problem(path, expected_puzzle=None)` đọc JSON và chọn parser. |
| `core/problem.py` | Protocol `SearchProblem`: state ban đầu, action, state kế tiếp, goal, heuristic và khóa state. |
| `core/node.py` | Node tìm kiếm, liên kết cha và action để dựng đường nghiệm. |
| `core/result.py` | `SearchResult`, `SearchMetrics`; chuyển trạng thái, đường nghiệm và số đo sang dictionary. |
| `core/events.py` | Loại event, dữ liệu event và bộ phát event cho GUI. |
| `core/cancellation.py` | `CancellationToken` dùng để hủy tìm kiếm. |
| `search/solver.py` | `solve(problem, algorithm, ...)` thực hiện tìm kiếm và thu số đo. |
| `search/frontier.py` | Stack cho DFS, priority queue cho GBFS. |
| `search/dfs.py` | Hàm `depth_first_search(problem, **kwargs)` gọi solver với DFS. |
| `search/gbfs.py` | Hàm `greedy_best_first_search(problem, **kwargs)` gọi solver với GBFS. |
| `puzzles/futoshiki/model.py` | State, miền giá trị, ràng buộc hàng/cột và bất đẳng thức, action, goal, heuristic Futoshiki. |
| `puzzles/pipes/model.py` | Bitmask hướng ống, phép xoay, nối biên, ô khóa, action, goal, heuristic Pipes. |
| `puzzles/futoshiki/parser.py`, `puzzles/pipes/parser.py` | Parse dictionary hoặc đọc file JSON thành problem; kiểm tra cấu trúc input. |
| `puzzles/futoshiki/rules.py`, `puzzles/pipes/rules.py` | `validate_solution(problem, state)` kiểm tra nghiệm. |
| `puzzles/futoshiki/heuristic.py`, `puzzles/pipes/heuristic.py` | Hàm heuristic gọi tính điểm của model tương ứng. |
| `puzzles/futoshiki/generator.py` | `generate_futoshiki(...)` sinh đề; `count_solutions(...)` đếm nghiệm. |
| `puzzles/pipes/generator.py` | `generate_pipes(...)` sinh đề; `count_solutions(...)` đếm nghiệm. |
| `ui/main_window.py` | Nạp đề, thao tác chơi, chọn thuật toán và điều khiển phát lại. |
| `ui/controller.py` | Worker tìm kiếm, hàng đợi event, tạm dừng, tiếp tục, từng bước và hủy. |
| `ui/game_logic.py` | Thao tác chơi, kiểm tra xung đột và gợi ý. |
| `ui/futoshiki_canvas.py`, `ui/pipes_canvas.py` | Vẽ bảng puzzle và state lên Tkinter canvas. |
| `ui/metrics_panel.py` | Hiển thị event và các số đo tìm kiếm. |
| `benchmark/runner.py` | Chạy warm-up, lượt đo thời gian và lượt đo bộ nhớ trong process riêng. |
| `benchmark/metrics.py` | Thu phiên bản Python, hệ điều hành, CPU và commit cho kết quả. |
| `benchmark/export.py` | Ghi kết quả CSV/JSON. |
| Các file `__init__.py` | Khai báo các package Python. |

Các file ngoài mã nguồn:

| File / nhóm file | Cách sử dụng |
| --- | --- |
| `scripts/generate_inputs.py` | Sinh bộ dữ liệu benchmark chính; xem mục 5. |
| `scripts/generate_pipes_inputs.py` | Sinh bộ Pipes tùy chỉnh; xem mục 5. |
| `scripts/run_benchmarks.py` | Chạy cấu hình benchmark mặc định; xem mục 4. |
| `scripts/summarize_results.py` | Tổng hợp CSV và vẽ biểu đồ; xem mục 4. |
| `scripts/validate_submission.py` | Kiểm tra manifest, checksum, ID và nghiệm duy nhất; xem mục 7. |
| `data/benchmark_manifest.json` | Danh sách 18 đề chính, đường dẫn tương đối và checksum SHA-256; truyền vào `--manifest`. |
| `data/futoshiki/*.json` | 9 đề Futoshiki: 4×4 Easy, 5×5 Medium, 6×6 Hard; mỗi nhóm 3 đề. Dùng với `solve --puzzle futoshiki` hoặc GUI. |
| `data/pipes/*.json` | 9 đề Pipes Hard nối biên: 6×6, 7×7, 8×8; mỗi kích thước 3 đề. Dùng với `solve --puzzle pipes` hoặc GUI. |
| `data/generated-pipes-wrap/benchmark_manifest.json` | Manifest bộ Pipes Hard 6×6 nối biên, tỷ lệ khóa tối thiểu 0,15; dùng với `benchmark --manifest`. |
| `data/generated-pipes-wrap/pipes/*.json` | 3 đề với seed 242–244; dùng với CLI/GUI. |
| `results/raw/benchmark.csv`, `results/raw/benchmark.json` | Số đo từng lượt chạy và thông tin môi trường. |
| `results/tables/summary.csv` | Số lượt, tỷ lệ thành công, số mẫu memory, median/mean/stdev/min/max theo puzzle, kích thước, độ khó, thuật toán. |
| `results/charts/runtime.svg`, `results/charts/memory.svg`, `results/charts/nodes.svg` | Mở bằng trình duyệt để xem biểu đồ thời gian, bộ nhớ và node mở rộng. |
| `docs/ADR-001.md` | Tài liệu quyết định kiến trúc. |
| `slides/README.md` | Hướng dẫn nội dung slide. |
| `LICENSE` | Giấy phép sử dụng mã nguồn. |

## 3. Giải đề và mở GUI

Có thể thay `python -m logic_search` bằng `logic-search` sau khi cài đặt. Các lệnh CLI và script dùng argparse hỗ trợ `-h` / `--help`, ngoại trừ hai script chạy cấu hình cố định được ghi rõ bên dưới.

### `solve`

```bash
python -m logic_search solve \
  --puzzle futoshiki \
  --input data/futoshiki/futoshiki-4x4-easy-seed-201.json \
  --algorithm gbfs --timeout 60 \
  --output results/raw/example.json

python -m logic_search solve \
  --puzzle pipes --input data/pipes/pipes-6x6-hard-wrap-seed-601.json \
  --algorithm dfs
```

| Flag | Giá trị / lựa chọn | Mặc định | Ý nghĩa |
| --- | --- | --- | --- |
| `--puzzle` | `pipes`, `futoshiki` | Bắt buộc | Loại puzzle, phải khớp file input. |
| `--input` | Đường dẫn JSON | Bắt buộc | Đề cần giải. |
| `--algorithm` | `dfs`, `gbfs` | `dfs` | Thuật toán tìm kiếm. |
| `--timeout` | Số thực, đơn vị giây | `60.0` | Giới hạn thời gian tìm kiếm. |
| `--output` | Đường dẫn JSON | Không ghi file | Lưu kết quả; kết quả luôn được in ra terminal. |

JSON trả về `status`, `path`, `actions`, `metrics`, `message` cùng thông tin puzzle và thuật toán. Mã thoát: `0` giải được, `1` không có nghiệm, `2` lỗi input, `3` hết thời gian, `4` lỗi nội bộ.

### `gui`

```bash
python -m logic_search gui
```

Lệnh chỉ có `-h` / `--help`, không có flag cấu hình. Khi mở, GUI nạp đề Futoshiki 4×4 Easy.

| Thao tác | Cách dùng |
| --- | --- |
| Browse… / Load | Chọn file JSON rồi nạp đề. |
| Chơi Futoshiki | Chọn ô trắng, nhập số `1–N`; Backspace hoặc Xóa để xóa. |
| Chơi Pipes | Bấm trái xoay thuận 90°, bấm phải xoay ngược; ô khóa giữ nguyên hướng. |
| Kiểm tra / Gợi ý | Kiểm tra bàn hiện tại hoặc điền/sửa một ô. |
| Hoàn tác / Chơi lại | Quay về state trước hoặc đặt lại đề. |
| Thuật toán | Chọn `dfs` hoặc `gbfs`; mặc định `dfs`. |
| Chạy / Dừng / Tiếp tục | Bắt đầu, tạm dừng hoặc tiếp tục tìm kiếm. |
| Từng bước / Hủy | Phát từng event hoặc hủy tìm kiếm. |
| Tốc độ | Điều chỉnh tốc độ hiển thị từ `0.25` đến `4.0`. |

## 4. Benchmark và tổng hợp kết quả

### `benchmark`

```bash
python -m logic_search benchmark \
  --manifest data/benchmark_manifest.json \
  --algorithms dfs gbfs --repeats 10 --timeout 60 \
  --csv results/raw/benchmark.csv --json results/raw/benchmark.json
```

| Flag | Giá trị / lựa chọn | Mặc định | Ý nghĩa |
| --- | --- | --- | --- |
| `--manifest` | Đường dẫn JSON | Bắt buộc | Danh sách input; đường dẫn input tương đối được tính từ thư mục chứa manifest. |
| `--algorithms` | Một hoặc nhiều giá trị `dfs`, `gbfs` | `dfs gbfs` | Thuật toán cần đo. |
| `--repeats` | Số nguyên | `10` | Số lượt timing cho mỗi cặp input/thuật toán. |
| `--timeout` | Số thực, đơn vị giây | `60.0` | Giới hạn mỗi lượt tìm kiếm. |
| `--csv` | Đường dẫn CSV | Bắt buộc | Lưu số đo từng lượt. |
| `--json` | Đường dẫn JSON | Không ghi JSON | Lưu thêm cùng số đo dưới dạng JSON. |

### `scripts/run_benchmarks.py`

```bash
python scripts/run_benchmarks.py
```

Script không có flags; chạy đúng cấu hình `benchmark` ở ví dụ trên và ghi lại hai file kết quả tương ứng.

### `scripts/summarize_results.py`

```bash
python scripts/summarize_results.py
python scripts/summarize_results.py results/raw/benchmark.csv \
  --table results/tables/summary.csv --charts results/charts
```

| Đối số / flag | Giá trị | Mặc định | Ý nghĩa |
| --- | --- | --- | --- |
| `input` | Đường dẫn CSV, đối số vị trí tùy chọn | `results/raw/benchmark.csv` | Raw results cần tổng hợp. |
| `--table` | Đường dẫn CSV | `results/tables/summary.csv` | Bảng thống kê đầu ra. |
| `--charts` | Thư mục | `results/charts` | Lưu `runtime.svg`, `memory.svg`, `nodes.svg`. |

## 5. Sinh dữ liệu

### `scripts/generate_inputs.py`

```bash
python scripts/generate_inputs.py
```

| Flag | Giá trị | Mặc định | Ý nghĩa |
| --- | --- | --- | --- |
| `--output` | Thư mục | `data` tại gốc dự án | Lưu các đề và `benchmark_manifest.json`. |
| `--pipes-only` | Bật/tắt | Tắt | Chọn chế độ sinh bộ Pipes. |

Cấu hình bộ chính: Pipes Hard nối biên 6×6, 7×7, 8×8 với seed 601–603, 701–703, 801–803; Futoshiki 4×4 Easy, 5×5 Medium, 6×6 Hard với seed 201–203, 301–303, 401–403. Script ghi lại các đề và manifest tại thư mục đầu ra.

### `scripts/generate_pipes_inputs.py`

```bash
python scripts/generate_pipes_inputs.py \
  --difficulty hard --rows 6 --cols 6 --wrap \
  --lock-ratio 0.15 --count 3 --seed 42 \
  --output data/generated-pipes-wrap --overwrite
```

| Flag | Giá trị / lựa chọn | Mặc định | Ý nghĩa |
| --- | --- | --- | --- |
| `--output` | Thư mục | `data/generated-pipes` tại gốc dự án | Lưu thư mục `pipes/` và manifest. |
| `--difficulty` | Một hoặc nhiều giá trị `easy`, `medium`, `hard` | `hard` | Mức độ khó cần sinh. |
| `--count` | Số nguyên ≥ 1 | `3` | Số đề cho mỗi mức. |
| `--seed` | Số nguyên | `101` khi bỏ qua | Seed cơ sở; cộng `0/100/200` cho Easy/Medium/Hard và cộng chỉ số đề từ 0. |
| `--rows` | Số nguyên ≥ 2 | `6` | Số hàng. |
| `--cols` | Số nguyên ≥ 2 | `6` | Số cột. |
| `--wrap` | Bật/tắt | Tắt | Cho phép nối qua biên; cả hai chiều phải ≥ 3. |
| `--lock-ratio` | Số thực trong `[0, 1]` | `0.0` | Tỷ lệ ô khóa tối thiểu; generator có thể thêm khóa để bảo đảm nghiệm duy nhất. |
| `--candidates` | Số nguyên ≥ 1 | `24` | Số ứng viên được xếp hạng cho mỗi đề. |
| `--node-limit` | Số nguyên ≥ 1 | `20000` | Ngân sách node kiểm tra nghiệm duy nhất mỗi lần thử. |
| `--overwrite` | Bật/tắt | Tắt | Cho phép thay thế đề trùng tên và manifest. |

Manifest đầu ra liệt kê đợt vừa sinh. Khi sinh nhiều mức, dùng `--count` không quá 100 để tránh trùng dải seed.

## 6. Số liệu kết quả

Số liệu lấy từ `results/tables/summary.csv`: 18 đề × 2 thuật toán × 10 lượt = **360 lượt timing**, tất cả giải thành công. Mỗi cặp đề/thuật toán có 1 lượt warm-up, 10 lượt timing và 1 lượt memory riêng; mỗi nhóm dưới đây có 30 lượt timing và 3 mẫu memory.

Thời gian và node là median trên các lượt giải thành công. Memory là median của peak cấp phát Python trong `solve()`, đo bằng `tracemalloc` sau khi nạp input. Thông tin máy và phiên bản Python của từng lượt nằm trong raw results.

| Puzzle | Kích thước | Độ khó | Thuật toán | Solved / lượt | Median thời gian (ms) | Median memory (KiB) | Median node mở rộng |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| Futoshiki | 4x4 | Easy | DFS | 30/30 | 0.35 | 8.33 | 8 |
| Futoshiki | 4x4 | Easy | GBFS | 30/30 | 0.53 | 8.60 | 8 |
| Futoshiki | 5x5 | Medium | DFS | 30/30 | 1.04 | 15.11 | 16 |
| Futoshiki | 5x5 | Medium | GBFS | 30/30 | 3.00 | 15.85 | 16 |
| Futoshiki | 6x6 | Hard | DFS | 30/30 | 4.83 | 37.12 | 53 |
| Futoshiki | 6x6 | Hard | GBFS | 30/30 | 17.31 | 61.31 | 89 |
| Pipes | 6x6 | Hard | DFS | 30/30 | 861.29 | 252.32 | 420 |
| Pipes | 6x6 | Hard | GBFS | 30/30 | 932.91 | 269.10 | 434 |
| Pipes | 7x7 | Hard | DFS | 30/30 | 2667.55 | 701.83 | 1098 |
| Pipes | 7x7 | Hard | GBFS | 30/30 | 3843.91 | 1028.31 | 1421 |
| Pipes | 8x8 | Hard | DFS | 30/30 | 6956.70 | 1505.78 | 1904 |
| Pipes | 8x8 | Hard | GBFS | 30/30 | 11247.38 | 2131.80 | 2689 |

## 7. Kiểm tra dữ liệu và chạy tests

### `scripts/validate_submission.py`

```bash
python scripts/validate_submission.py
```

Script không có flags; đọc `data/benchmark_manifest.json`, kiểm tra ít nhất 18 đề, checksum, ID không trùng và đúng một nghiệm. Mã thoát `0` khi hợp lệ, `1` khi có lỗi.

### Các file kiểm thử

```bash
python -m pytest -q
python -m pytest tests/unit/test_pipes.py -q
python -m pytest tests/integration -q
```

`-q` giảm thông tin in ra; đối số đường dẫn chọn file hoặc thư mục tests cần chạy.

| File | Nội dung kiểm tra |
| --- | --- |
| `tests/unit/test_pipes.py` | Phép xoay, ràng buộc, parser và generator Pipes. |
| `tests/unit/test_futoshiki.py` | Miền giá trị, bất đẳng thức, parser và generator Futoshiki. |
| `tests/unit/test_search.py` | DFS, GBFS, frontier, event và hủy tìm kiếm. |
| `tests/unit/test_game_logic.py` | Thao tác chơi, xung đột và gợi ý. |
| `tests/integration/test_end_to_end.py` | Giải đề và kiểm tra nghiệm đầu cuối. |
| `tests/integration/test_benchmark.py` | Chạy benchmark và kiểm tra dữ liệu xuất. |
