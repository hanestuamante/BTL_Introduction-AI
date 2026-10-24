# Báo cáo kiểm tra sau khi bổ sung Pipes 5×5

## Dữ liệu và cấu hình

Thêm ba file `pipes-5x5-hard-wrap-seed-501.json`, `-502.json`, `-503.json` trong
`data/pipes/`. Cấu hình: Hard, wrap=true, 24 ứng viên, node_limit=20000,
requested_lock_ratio=0.0. Cả ba có đúng một nghiệm và không cần thêm ô khóa.
Nguồn nước mặc định ở hàng 1, cột 1. Các đề cũ được giữ nguyên.

Manifest có 21 đề với checksum. Generator mặc định gồm Pipes 5×5–8×8; validator
yêu cầu tối thiểu ba đề cho mỗi nhóm chuẩn. Tests đầu cuối đã thêm cả ba đề mới
với DFS và GBFS; tests dữ liệu kiểm tra checksum, cấu hình, nguồn và nghiệm duy nhất.

## Kiểm tra đã thực hiện

- Toàn bộ suite: **115 passed in 6.63s** trong bản chuẩn bị trước benchmark.
- Validator: **Validated 21 unique, checksummed inputs**.
- Benchmark đầy đủ: **420/420 timing solved**, **42/42 memory solved**;
  42 warm-up, timeout 60 giây, 10 timing/cặp input/thuật toán.
- Commit package được đo: `054bb6fcd89823e54273ced470de5ef2e05c2594`; trạng thái Git tại lúc đo sạch.
- CSV và JSON khớp 420 bản ghi, đủ 42 cặp và repeat 1–10, checksum manifest/input khớp file thực tế.
- Summary sinh lại từ raw, gồm 14 nhóm; ba SVG hợp lệ và có cả hai cột thuật toán cho Pipes 5×5.
- Các bảng số liệu README được lấy trực tiếp từ summary, không điền số ước lượng.
- Bộ 360 lượt cũ được lưu riêng trong `results/archive/7a80ea9/`, không chỉnh sửa nội dung cũ.

## Phạm vi và giới hạn

Thử nghiệm dùng Python 3.14.7. Full suite cần thư viện Tk
có sẵn; các test giao diện dùng đối tượng giả và chưa thay thế kiểm tra cửa sổ thực tế.
Mỗi nhóm chỉ có ba đề độc lập. Peak memory là cấp phát Python, không phải RSS.
Đợt này không sửa cách Hint tính đồng bộ, không sửa báo cáo học thuật trong
`report/README.md`, không tạo lại môi trường Conda và không công bố phần trăm coverage.
