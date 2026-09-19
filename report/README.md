# Khung báo cáo BTL1

File này là khung nội dung để nhóm điền thông tin thành viên và chuyển sang DOCX/PDF sau khi chạy benchmark chính thức.

## 1. Mục tiêu và hai bài toán

Ứng dụng giải Pipes và Futoshiki bằng DFS iterative và Greedy Best-First Search, trực quan hóa quá trình tìm kiếm và xuất số liệu thực nghiệm có thể tái lập.

## 2. Mô hình hóa

- Pipes dùng bitmask `N=1, E=2, S=4, W=8`; mỗi action gán một orientation cho ô tiếp theo. Goal phải khớp cạnh, liên thông và không chu trình.
- Futoshiki dùng tuple `N*N`, giá trị 0 là chưa gán. Goal là Latin square thỏa toàn bộ bất đẳng thức.

## 3. Thuật toán

Mô tả DFS, GBFS, cách dựng lại parent path, timeout/cancel và các heuristic đã cố định trong `model.py` của từng puzzle.

## 4. Dữ liệu và thực nghiệm

Bộ dữ liệu có 18 input: 2 puzzle × 3 mức × 3 seed. Manifest lưu SHA-256. Điền cấu hình máy, Python, timeout và số repeat từ raw CSV.

## 5. Kết quả

Chèn `results/tables/summary.csv` và ba biểu đồ SVG được tạo bởi `scripts/summarize_results.py`. Timeout phải giữ nguyên trong bảng, không quy đổi thành 0 ms.

## 6. Phân tích, hạn chế và kết luận

Phân tích runtime, peak Python memory, nodes expanded và success rate. Nêu rõ GBFS không tối ưu, heuristic phụ thuộc cấu trúc input và DFS có nguy cơ bùng nổ không gian tìm kiếm.

