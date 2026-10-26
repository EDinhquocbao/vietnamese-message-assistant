# Khảo sát VSEC (nguyenthanhasia/vsec-vietnamese-spell-correction)

## Cấu trúc
- Tổng số dòng: 9,341
- Các split gốc: {'train': 9341}
- Cột: ['text', 'corrected_text', 'syllable_annotations', 'error_count', 'error_positions', 'correction_pairs', 'has_errors']

## Kiểu dữ liệu và giá trị rỗng
```
text                       str
corrected_text             str
syllable_annotations    object
error_count              int64
error_positions         object
correction_pairs        object
has_errors                bool
_orig_split                str
dtype: object
---
text                    0
corrected_text          0
syllable_annotations    0
error_count             0
error_positions         0
correction_pairs        0
has_errors              0
_orig_split             0
dtype: int64
```

## Cột được dùng
- source = `text`, target = `corrected_text` (kiểm tra xem có đúng chiều không!)

## Độ dài
```
       source_chars  target_chars  source_words  target_words
count        9341.0        9341.0        9341.0        9341.0
mean          135.8         135.8          30.2          30.2
std            57.7          57.7          12.8          12.8
min            20.0          20.0           4.0           4.0
50%           133.0         133.0          30.0          30.0
90%           218.0         218.0          48.0          48.0
99%           251.0         251.0          56.0          56.0
max           278.0         278.0          64.0          64.0
```

## Chất lượng
- Cặp source == target: 0.00%
- Source rỗng: 0; target rỗng: 0
- Cặp (source, target) trùng hoàn toàn: 0
- Số source duy nhất: 9,341; số target duy nhất: 9,331
- Số target xuất hiện >1 lần: 10

## 15 mẫu ngẫu nhiên (seed=42)

- **S:** Các thể hiện nội dung của từng chủ đề khác nhau.
  **T:** Cách thể hiện nội dung của từng chủ đề khác nhau.
- **S:** Ví dụ 2.2.5. Mai có 15 cái kẹo, Mai đự định chia đều cho 3 bạn Hoa, Ngân và Ly.
  **T:** Ví dụ 2.2.5. Mai có 15 cái kẹo, Mai dự định chia đều cho 3 bạn Hoa, Ngân và Ly.
- **S:** Trình bày bày được các quy luật di truyền, sinh lý, sinh thái của sinh vật.
  **T:** Trình bày được các quy luật di truyền, sinh lý, sinh thái của sinh vật.
- **S:** Bên cạnh đó, biến CS4 thuộc nhân tố chính sách cửa hàng, cụ thể là cửa hàng cung cấp nơi giữ xe thuận tiện và an toàn có giá trị trung bình thấp nhất (3,17) trong tất cả các biến quan sát chứng tỏ rằng yếu tố này chưa được người tiêu dùng đánh gía cao.
  **T:** Bên cạnh đó, biến CS4 thuộc nhân tố chính sách cửa hàng, cụ thể là cửa hàng cung cấp nơi giữ xe thuận tiện và an toàn có giá trị trung bình thấp nhất (3,17) trong tất cả các biến quan sát chứng tỏ rằng yếu tố này chưa được người tiêu dùng đánh giá cao.
- **S:** Khi Driving test nhóm sẽ qua sát chủ yếu giao diện này để phát hiện lỗi trong quá trình đo.
  **T:** Khi Driving test nhóm sẽ quan sát chủ yếu giao diện này để phát hiện lỗi trong quá trình đo.
- **S:** Thảo luận/ trả lời ác câu hỏi đúng trọng tâm/ rõ ràng/ dễ hiểu/ đầy đủ/ ngắn gọn.
  **T:** Thảo luận/ trả lời các câu hỏi đúng trọng tâm/ rõ ràng/ dễ hiểu/ đầy đủ/ ngắn gọn.
- **S:** Nếu giá trị là true thì hệ thống sẽ tạo bản tin thông báo nếu mức sử năng lượng của tòa nhà cao hơn mức cao nhất tính theo phần trăm và ngược lại nếu giá trị là false hệ thống sẽ bỏ qua.
  **T:** Nếu giá trị là true thì hệ thống sẽ tạo bản tin thông báo nếu mức sử dụng năng lượng của tòa nhà cao hơn mức cao nhất tính theo phần trăm và ngược lại nếu giá trị là false hệ thống sẽ bỏ qua.
- **S:** Theo [0][trang 11] "Kỹ năng là năng lực sử dụng các dữ kiện, các tri thức hay khái niệm đã có, năng lực vận dụng chúng để phát hiện những thuộc tính bản chất của các sự vật và giải quyết thành công nhiệm vụ lý luận hay thực thiễn xác định".
  **T:** Theo [0][trang 11] "Kỹ năng là năng lực sử dụng các dữ kiện, các tri thức hay khái niệm đã có, năng lực vận dụng chúng để phát hiện những thuộc tính bản chất của các sự vật và giải quyết thành công nhiệm vụ lý luận hay thực tiễn xác định".
- **S:** Hồ Chí Minh, Giáo trình pháp luật về hợp đồng và bồi thường thiệt hại ngoài hợp đồng (tái bản lần thứ nhất, có sửa đổi và bổi sung).
  **T:** Hồ Chí Minh, Giáo trình pháp luật về hợp đồng và bồi thường thiệt hại ngoài hợp đồng (tái bản lần thứ nhất, có sửa đổi và bổ sung).
- **S:** Tổ chức tuyên truyền, phổ biến, hướng dấn khai thác học liệu.
  **T:** Tổ chức tuyên truyền, phổ biến, hướng dẫn khai thác học liệu.
- **S:** Phỏng vấn trực tiếp một số cán bộ, nhân viên, người lao động tại công ty cổ phần Tiến bộ Thế giới về thực trạng đảm bảo an ninh con nguwoif tại công ty.
  **T:** Phỏng vấn trực tiếp một số cán bộ, nhân viên, người lao động tại công ty cổ phần Tiến bộ Thế giới về thực trạng đảm bảo an ninh con người tại công ty.
- **S:** Bên cạnh đó, huyện có những thung lũng được khai phát thành những ruộng lúa rộng như cánh đồng Bình Phúc, Yên Phúc, Vân Mộng, Trấn Ninh, Tân Đoàn, Tràng Phái.
  **T:** Bên cạnh đó, huyện có những thung lũng được khai phá thành những ruộng lúa rộng như cánh đồng Bình Phúc, Yên Phúc, Vân Mộng, Trấn Ninh, Tân Đoàn, Tràng Phái.
- **S:** Bằng cách ấy, các em vừa hứng thú, vừa từng bửớc khắc phục sai lầm của chính mình và không mắc lại sai lầm của bạn mà tiết học lại nhẹ nhàng.
  **T:** Bằng cách ấy, các em vừa hứng thú, vừa từng bước khắc phục sai lầm của chính mình và không mắc lại sai lầm của bạn mà tiết học lại nhẹ nhàng.
- **S:** Mối quan hê thông qua quyền sở hữu:
  **T:** Mối quan hệ thông qua quyền sở hữu:
- **S:** Trong thời kì kinh tế hội nhập, hàng hóa lưu thông dễ dàng từ trong nước ra ngoài nước những vẫn gặp nhiều khó khăn và thất bại vì việc kinh doanh không hề dễ dàng và thuận lợi nên chúng ta phải biết:
  **T:** Trong thời kì kinh tế hội nhập, hàng hóa lưu thông dễ dàng từ trong nước ra ngoài nước nhưng vẫn gặp nhiều khó khăn và thất bại vì việc kinh doanh không hề dễ dàng và thuận lợi nên chúng ta phải biết:
