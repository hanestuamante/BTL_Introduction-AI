# Nguồn gốc bộ kết quả thực nghiệm

## Bộ hiện tại: 21 đề, 420 lượt timing

`raw/benchmark.csv`, `raw/benchmark.json`, `tables/summary.csv` và ba SVG trong
`charts/` thuộc cùng một đợt đo mới trên 9 đề Futoshiki và 12 đề Pipes Hard nối biên
5×5, 6×6, 7×7, 8×8. Mỗi cặp input/thuật toán có 1 warm-up, 10 timing và 1 memory,
timeout 60 giây. Timing solved: 420/420; memory solved: 42/42.

- Commit mã được đo: `054bb6fcd89823e54273ced470de5ef2e05c2594`.
- Git working tree tại lần đo: `false` (không có thay đổi theo Git).
- SHA-256 các file Python trong package: `1de4e7d1eb5db91538f95b6402361eefab6c4ac81661faba0ee841d8c65ec8e1`.
- SHA-256 manifest: `315644a8d0d8d71a3a5cbc8e3e04b9ad9bbae5dbc8ad21dafc131788273d1427`.
- Python: `3.14.7`; interpreter: `/usr/bin/python3`.
- Hệ điều hành: `Linux-7.2.7-arch1-1-x86_64-with-glibc2.44`.
- Trường CPU: `x86_64`; đây có thể chỉ là kiến trúc, không xác nhận model CPU.

Mỗi dòng còn ghi checksum input, repeats, timeout và trạng thái memory. Summary
không đếm lặp mẫu memory gắn trên 10 dòng timing. Mỗi nhóm chỉ có ba đề độc lập.
Các commit chỉ cập nhật kết quả/tài liệu sau lần đo không thay đổi package đã đo.

## Bộ lịch sử: commit được ghi nhận 7a80ea9

Raw CSV/JSON, summary và ba biểu đồ ban đầu được giữ nguyên byte tại
`archive/7a80ea9/`. Bộ này có 18 đề, 360 timing và không chứa Pipes 5×5.
Nó không lưu trạng thái working tree, checksum nguồn/manifest hoặc timeout.
Không bổ sung hồi tố những giá trị chưa biết, không trộn số liệu lịch sử vào bộ mới.

## Đo lại

Chạy từ thư mục gốc sau khi cài theo README, dùng thư mục mới cho mỗi đợt đo:

```bash
python -m logic_search benchmark --manifest data/benchmark_manifest.json \
  --algorithms dfs gbfs --repeats 10 --timeout 60 \
  --csv results/current/raw.csv --json results/current/raw.json
python scripts/summarize_results.py results/current/raw.csv \
  --table results/current/summary.csv --charts results/current/charts
```

Lệnh ghi lại output nếu đường dẫn đã tồn tại. Checksum source chỉ đại diện cho
package Python, không thay thế thông tin dependency/môi trường. API không có
manifest ghi `manifest_sha256=unknown`. Chi tiết kiểm tra ở `docs/VERIFICATION.md`.
