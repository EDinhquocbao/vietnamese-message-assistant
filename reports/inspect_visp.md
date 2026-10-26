# Khảo sát VISP (ngwgsang/ViSP)

## Cấu trúc
- Tổng số dòng: 1,177,942
- Các split gốc: {'train': 406308, 'validation': 391044, 'test': 380590}
- Cột: ['original_id', 'paraphrase_id', 'source', 'topic', 'original_text', 'paraphrase_text']

## Kiểu dữ liệu và giá trị rỗng
```
original_id        str
paraphrase_id      str
source             str
topic              str
original_text      str
paraphrase_text    str
_orig_split        str
dtype: object
---
original_id        0
paraphrase_id      0
source             0
topic              0
original_text      0
paraphrase_text    0
_orig_split        0
dtype: int64
```

## Cột được dùng
- source = `original_text`, target = `paraphrase_text` (kiểm tra xem có đúng chiều không!)

## Độ dài
```
       source_chars  target_chars  source_words  target_words
count     1177942.0     1177942.0     1177942.0     1177942.0
mean          123.9         123.9          27.4          27.4
std            50.3          50.3          10.9          10.9
min             9.0           9.0           2.0           2.0
50%           117.0         117.0          26.0          26.0
90%           192.0         192.0          42.0          42.0
99%           269.0         269.0          59.0          59.0
max           589.0         589.0         127.0         127.0
```

## Chất lượng
- Cặp source == target: 0.10%
- Source rỗng: 0; target rỗng: 0
- Cặp (source, target) trùng hoàn toàn: 10,527
- Số source duy nhất: 234,415; số target duy nhất: 234,415
- Số target xuất hiện >1 lần: 234,415

## Cấu trúc nhóm (ViSP)
- Số câu gốc duy nhất (original_id): 46,922
- Số paraphrase mỗi câu gốc:
```
count    46922.00
mean        25.10
std         23.22
min          6.00
25%         12.00
50%         12.00
75%         42.00
max        132.00
dtype: float64
```
- Câu gốc xuất hiện ở >1 split gốc: 0

- topic: {'health': 458342, 'science': 126154, 'politics_society': 108874, 'business': 93502, 'lifestyle': 87836, 'other': 85176, 'culture': 79528, 'law': 67362, 'sports': 45734, 'computer': 25434}
- source: {'ViNewsQA': 499178, 'ViNLI': 445852, 'ViQuAD': 197948, 'ALQAC': 34964}

## 15 mẫu ngẫu nhiên (seed=42)

- **S:** HCDC chiều 21/5 thông báo tìm người đến nhà sách Nguyễn Huệ và Starbucks coffee ở góc đường Phạm Hồng Thái tại quận 1, vào thời gian có mặt người mắc Covid-19.
  **T:** Chiều 21/5, HCDC đã thông báo tìm những người đã đến nhà sách Nguyễn Huệ và quán cà phê Starbucks ở góc đường Phạm Hồng Thái, quận 1, trong khoảng thời gian có người nhiễm Covid-19.
- **S:** Tại thời điểm này trong năm 2019, chỉ có 10% số xe phải đỗ một chỗ do cùng một lý do.
  **T:** Tỷ lệ xe phải đỗ một chỗ do cùng một lý do trong năm 2019 vào thời điểm này chỉ là 10%.
- **S:** Theo bác sĩ Cảnh, việc cố bóc nhau thai có thể gây mất máu nghiêm trọng cho sản phụ, đồng thời gây tổn thương đến tử cung và các cơ quan lân cận.
  **T:** Theo bác sĩ Cảnh, cố gắng bóc nhau thai sẽ khiến sản phụ bị mất máu trầm trọng và gây tổn thương nghiêm trọng cho tử cung và các cơ quan xung quanh.
- **S:** Việc dự đoán diễn biến bệnh rất khó khăn, do nó phụ thuộc nhiều vào tình trạng sức khỏe của từng trẻ.
  **T:** Tiên lượng bệnh rất khó khăn, do phụ thuộc vào thể trạng của từng trẻ nhỏ.
- **S:** Do đồ ăn ở Anh không hợp khẩu vị, cô ấy quyết định tự nấu ăn mỗi ngày để vừa tiết kiệm, vừa ngon miệng và đảm bảo sức khỏe trong thời gian xa nhà.
  **T:** Đồ ăn ở Anh không hợp khẩu vị nên cô quyết định tự chuẩn bị bữa ăn mỗi ngày để vừa tiết kiệm, ngon miệng lại an toàn cho sức khỏe trong thời gian xa nhà.
- **S:** Quá trình làm sạch hệ thống được thể hiện rõ qua một phần kênh đào.
  **T:** Một phần kênh đào minh họa quá trình làm sạch hệ thống.
- **S:** Có thể thấy, khái niệm nhu cầu và nhu yếu có mối quan hệ tương đối với nhau.
  **T:** Như vậy khái niệm nhu cầu và nhu yếu mang tính tương đối với nhau.
- **S:** Djokovic đã giành chiến thắng trước Tsitsipas, nâng chuỗi thắng lên bốn trận, và lần thứ tám liên tiếp góp mặt ở bán kết Rome Masters.
  **T:** Djokovic tiếp tục mạch thắng lên bốn trận bằng cách đánh bại Tsitsipas, qua đó giành vé vào bán kết Rome Masters lần thứ tám liên tiếp.
- **S:** Chức vô địch Ngoại hạng Anh mùa giải 2020-2021 đã nâng tổng số danh hiệu của Guardiola với tư cách là huấn luyện viên lên con số 31.
  **T:** Guardiola đã có 31 danh hiệu trong sự nghiệp huấn luyện, trong đó có chức vô địch Ngoại hạng Anh 2020-2021.
- **S:** Mục tiêu của Pairs là kết nối những người độc thân nghiêm túc trong hôn nhân, đồng thời tạo điều kiện cho phụ nữ cảm thấy thoải mái hơn với việc tìm kiếm bạn đời trực tuyến.
  **T:** Pairs nhắm đến những người độc thân nghiêm túc trong hôn nhân và khiến phụ nữ cảm thấy thoải mái khi nghĩ đến chuyện kết đôi trực tuyến.
- **S:** Fanpage chính thức của thị trấn Bitche đã bị Facebook khóa trong 3 tuần vì lý do phát âm của tên thị trấn có thể bị hiểu nhầm là một từ tục tĩu.
  **T:** Facebook đã tạm khóa fanpage chính thức của thị trấn Bitche trong 3 tuần do phát âm của tên thị trấn có thể gây hiểu nhầm với một từ mang nghĩa xúc phạm.
- **S:** Hai trường hợp sản phụ mắc Covid-19 sinh con thành công đã được ghi nhận tại Bệnh viện Bệnh nhiệt đới Trung ương.
  **T:** Đến nay, đây là sản phụ mắc Covid-19 thứ hai sinh con thành công tại Bệnh viện Bệnh nhiệt đới Trung ương.
- **S:** Bà không muốn rời bỏ quê hương và công việc yêu thích, nên đã từ chối lời mời của con cháu sang Mỹ an hưởng tuổi già.
  **T:** Dù con cháu nhiều lần đề nghị bà sang Mỹ an dưỡng tuổi già, bà vẫn quyết tâm ở lại để tiếp tục cống hiến cho điện ảnh.
- **S:** Đối với công đức, tài trợ bằng kim loại quý, đá quý, người làm công đức, tài trợ chuyển giao cho cơ sở quản lý di tích kèm theo các giấy tờ có liên quan.
  **T:** Việc tài trợ bằng kim loại quý, đá quý cần được chuyển giao cho cơ sở quản lý di tích kèm theo các giấy tờ chứng minh nguồn gốc, nhằm ghi nhận công đức cho người tài trợ.
- **S:** Chất lượng hệ thống đường bộ ở Đông Malaysia kém phát triển và thấp hơn so với Malaysia bán đảo.
  **T:** Hệ thống đường bộ ở Đông Malaysia có chất lượng thấp hơn và kém phát triển hơn so với phần còn lại của Malaysia.
