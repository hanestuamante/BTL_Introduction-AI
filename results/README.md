# Nguồn gốc bộ kết quả thực nghiệm

`raw/benchmark.csv`, `raw/benchmark.json`, `tables/summary.csv` và ba SVG trong
`charts/` là cùng một bộ kết quả lịch sử. 360 bản ghi có commit được ghi nhận
`7a80ea9`, Python 3.14.7; mọi lượt timing và memory được gắn vào dữ liệu đều solved.
Summary và biểu đồ được tổng hợp từ raw CSV, không phải một lần đo mới.

Commit này khác phiên bản code hiện tại. Bộ cũ không ghi checksum mã nguồn,
manifest, timeout hoặc trạng thái working tree. Không thể khẳng định mã đo là
working tree sạch chỉ từ trường commit; không bổ sung hồi tố những giá trị chưa biết.
Giữ nguyên raw cũ để bảo toàn bằng chứng của đợt đo.

Các lần benchmark mới ghi full commit, trạng thái working tree, checksum nội dung
các file Python của package, checksum manifest/input và cấu hình repeats/timeout.
Checksum mã nguồn chỉ đại diện cho package Python, không thay thế thông tin môi trường
hoặc checksum dependency. API không có manifest ghi `manifest_sha256=unknown`.

Đo phiên bản mới từ thư mục gốc dự án, sau khi cài theo README:

```bash
python -m logic_search benchmark --manifest data/benchmark_manifest.json \
  --algorithms dfs gbfs --repeats 10 --timeout 60 \
  --csv results/current/raw.csv --json results/current/raw.json
python scripts/summarize_results.py results/current/raw.csv \
  --table results/current/summary.csv --charts results/current/charts
```

Lệnh ghi lại output nếu đường dẫn đã tồn tại. Chọn thư mục mới cho mỗi đợt đo.
Muốn công bố số liệu mới, cập nhật đồng thời raw, summary, biểu đồ, README và report,
kèm commit/cấu hình đã đo. Mười lượt lặp mỗi đề đo dao động runtime; mỗi nhóm chỉ
có ba đề độc lập. Không coi kết quả một lần giải smoke test là benchmark thay thế.
