# Khảo sát VILEXNORM (https://raw.githubusercontent.com/ngxtnhi/ViLexNorm/1070c6b9b00830fad278f48d9797df9ae1c942ac/data)

## Cấu trúc
- Tổng số dòng: 10,467
- Các split gốc: {'train': 8372, 'validation': 1050, 'test': 1045}
- Cột: ['original', 'normalized']

## Kiểu dữ liệu và giá trị rỗng
```
original       str
normalized     str
_orig_split    str
dtype: object
---
original       0
normalized     0
_orig_split    0
dtype: int64
```

## Cột được dùng
- source = `original`, target = `normalized` (kiểm tra xem có đúng chiều không!)

## Độ dài
```
       source_chars  target_chars  source_words  target_words
count       10467.0       10467.0       10467.0       10467.0
mean           49.0          52.6          12.3          12.5
std            37.1          38.7           8.9           9.0
min            11.0          14.0           4.0           4.0
50%            38.0          41.0          10.0          10.0
90%            90.0          95.0          22.0          22.4
99%           196.0         207.0          48.0          48.3
max           550.0         553.0         131.0         131.0
```

## Chất lượng
- Cặp source == target: 0.00%
- Source rỗng: 0; target rỗng: 0
- Cặp (source, target) trùng hoàn toàn: 1
- Số source duy nhất: 10,466; số target duy nhất: 10,450
- Số target xuất hiện >1 lần: 17

## 15 mẫu ngẫu nhiên (seed=42)

- **S:** Mình k bh tin đc bọn trẻ con dù nắm chặt tay đến mấy, qua đường mình toàn bế sang, bh nó đủ nhận thức đi song song vs mình thì mới dắt, chứ cầm tay tụi nó vẫn lao về phía trước đc ~~
  **T:** Mình không bao giờ tin được bọn trẻ con dù nắm chặt tay đến mấy, qua đường mình toàn bế sang, bao giờ nó đủ nhận thức đi song song với mình thì mới dắt, chứ cầm tay tụi nó vẫn lao về phía trước được ~~
- **S:** Thực sự nói ra chắc bị chử.i nhưng chương trình đang sang cảm thấy bớt sang hẳn huhuuuuuuuuuuu.
  **T:** Thực sự nói ra chắc bị chửi nhưng chương trình đang sang cảm thấy bớt sang hẳn huhuuuuuuuuuuu.
- **S:** em cũng đáng iu như vậy đúng không?
  **T:** em cũng đáng yêu như vậy đúng không?
- **S:** trường cta trời nóng bật điều hoà đến mức sv bị cảm lạnh luôn =)))
  **T:** trường chúng ta trời nóng bật điều hoà đến mức sinh viên bị cảm lạnh luôn =)))
- **S:** Trc ở VN cũng có kb giờ đôi đó thế nào
  **T:** Trước ở VN cũng có không biết giờ đôi đó thế nào
- **S:** bữa nào a cũng v quó.
  **T:** bữa nào anh cũng vậy quá.
- **S:** Cái đổi đời meme này đúng đang nói t nè
  **T:** Cái đổi đời meme này đúng đang nói tôi nè
- **S:** Vai với eo nó bé m ơi :)))
  **T:** Vai với eo nó bé mày ơi :)))
- **S:** Nếu k cùng nhau nc để hiểu nhau hơn thì hôn nhân đi vào ngõ cụt la đúng thôi
  **T:** Nếu không cùng nhau nói chuyện để hiểu nhau hơn thì hôn nhân đi vào ngõ cụt là đúng thôi
- **S:** Đi trong bụng ng ta hay j
  **T:** Đi trong bụng người ta hay gì
- **S:** T ko cần tưởng tượng cũng đủ khóc sẵn rồi
  **T:** Tôi không cần tưởng tượng cũng đủ khóc sẵn rồi
- **S:** ngừi iu em y hệt lun ạ
  **T:** người yêu em y hệt luôn ạ
- **S:** Gòi gòi mình đã tìm được nhà của mình gòi
  **T:** Rồi rồi mình đã tìm được nhà của mình rồi
- **S:** Sao hay ra zẻ qá
  **T:** Sao hay ra vẻ quá
- **S:** coi z chứ tui có nhiều kinh nghiệm sống đó
  **T:** coi vậy chứ tui có nhiều kinh nghiệm sống đó
