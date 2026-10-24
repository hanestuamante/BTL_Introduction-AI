# Trực quan hóa tìm kiếm Pipes

Bấm **Run** để xem DFS hoặc GBFS giải đề gốc. Solver gán hướng cho các ô theo
thứ tự hàng–cột, giữ nguyên ô khóa; các hướng trên bàn chơi trước khi bấm Run
không phải những hướng đã được thuật toán xác nhận.

| Màu nền/viền ô | Ý nghĩa |
| --- | --- |
| Xám nhạt | Ô chưa được gán trong nhánh đang xét. Hình ống mờ là hướng ban đầu để tham khảo. |
| Vàng | Ô đang xét hoặc hướng đang được thử. |
| Tím nhạt | Hướng được giữ làm ứng viên hoặc đã gán trong nhánh hiện tại; chưa xác nhận nghiệm. |
| Đỏ | Hướng bị loại, node không sinh được child mới hoặc nhánh DFS đã xét hết. |
| Xanh lá | Toàn bộ bảng đã được kiểm tra là nghiệm. |

Màu xanh dương trên **thân ống** tiếp tục biểu thị nước từ nguồn. Nguồn đỏ,
viền khóa màu cam, đường nối biên và cờ ghi chú giữ ý nghĩa riêng. Khi bắt đầu
tìm kiếm, lựa chọn ô và cờ ghi chú được xóa để dễ theo dõi màu tìm kiếm.

Mỗi ô được phát lại theo trình tự: xét miền hướng hợp lệ cục bộ → thử từng
hướng khác nhau → giữ ứng viên hoặc loại kèm lý do. Một hướng có thể bị loại
vì chĩa ra ngoài biên, không khớp hàng xóm, tạo chu trình hoặc làm các ô chưa
gán mất hướng tương thích. Dòng trạng thái ghi hàng/cột và hướng bằng
`N / E / S / W` (Bắc / Đông / Nam / Tây).

**Pause**, **Resume**, **Step** và thanh tốc độ điều khiển cả những bước nhỏ này.
DFS hiển thị quay lui khi rời nhánh đã xét hết. GBFS ghi việc chuyển nhánh và
giá trị heuristic; chuyển nhánh không đồng nghĩa nhánh trước thất bại.

**Cancel** bỏ hướng đang thử, giữ các hướng trong node mở rộng gần nhất và
điền các ô chưa gán bằng hướng ban đầu để tiếp tục chơi. Màu tìm kiếm được xóa.
**Reset**, Load và lượt Run mới cũng xóa dấu dò cũ. Khi đang tìm kiếm, cần hủy
trước khi sửa ống, kiểm tra bàn hoặc chỉnh ghi chú.

Các sự kiện chi tiết chỉ phục vụ GUI/callback. CLI và benchmark dùng cùng quy
tắc, thứ tự action và phép kiểm tra nghiệm, không phát lại từng hướng. Số đo
node không đếm các bước tô màu là node mới. Kết quả benchmark lưu sẵn vẫn
thuộc phiên bản package được ghi trong metadata; chưa đo lại sau thay đổi này.
