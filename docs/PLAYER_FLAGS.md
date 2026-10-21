# Cờ đánh dấu và phím tắt cho Pipes

Tính năng nằm trên nhánh `feat/player-flags-shortcuts`, phát triển từ
`chore/english-only`. Chỉ trò Pipes có các thay đổi này; giao diện, phím tắt
và cách chơi Futoshiki được giữ như bản tiếng Anh. GUI dùng ASCII; cờ tím được vẽ bằng nét và đa giác,
không phụ thuộc font hay emoji.

## Gắn cờ

- Chọn ô rồi bấm **Flag (F)**, hoặc dùng **Shift + bấm trái** trực tiếp vào ô.
- Thực hiện lại để bỏ cờ.
- Cờ thể hiện nhận định của người chơi; chương trình không xác nhận ô đó đúng.
- Cờ không khóa ô và không ràng buộc thuật toán. Khi xoay ống hoặc dùng
  Hint đổi hướng của ô, cờ trên ô đó tự bỏ; cờ ở các ô khác được giữ nguyên.
- Với Pipes, **Ctrl + bấm trái** chỉ chọn ô, không xoay. Dùng **Q/E** để xoay
  ngược/thuận chiều kim đồng hồ. Quy tắc ô khóa của đề vẫn được giữ nguyên.
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
| Gắn/bỏ cờ ô đang chọn | F hoặc Shift+bấm trái |
| Xóa tất cả cờ | Ctrl+Shift+F |
| Chọn ô Pipes mà không xoay | Ctrl+bấm trái |
| Xoay Pipes ngược/thuận chiều kim đồng hồ | Q / E |
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
