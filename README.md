# Logic Puzzle Search

Giải và trực quan hóa Pipes, Futoshiki bằng DFS và Greedy Best-First Search (GBFS).

## 1. Cài đặt

Yêu cầu Python 3.11 trở lên. Chạy các lệnh dưới đây tại thư mục gốc dự án. Dùng một môi trường riêng để tránh chọn nhầm Python hoặc cài dependencies vào interpreter khác.

Linux/macOS (thay `python3.11` bằng interpreter ≥3.11 bạn đã cài):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
```

Hoặc dùng Conda với cấu hình được lưu trong repository, bao gồm Python 3.11 và Tk:

```bash
conda env create -f environment-dev.yml
conda activate logic-puzzle-search
```

Nếu đã có môi trường Python ≥3.11 phù hợp, chỉ cần:

```bash
python -m pip install -e '.[dev]'
```

`pyproject.toml` khai báo gói, phiên bản Python, dependencies và lệnh `logic-search`. `requirements-dev.txt` cài cùng bộ dependencies phát triển qua `python -m pip install -r requirements-dev.txt`.

### Kiểm tra interpreter và Tkinter

```bash
python -c "import sys; print(sys.executable, sys.version); assert sys.version_info >= (3, 11)"
python -m pytest --version
python -c "import tkinter; print('Tk', tkinter.TkVersion)"
```

Tkinter cần cho GUI **và toàn bộ suite tests**, vì một số test nhập các lớp canvas/cửa sổ. Các test này không mở cửa sổ và không cần display. Import các module logic chơi, controller và dùng CLI không cần Tk. Việc mở GUI cần thêm display hoạt động; `python -m tkinter` dùng để thử cửa sổ Tk trên máy desktop.

Tkinter thường đi cùng Python trên Windows/macOS; trên Linux cần cài gói Tk tương ứng với đúng interpreter qua trình quản lý gói hệ thống hoặc dùng môi trường Conda ở trên. Nếu gặp `No module named pytest`, kiểm tra đã kích hoạt đúng môi trường và cài `.[dev]`. Nếu gặp lỗi thiếu `_tkinter` hoặc `libtk8.6.so`, sửa bộ cài Python/Tk và đường dẫn thư viện của môi trường; virtualenv không tự bổ sung thư viện Tk của hệ điều hành.

Các file `environment.yml` và thư mục `env/` cục bộ không phải cấu hình phát hành. Dùng `environment-dev.yml`; không dùng môi trường Python 3.10 cho project này.

### Kiểm tra nhanh sau khi cài

```bash
python -m logic_search --help
python -m logic_search solve --puzzle futoshiki \
  --input data/futoshiki/futoshiki-4x4-easy-seed-201.json --algorithm gbfs
python -m pytest -q
python scripts/validate_submission.py
```

Lệnh solve cần trả `status: solved`; validator cần báo `Validated 21 unique, checksummed inputs`. Số test phụ thuộc commit đang chạy. Benchmark đầy đủ gồm nhiều process và có thể mất nhiều phút; generator và các lệnh benchmark ghi lại file đầu ra nếu trùng đường dẫn, nên chọn thư mục riêng khi chỉ chạy thử.

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
| `data/benchmark_manifest.json` | Danh sách 21 đề chính, đường dẫn tương đối và checksum SHA-256; truyền vào `--manifest`. |
| `data/futoshiki/*.json` | 9 đề Futoshiki: 4×4 Easy, 5×5 Medium, 6×6 Hard; mỗi nhóm 3 đề. Dùng với `solve --puzzle futoshiki` hoặc GUI. |
| `data/pipes/*.json` | 12 đề Pipes Hard nối biên: 5×5, 6×6, 7×7, 8×8; mỗi kích thước 3 đề. Dùng với `solve --puzzle pipes` hoặc GUI. |
| `data/generated-pipes-wrap/benchmark_manifest.json` | Manifest bộ Pipes Hard 6×6 nối biên, tỷ lệ khóa tối thiểu 0,15; dùng với `benchmark --manifest`. |
| `data/generated-pipes-wrap/pipes/*.json` | 3 đề với seed 242–244; dùng với CLI/GUI. |
| `results/raw/benchmark.csv`, `results/raw/benchmark.json` | Số đo từng lượt chạy và thông tin môi trường. |
| `results/tables/summary.csv` | Số lượt, tỷ lệ thành công, số mẫu memory, median/mean/stdev/min/max theo puzzle, kích thước, độ khó, thuật toán. |
| `results/charts/runtime.svg`, `results/charts/memory.svg`, `results/charts/nodes.svg` | Mở bằng trình duyệt để xem biểu đồ thời gian, bộ nhớ và node mở rộng. |
| `docs/ADR-001.md` | Tài liệu quyết định kiến trúc. |
| `docs/ADR-002.md` | Sự kiện tìm kiếm, phát lại và cách tính thời gian GUI. |
| `docs/PLAYER_FLAGS.md` | Cờ ghi chú và phím tắt khi chơi Pipes. |
| `docs/PIPES_SEARCH.md` | Chú giải màu, thử/loại hướng và điều khiển phát lại tìm kiếm Pipes. |
| `environment-dev.yml` | Môi trường Conda Python 3.11, Tk và dependencies phát triển. |
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
  --puzzle pipes --input data/pipes/pipes-5x5-hard-wrap-seed-501.json \
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

Riêng trò Pipes, cờ đánh dấu do người chơi tự đặt và các phím tắt mới được mô tả trong [hướng dẫn cờ đánh dấu và phím tắt](docs/PLAYER_FLAGS.md). Cờ không xác nhận ô đúng và không ràng buộc thuật toán. Nguồn nước mặc định ở hàng 1, cột 1 (góc trên bên trái); file JSON có thể chỉ định nguồn riêng qua `source`.

Khi bấm **Run** ở Pipes, nền/viền ô thể hiện trạng thái chưa gán, đang thử, ứng viên, bị loại và nghiệm. Xem [chú giải màu và cách phát từng bước tìm kiếm](docs/PIPES_SEARCH.md).

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

Cấu hình bộ chính: Pipes Hard nối biên 5×5, 6×6, 7×7, 8×8 với seed 501–503, 601–603, 701–703, 801–803; Futoshiki 4×4 Easy, 5×5 Medium, 6×6 Hard với seed 201–203, 301–303, 401–403. Script ghi lại các đề và manifest tại thư mục đầu ra.

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

## 6. Số liệu kết quả — bộ 21 đề

Đợt benchmark lưu sẵn có **21 đề × 2 thuật toán × 10 lượt = 420 lượt timing**, với **420/420 lượt giải thành công**. Bộ dữ liệu gồm 9 đề Futoshiki và 12 đề Pipes Hard nối biên 5×5–8×8. Mã được đo tại commit `054bb6fcd89823e54273ced470de5ef2e05c2594`; package Python có SHA-256 `1de4e7d1eb5db91538f95b6402361eefab6c4ac81661faba0ee841d8c65ec8e1`. Các lượt đo ghi `git_worktree_dirty=false`.

Commit `ca97908` bổ sung trực quan hóa tìm kiếm Pipes và đã thay đổi package Python. **Chưa đo lại benchmark sau cập nhật này**; bảng dưới đây tiếp tục mô tả phiên bản `054bb6f`, không phải phép đo của mã nguồn hiện tại. Các số liệu và checksum lịch sử được giữ nguyên.

Mỗi cặp đề/thuật toán có 1 warm-up, 10 timing và 1 memory riêng trong process tách biệt, timeout 60 giây mỗi lượt. Tổng cộng 42 warm-up, 420 timing và 42 memory; **42/42 lượt memory thành công**. Mỗi nhóm trong bảng có 30 timing và tối đa 3 mẫu memory độc lập. Ba seed là 3 đề độc lập; 10 lượt lặp mỗi seed đo dao động thời gian, không biến thành 30 đề độc lập.

Thời gian và node là median trên timing solved. Memory là median peak cấp phát Python trong `solve()`, đo bằng `tracemalloc` sau khi nạp input; không phải RSS. Memory thất bại được loại khỏi mẫu memory và giữ nguyên trạng thái trong raw. Nguồn dữ liệu: [raw CSV](results/raw/benchmark.csv), [raw JSON](results/raw/benchmark.json), [summary](results/tables/summary.csv). Xem thêm [nguồn gốc bộ kết quả và cách đo lại](results/README.md).

Các bản ghi có full commit, trạng thái Git, `source_sha256`, `manifest_sha256`, `input_sha256`, `benchmark_timeout_s` và `benchmark_repeats`. API không được truyền hash manifest ghi `unknown`; CLI tính hash từ đúng bytes đã đọc. Bộ 360 lượt cũ tại commit được ghi nhận `7a80ea9` được giữ nguyên trong `results/archive/7a80ea9/`, không trộn vào số liệu mới.

| Puzzle | Kích thước | Độ khó | Thuật toán | Solved / lượt | Median thời gian (ms) | Median memory (KiB) | Median node mở rộng |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| Futoshiki | 4x4 | Easy | DFS | 30/30 | 0.40 | 8.71 | 8 |
| Futoshiki | 4x4 | Easy | GBFS | 30/30 | 0.54 | 8.95 | 8 |
| Futoshiki | 5x5 | Medium | DFS | 30/30 | 1.11 | 15.22 | 16 |
| Futoshiki | 5x5 | Medium | GBFS | 30/30 | 2.45 | 17.71 | 20 |
| Futoshiki | 6x6 | Hard | DFS | 30/30 | 5.04 | 37.33 | 53 |
| Futoshiki | 6x6 | Hard | GBFS | 30/30 | 5.78 | 31.51 | 38 |
| Pipes | 5x5 | Hard | DFS | 30/30 | 304.40 | 122.46 | 268 |
| Pipes | 5x5 | Hard | GBFS | 30/30 | 322.50 | 123.60 | 249 |
| Pipes | 6x6 | Hard | DFS | 30/30 | 852.96 | 251.33 | 420 |
| Pipes | 6x6 | Hard | GBFS | 30/30 | 929.19 | 268.13 | 434 |
| Pipes | 7x7 | Hard | DFS | 30/30 | 2642.87 | 700.81 | 1098 |
| Pipes | 7x7 | Hard | GBFS | 30/30 | 3861.51 | 1027.31 | 1421 |
| Pipes | 8x8 | Hard | DFS | 30/30 | 6958.31 | 1504.75 | 1904 |
| Pipes | 8x8 | Hard | GBFS | 30/30 | 11240.70 | 2130.86 | 2689 |

## 7. Kiểm tra dữ liệu và chạy tests

### `scripts/validate_submission.py`

```bash
python scripts/validate_submission.py
```

Script không có flags; đọc `data/benchmark_manifest.json`, kiểm tra ít nhất 21 đề, đủ tối thiểu 3 đề cho mỗi nhóm puzzle/kích thước/độ khó chuẩn, checksum, ID không trùng và đúng một nghiệm. Mã thoát `0` khi hợp lệ, `1` khi có lỗi.

### Các file kiểm thử

```bash
python -m pytest -q
python -m pytest tests/unit/test_pipes.py -q
python -m pytest tests/integration -q
```

`-q` giảm thông tin in ra; đối số đường dẫn chọn file hoặc thư mục tests cần chạy.

Nếu máy không có Tk, có thể chạy phần core/CLI/benchmark sau; đây là **một phần suite**, không thay thế kiểm tra đầy đủ:

```bash
python -m pytest tests/unit/test_futoshiki.py tests/unit/test_pipes.py \
  tests/unit/test_search.py tests/unit/test_summary.py tests/unit/test_dataset.py \
  tests/unit/test_benchmark_metadata.py tests/unit/test_ui_imports.py \
  tests/integration -q
```

Để đo coverage sau khi cài `.[dev]`:

```bash
python -m pytest --cov=logic_search --cov-branch --cov-report=term-missing
```

Coverage cấu hình cho toàn bộ package, kể cả model, parser, GUI và benchmark. Các worker benchmark dùng process spawn riêng; không mặc nhiên coi code trong process con đã được công cụ coverage theo dõi. Phần GUI kiểm tra bằng đối tượng giả chưa thay thế được thử tương tác cửa sổ thực tế.

| File | Nội dung kiểm tra |
| --- | --- |
| `tests/unit/test_dataset.py` | Checksum, cấu hình và nghiệm duy nhất của ba đề Pipes 5×5. |
| `tests/unit/test_pipes.py` | Phép xoay, ràng buộc, parser và generator Pipes. |
| `tests/unit/test_pipes_playback.py` | Thử/giữ/loại hướng và lý do loại, màu tìm kiếm, quay lui DFS/chuyển nhánh GBFS, phát từng bước và xóa trạng thái thử khi hủy hoặc kết thúc. |
| `tests/unit/test_futoshiki.py` | Miền giá trị, bất đẳng thức, parser, nghiệm giữ nguyên givens và event Futoshiki. |
| `tests/unit/test_search.py` | DFS, GBFS, frontier, event và hủy tìm kiếm. |
| `tests/unit/test_game_logic.py` | Thao tác chơi, xung đột và gợi ý Futoshiki liên tiếp/sau Reset. |
| `tests/unit/test_branch_integration.py` | Kết hợp puzzle, sự kiện, canvas, timeout loại thời gian callback và controller. |
| `tests/unit/test_player_flags_shortcuts.py` | Cờ, hoàn tác và phím tắt Pipes. |
| `tests/unit/test_metrics_panel.py` | Giữ số đo và depth khi nhận các loại sự kiện khác nhau. |
| `tests/unit/test_summary.py` | Tách nhóm kích thước và không đếm lặp mẫu memory. |
| `tests/unit/test_benchmark_metadata.py` | Commit, trạng thái working tree và checksum nguồn khi mã thay đổi. |
| `tests/unit/test_ui_imports.py` | Import logic chơi/controller khi Tkinter không có sẵn. |
| `tests/integration/test_end_to_end.py` | Giải đề và kiểm tra nghiệm đầu cuối. |
| `tests/integration/test_benchmark.py` | Chạy benchmark và kiểm tra dữ liệu xuất. |
| `tests/integration/test_cli.py` | Mã thoát và lỗi input khi tile/op có kiểu hoặc giá trị không hợp lệ. |

### Kiểm tra đã thực hiện cho bản trực quan hóa Pipes

Phần mã nguồn được đưa vào commit `ca97908` đã được kiểm tra trong môi trường Conda cục bộ với **Python 3.10.21, Tk 8.6 và pytest 9.1.1**:

- `python -m pytest -q`: **131 passed**. Kiểm thử tích hợp đối chiếu chế độ trực quan với chế độ thường cho DFS/GBFS trên đề Pipes nối biên có/không có ô khóa; đường nghiệm, action và số đo tìm kiếm khớp nhau, ngoại trừ thời gian chạy.
- `python scripts/validate_submission.py`: **Validated 21 unique, checksummed inputs**.
- Kiểm tra cửa sổ Tkinter ẩn: chú giải, màu thử/loại hướng, Run, Cancel, Reset, chạy lại và chuyển sang Futoshiki hoạt động. Đây chưa phải kiểm tra trực quan thủ công trên cửa sổ hiển thị.

Đây là kết quả kiểm tra local của phiên bản trên, chưa phải kiểm chứng cài đặt gói trên Python 3.10. Yêu cầu phát hành trong `pyproject.toml` vẫn là **Python ≥3.11**, môi trường tái lập vẫn dùng `environment-dev.yml`. Số test có thể thay đổi ở các commit sau. Không chạy lại benchmark đầy đủ trong lần kiểm tra này.
