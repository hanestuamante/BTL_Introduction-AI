# Cờ đánh dấu và phím tắt cho Pipes

Tính năng nằm trên nhánh `feat/player-flags-shortcuts`, phát triển từ
`chore/english-only`. Chỉ trò Pipes có các thay đổi này; giao diện, phím tắt
và cách chơi Futoshiki được giữ như bản tiếng Anh. GUI dùng ASCII; cờ tím được vẽ bằng nét và đa giác,
không phụ thuộc font hay emoji.

## Gắn cờ

- Rê con trỏ chuột lên ô rồi nhấn **F** để gắn/bỏ cờ cho ô dưới con trỏ,
  không cần bấm chọn ô. Thao tác này giữ nguyên ô đang chọn để xoay.
- **Shift + bấm trái** cũng gắn/bỏ cờ trực tiếp vào ô được bấm.
- Nút **Flag (F)** / **Unflag (F)** trên thanh công cụ áp dụng cho ô vừa
  được rê chuột qua, để vẫn bấm được nút sau khi rời bàn chơi.
- Nhấn **F** khi con trỏ ở ngoài bàn chơi sẽ không gắn cờ vào ô cũ.
- Thực hiện lại để bỏ cờ.
- Cờ thể hiện nhận định của người chơi; chương trình không xác nhận ô đó đúng.
- Cờ không khóa ô và không ràng buộc thuật toán. Khi xoay ống hoặc dùng
  Hint đổi hướng của ô, cờ trên ô đó tự bỏ; cờ ở các ô khác được giữ nguyên.
- Rê chuột lên ô rồi dùng **Q/E** để xoay ô đó ngược/thuận chiều kim đồng hồ.
  Không cần bấm chọn ô; thao tác giữ nguyên ô đang chọn. Ngoài bàn chơi,
  Q/E không tác động. Quy tắc ô khóa của đề vẫn được giữ nguyên.
- **Ctrl + bấm trái** chỉ chọn ô. Các nút **Rotate CCW (Q)** và
  **Rotate CW (E)** trên thanh công cụ xoay ô đang chọn.
- **Undo** khôi phục cả trạng thái ô và các cờ, kể cả thao tác gắn/bỏ/xóa cờ.
- Load, Reset hoặc bắt đầu lượt tìm kiếm mới sẽ xóa cờ. Hãy hủy lượt tìm kiếm
  trước khi chỉnh ghi chú thủ công.

## Phím tắt trong Pipes

| Thao tác | Phím |
| --- | --- |
| Browse | Ctrl+O |
| Load đường dẫn hiện tại | Ctrl+L |
| Check | C |
| Hint | H |
| Undo | Ctrl+Z |
| Reset | Ctrl+R |
| Gắn/bỏ cờ ô dưới con trỏ | F hoặc Shift+bấm trái |
| Xóa tất cả cờ | Ctrl+Shift+F |
| Chọn ô Pipes mà không xoay | Ctrl+bấm trái |
| Xoay ô dưới con trỏ ngược/thuận chiều kim đồng hồ | Q / E |
| Run | Enter |
| Pause/Resume | Space |
| Step | S hoặc mũi tên phải |
| Cancel | Esc |
| Chuyển DFS/GBFS khi không chạy | A |
| Tăng/giảm tốc độ phát lại | + / - |

Các nút thao tác trong Pipes ghi phím tắt trong ngoặc. Khi đang nhập trong ô đường dẫn hoặc chọn thuật toán, các phím
chữ và phím chỉnh sửa giữ hành vi gốc; Ctrl+O và Ctrl+L vẫn hoạt động.

Cờ là dữ liệu trong phiên chơi, không được ghi vào đề JSON hoặc kết quả benchmark.
Solver tiếp tục dùng đề gốc. Tính năng thử nghiệm xem lý do loại hướng ống
ở nhánh trước đã được bỏ khỏi nhánh này.
