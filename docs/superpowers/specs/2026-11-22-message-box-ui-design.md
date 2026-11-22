# Giao diện khung tin nhắn cho trang gợi ý khi gõ (22/11/2026)

## Mục đích
Người dùng muốn demo trông như ô soạn tin của app nhắn tin, gợi ý sửa ngay trong lúc gõ, không màu mè. Đây là demo chính
khi thuyết trình; demo Streamlit giữ nguyên làm dự phòng.

## Đã chốt với người dùng
- Nền trắng, chỉ một khung soạn tin + nút Gửi; không có lịch sử trò chuyện.
- Danh sách gợi ý trồi lên phía trên khung. Mỗi dòng là **cả câu** (từ đúng giữ nguyên, từ sai đã sửa, từ vừa gõ được đoán),
  các dòng khác nhau ở chỗ hệ thống chưa chắc. Bấm dòng nào thì cả khung đổi thành câu đó.
- Bấm Gửi: chữ trong khung giữ nguyên; danh sách trồi lên hiện các câu đã sửa (mô hình sửa cả câu, tối đa 3) và 1 câu diễn
  đạt lại ý.

- (Bổ sung cùng ngày) Gõ `.` `!` `?` `…` là sang câu mới: danh sách chỉ gợi ý cho câu chứa con trỏ (mặc định câu đang gõ);
  bấm vào câu cũ để sửa riêng câu đó. Dấu chấm giữa hai chữ số không tính. Gửi vẫn sửa cả tin nhắn.

## Cách làm (một hướng hợp lý)
Nâng cấp `app/realtime` (WebSocket). Streamlit không bắt được từng phím gõ nên bị loại.
- `Session.sentences(text, n=3)`: ghép tối đa 3 câu từ phương án của từng từ; chỉ từ "chưa chắc" (`uncertain`) mới có
  phương án thay thế; xếp theo tổng độ lệch điểm so với phương án đầu của từng từ. Từ đang gõ dở và phần chữ giữa các từ giữ
  nguyên theo ô nhập. Ẩn danh sách khi câu duy nhất trùng chữ đang có.
- `Session.pick(picks)`: bấm một câu = chọn phương án cho các từ chưa chắc hoặc khác chữ đang hiện (khóa lại, ghi log).
- Server dùng `src.pipeline.assistant.from_config()` (một lần nạp: bộ sửa lỗi + diễn đạt + bộ xếp hạng); tầng ViT5 của
  phiên dùng chính bộ sửa lỗi đó. Gửi: trả câu đã sửa trước, câu diễn đạt sau (chậm hơn); không đưa câu diễn đạt khi câu đã
  sửa còn từ lạ hoặc không ứng viên nào qua bộ lọc (giữ quy tắc cũ).
- Gạch chân từ chưa chắc ngay trong khung bằng lớp chữ trong suốt nằm dưới ô nhập (Claude chọn).

## Không làm
Lịch sử trò chuyện, gợi ý theo từng ký tự, khung điện thoại, màu mè.
