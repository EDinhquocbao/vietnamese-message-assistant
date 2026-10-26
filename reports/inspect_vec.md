# Khảo sát VEC (yammdd/vietnamese-error-correction-corpus)

## Cấu trúc
- Tổng số dòng: 70,557
- Các split gốc: {'train': 56445, 'test': 7056, 'validation': 7056}
- Cột: ['input', 'target']

## Kiểu dữ liệu và giá trị rỗng
```
input          str
target         str
_orig_split    str
dtype: object
---
input          0
target         0
_orig_split    0
dtype: int64
```

## Cột được dùng
- source = `input`, target = `target` (kiểm tra xem có đúng chiều không!)

## Độ dài
```
       source_chars  target_chars  source_words  target_words
count       70557.0       70557.0       70557.0       70557.0
mean           60.8          61.8          13.9          14.0
std            59.9          60.0          13.2          13.2
min             1.0           1.0           1.0           1.0
50%            47.0          47.0          11.0          11.0
90%           115.0         117.0          26.0          26.0
99%           303.0         304.0          67.0          67.0
max          3367.0        3367.0         623.0         623.0
```

## Chất lượng
- Cặp source == target: 15.36%
- Source rỗng: 0; target rỗng: 0
- Cặp (source, target) trùng hoàn toàn: 15
- Số source duy nhất: 70,453; số target duy nhất: 70,122
- Số target xuất hiện >1 lần: 268

## 15 mẫu ngẫu nhiên (seed=42)

- **S:** Võ Minh Hiếu check ib ông ơi
  **T:** Võ Minh Hiếu check inbox ông ơi
- **S:** Chúa sẽ phù hộ độ trì cho cụ a Di đà phật
  **T:** Chúa sẽ phù hộ độ trì cho cụ A Di Đà Phật
- **S:** mọi người qua ủng hộ anh độ nhé
  **T:** mọi người qua ủng hộ anh Độ nhé
- **S:** Cực kì cái con mã mẹ tụi mày chứ thuyết phục
  **T:** Cực kì cái con mã mẹ tụi mày chứ thuyết phục
- **S:** thằng lồn này chỉ biết tham Mu chứ biết cc gì
  **T:** thằng lồn này chỉ biết tham MU chứ biết con cặc gì
- **S:** Mấy chị này hồi xưa làm trong hội bánh trán
  **T:** Mấy chị này hồi xưa làm trong hội bánh tráng
- **S:** Jang Dong Gun kin tieng chuyen yeu duong.
  **T:** Jang Dong Gun kín tiếng chuyện yêu đương.
- **S:** Sao kg im lặng giải quyết, cứ lên mạng kể làm gì có hiệp sĩ nào giúp thay đổi đc đâu
  **T:** Sao không im lặng giải quyết, cứ lên mạng kể làm gì có hiệp sĩ nào giúp thay đổi đượcđâu
- **S:** Lua thieu rui tiem tap hoa, khu chung cu nao loan.
  **T:** Lửa thiêu rụi tiệm tạp hóa, khu chung cư náo loạn.
- **S:** tuy nhiinê, ở hnung địa đtểm nệch eef phisa đoong lhiều hown thì sự lệch múi giờ sẽ dẫn towsi lệch về ngafy.
  **T:** tuy nhiên, ở những địa điểm lệch về phía đông nhiều hơn thì sự lệch múi giờ sẽ dẫn tới lệch về ngày.
- **S:** Yumi Duong dien mot khong quan sexy trong phong ngu.
  **T:** Yumi Dương diện mốt không quần sexy trong phòng ngủ.
- **S:** Nghe rất là vô sinh nhưng lại có bầu
  **T:** Nghe rất là vô sinh nhưng lại có bầu
- **S:** Chao mung den voi Oymyakon, khu vuc co nguoi o lanh nhat tren Trai dat.
  **T:** Chào mừng đến với Oymyakon, khu vực có người ở lạnh nhất trên Trái đất.
- **S:** Diem tin Bongda24h sang 17/4: M.U tranh sao tre Tete voi Juventus.
  **T:** Điểm tin Bongda24h sáng 17/4: M.U tranh sao trẻ Tete với Juventus.
- **S:** Xot xa mua chim troi di tru Ha Noi!.
  **T:** Xót xa mùa chim trời di trú Hà Nội!.
