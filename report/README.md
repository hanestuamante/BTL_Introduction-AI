# Khung báo cáo BTL1

File này là khung nội dung để nhóm điền thông tin thành viên, hoàn thiện phân tích và chuyển sang DOCX/PDF. Bộ benchmark lưu sẵn và phiên bản mã được đo được mô tả trong [nguồn gốc kết quả](../results/README.md).

## 1. Mục tiêu và hai bài toán

Ứng dụng giải Pipes và Futoshiki bằng DFS iterative và Greedy Best-First Search, trực quan hóa quá trình tìm kiếm và xuất số liệu thực nghiệm có thể tái lập.

## 2. Mô hình hóa

- Pipes dùng bitmask `N=1, E=2, S=4, W=8`; mỗi action gán một orientation cho ô tiếp theo. Goal phải khớp cạnh, liên thông và không chu trình.
- Futoshiki dùng tuple `N*N`, giá trị 0 là chưa gán. Goal là Latin square thỏa toàn bộ bất đẳng thức.

## 3. Thuật toán

Mô tả DFS, GBFS, cách dựng lại parent path, timeout/cancel và các heuristic đã cố định trong `model.py` của từng puzzle.

Phần minh họa Pipes cần giải thích màu chưa gán/đang thử/ứng viên/bị loại/nghiệm, lý do loại hướng và sự khác nhau giữa quay lui DFS với chuyển nhánh GBFS. Màu ứng viên chưa xác nhận ô đúng; xem [hướng dẫn trực quan hóa](../docs/PIPES_SEARCH.md).

## 4. Dữ liệu và thực nghiệm

Bộ dữ liệu chính có **21 input**: 12 đề Pipes Hard nối biên 5×5, 6×6, 7×7, 8×8 (3 seed/kích thước) và 9 đề Futoshiki Easy/Medium/Hard 4×4, 5×5, 6×6 (3 seed/mức). Manifest lưu SHA-256. Ba đề Pipes 6×6 có ô khóa trong `data/generated-pipes-wrap/` là bộ bổ sung, không thuộc 21 đề của đợt đo này.

Đợt benchmark lưu sẵn đo commit `054bb6f`, gồm 420 lượt timing (10 lượt/cặp đề–thuật toán), 42 warm-up và 42 lượt memory, timeout 60 giây. Điền cấu hình máy và Python từ metadata raw; không dùng môi trường kiểm thử local thay cho môi trường benchmark. Chưa đo lại sau commit `ca97908` bổ sung trực quan hóa Pipes.

## 5. Kết quả

Chèn `results/tables/summary.csv` và ba biểu đồ SVG được tạo bởi `scripts/summarize_results.py`. Timeout phải giữ nguyên trong bảng, không quy đổi thành 0 ms.

## 6. Phân tích, hạn chế và kết luận

Phân tích runtime, peak Python memory, nodes expanded và success rate. Nêu rõ GBFS không tối ưu, heuristic phụ thuộc cấu trúc input và DFS có nguy cơ bùng nổ không gian tìm kiếm.

