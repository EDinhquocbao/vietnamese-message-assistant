# Kế hoạch cải tiến sau khi thử demo (bắt đầu 26/10/2026)

Bối cảnh: mô hình sửa lỗi v1 (ViT5-base, 3 epoch trên VSEC + ViLexNorm + VEC) sửa tốt viết tắt/không dấu
nhưng gần như bỏ qua lỗi gõ nhanh. Đo trên 300 câu ViLexNorm test bị gây lỗi tự động:

| Kiểu lỗi | WER đầu vào | WER sau sửa (v1) | Câu đúng hết |
|---|---|---|---|
| Không dấu cả câu | 77,0% | 16,5% | 26,0% |
| Đảo chữ (1–2 từ) | 14,1% | 9,0% | 34,3% |
| Bấm hụt/thiếu chữ (1–2 từ) | 14,3% | 11,0% | 23,3% |
| Không dấu + đảo/thiếu chữ | 79,5% | 27,7% | 4,0% |

Nguyên tắc: mọi mẫu lỗi đều sinh tự động theo quy tắc ghi rõ; val/test giữ dữ liệu thật; mẫu sinh
từ câu test chỉ dùng để đánh giá, không bao giờ để train.

Trạng thái: ✅ xong · 🔄 đang làm · ⏳ chưa làm · 💤 để sau (nếu còn thời gian)

| # | Mục | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | Mô hình lỗi "gõ nhanh": bỏ dấu (cả câu/một phần) + đảo chữ, bấm hụt, phím bên cạnh, phím đúp, dính chữ, Telex dở; tăng lên ~90k câu | 🔄 | Dữ liệu xong (89.190 câu, `augment_report.json`); đang huấn luyện `vit5-base-aug` (2 epoch, 154k cặp) |
| 2 | Bộ test lỗi tự nhiên do người gõ | 💤 | Thay bằng bộ test sinh tự động theo hồ sơ "gõ nhanh" (mục 3) theo yêu cầu; hạn chế: lỗi nhân tạo có thể dễ hơn lỗi thật |
| 3 | Script đo theo từng kiểu lỗi (stress test) trên câu test held-out | ✅ | `src/correction/stress_test.py`, 400 câu ViLexNorm test × 8 kiểu lỗi, seed 2026 |
| 4 | So sánh với mô hình có sẵn `bmd1905/vietnamese-correction-v2` (BARTpho, Apache-2.0) | 🔄 | Đã tải, nạp được (`HubCorrector`); thử nhanh: sửa tốt lỗi gõ nhưng không hiểu teencode (e, r, c, vs) và hay tự thêm dấu câu/viết hoa. Chờ GPU để chạy stress test + 3 tập test |
| 5 | Mô hình mức ký tự ByT5-small | 💤 | chuỗi dài gấp ~3 lần, huấn luyện chậm 2–3 lần trên GPU 6 GB |
| 6 | Đưa 2–3 phương án sửa (N-best) cho từ không chắc chắn trong demo | ✅ | `Corrector.nbest`, `uncertain_words`; demo hiện "Chưa chắc chắn: ngày (hoặc: người yêu)" |
| 7 | Lọc nghĩa gợi ý bằng NLI hai chiều (mDeBERTa-v3 XNLI, MIT) | 🔄 | Code xong trong `Ranker`; đang chọn ngưỡng trên ViSP val. Thử tay: chặn được "Không nên mua sữa" (0,02) nhưng KHÔNG chặn được đảo vai "em gửi chị" -> "chị gửi em" (0,98) |
| 8 | Diễn đạt lại theo văn phong tin nhắn (dữ liệu sinh bằng LLM hoặc LLM nhỏ dùng prompt) | 💤 | tốn công nhất; đưa vào "hướng phát triển" |
| 9 | Hậu xử lý ký tự bị tokenizer chuẩn hóa ("…" -> "...", số lượng ")" trong "=))") | 💤 | lỗi nhỏ, phát hiện khi phân tích lỗi ViLexNorm |
| 10 | Huấn luyện thêm epoch cho mô hình diễn đạt lại (val loss còn giảm ở epoch 2) | 💤 | |
| 11 | Quy tắc phủ định chặn nhầm phủ định kép ("Đừng quên" ⇔ "Nhớ") | 💤 | phát hiện khi viết test NLI; có thể bỏ quy tắc khi NLI đã bật |
| 12 | Phát hiện đảo vai (ai làm gì cho ai) trong gợi ý | 💤 | cả embedding lẫn NLI đều bỏ sót; cần quy tắc theo đại từ hoặc mô hình khác |
