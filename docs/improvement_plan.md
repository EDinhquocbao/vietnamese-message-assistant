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
| 4 | So sánh với mô hình có sẵn `bmd1905/vietnamese-correction-v2` (BARTpho, Apache-2.0) | ✅ | Đã tải, nạp được (`HubCorrector`); thử nhanh: sửa tốt lỗi gõ nhưng không hiểu teencode (e, r, c, vs) và hay tự thêm dấu câu/viết hoa. Chờ GPU để chạy stress test + 3 tập test |
| 5 | Mô hình mức ký tự ByT5-small | 💤 | chuỗi dài gấp ~3 lần, huấn luyện chậm 2–3 lần trên GPU 6 GB |
| 6 | Đưa 2–3 phương án sửa (N-best) cho từ không chắc chắn trong demo | ✅ | `Corrector.nbest`, `uncertain_words`; demo hiện "Chưa chắc chắn: ngày (hoặc: người yêu)" |
| 7 | Lọc nghĩa gợi ý bằng NLI hai chiều (mDeBERTa-v3 XNLI, MIT) | 🔄 | Code xong trong `Ranker`; đang chọn ngưỡng trên ViSP val. Thử tay: chặn được "Không nên mua sữa" (0,02) nhưng KHÔNG chặn được đảo vai "em gửi chị" -> "chị gửi em" (0,98) |
| 8 | Diễn đạt lại theo văn phong tin nhắn (dữ liệu sinh bằng LLM hoặc LLM nhỏ dùng prompt) | 💤 | tốn công nhất; đưa vào "hướng phát triển" |
| 9 | Hậu xử lý ký tự bị tokenizer chuẩn hóa ("…" -> "...", số lượng ")" trong "=))") | ✅ | `restore_symbols`; ViLexNorm v1: EM 69,1% -> 69,8%, WER 3,96% -> 3,72% |
| 10 | Huấn luyện thêm epoch cho mô hình diễn đạt lại (val loss còn giảm ở epoch 2) | 💤 | |
| 11 | Quy tắc phủ định chặn nhầm phủ định kép ("Đừng quên" ⇔ "Nhớ") | 💤 | phát hiện khi viết test NLI; có thể bỏ quy tắc khi NLI đã bật |
| 12 | Phát hiện đảo vai (ai làm gì cho ai) trong gợi ý | 💤 | cả embedding lẫn NLI đều bỏ sót; cần quy tắc theo đại từ hoặc mô hình khác |

## Kết quả vòng 1 (26/10/2026)

Stress test (400 câu ViLexNorm test × 8 kiểu lỗi, `outputs/metrics/stress_comparison.md`), ô = WER sau sửa / câu đúng hết:

| Kiểu lỗi | WER đầu vào | v1 | v2 (aug) | bmd1905 có sẵn |
|---|---|---|---|---|
| Câu đã đúng | 0,0% | 1,2% / 90,0% | 1,3% / 88,8% | 19,4% / 6,8% |
| Không dấu cả câu | 74,3% | 15,2% / 23,8% | 9,6% / 46,5% | 88,3% / 0,0% |
| Đảo chữ | 13,2% | 7,7% / 34,8% | 6,3% / 71,0% | 24,5% / 1,2% |
| Bấm hụt | 12,8% | 9,7% / 22,2% | 6,0% / 45,2% | 23,8% / 2,0% |
| Phím bên cạnh | 12,6% | 8,7% / 30,0% | 4,3% / 62,0% | 23,1% / 3,0% |
| Phím đúp | 13,1% | 3,7% / 68,8% | 1,9% / 82,2% | 21,5% / 4,2% |
| Sai dấu | 12,4% | 9,1% / 24,8% | 4,1% / 63,7% | 25,5% / 1,0% |
| Gõ nhanh (không dấu + lỗi gõ) | 76,4% | 24,1% / 6,5% | 14,7% / 26,8% | 90,1% / 0,0% |

Tập test thật (WER / câu đúng hết / sửa quá tay), v1 đo lại sau khi thêm `restore_symbols`:

| | ViLexNorm | VSEC | VEC |
|---|---|---|---|
| v1 | 3,72% / 69,8% / 10,9% | 1,24% / 67,7% / 4,4% | 8,84% / 51,4% / 7,3% |
| v2 (aug) | 5,00% / 66,5% / 12,3% | 1,22% / 68,8% / 4,7% | 8,19% / 51,3% / 9,6% |
| bmd1905 | 31,0% / 0,3% / 93,9% | 3,87% / 13,2% / 19,6% | 40,9% / 5,4% / 53,7% |

Nhận xét:
- Dữ liệu lỗi nhân tạo giúp rất rõ với lỗi gõ (câu "gõ nhanh" đúng hết 6,5% -> 26,8%) nhưng làm v2
  "sửa hăng" trên ViLexNorm thật: sai 88 câu v1 đúng, cứu 53 câu v1 sai (hường -> hưởng, song tử ->
  sống tử, tết -> Tết). Lý do: lỗi nhân tạo kiểu từ-đúng -> từ-đúng-khác dạy mô hình nghi ngờ cả từ đúng.
- Mô hình có sẵn bmd1905 (học trên văn bản tin tức) không chuyển sang miền tin nhắn: gần như không
  thêm dấu cho câu viết thường không dấu, và thêm dấu câu/viết hoa vào 94% câu đúng của ViLexNorm.
- Hướng xử lý đang thử: fine-tune giai đoạn 2 chỉ trên dữ liệu thật (`configs/correction_stage2.yaml`,
  1 epoch, lr 1e-4) -> `vit5-base-aug-ft`.
