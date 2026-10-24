# Dàn ý slide (12 trang)

1. Bài toán và yêu cầu.
2. Lý do chọn Pipes và Futoshiki.
3. Mô hình hóa Pipes.
4. Mô hình hóa Futoshiki.
5. DFS iterative.
6. GBFS và heuristic.
7. Kiến trúc ứng dụng.
8. Demo Pipes: chú giải màu, thử/giữ/loại hướng kèm lý do, quay lui DFS và chuyển nhánh GBFS; dùng Pause/Step/Resume.
9. Demo Futoshiki: pause/step/back.
10. Kết quả benchmark và biểu đồ.
11. Trade-off thời gian/bộ nhớ, timeout.
12. Kết luận và phân công.

Lấy số liệu từ `results/tables/summary.csv`: bộ chính có 21 đề (9 Futoshiki,
12 Pipes 5×5–8×8), 420 lượt timing. Ghi rõ mã được đo là commit `054bb6f`;
chưa đo lại sau cập nhật trực quan hóa `ca97908`. Không nhập số ước lượng.

Demo theo [hướng dẫn màu và phát từng bước Pipes](../docs/PIPES_SEARCH.md).
Giải thích màu tím chỉ là ứng viên trong nhánh đang xét, màu xanh lá xác nhận
nghiệm hoàn chỉnh; việc GBFS chuyển nhánh không kết luận nhánh cũ thất bại.
