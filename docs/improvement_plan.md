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
| 1 | Mô hình lỗi "gõ nhanh": bỏ dấu (cả câu/một phần) + đảo chữ, bấm hụt, phím bên cạnh, phím đúp, dính chữ, Telex dở; tăng lên ~90k câu | ✅ | 89.190 câu; `vit5-base-aug` + giai đoạn 2 `vit5-base-aug-ft` (đang dùng trong demo) |
| 2 | Bộ test lỗi tự nhiên do người gõ | 💤 | Thay bằng bộ test sinh tự động theo hồ sơ "gõ nhanh" (mục 3) theo yêu cầu; hạn chế: lỗi nhân tạo có thể dễ hơn lỗi thật |
| 3 | Script đo theo từng kiểu lỗi (stress test) trên câu test held-out | ✅ | `src/correction/stress_test.py`, 400 câu ViLexNorm test × 8 kiểu lỗi, seed 2026 |
| 4 | So sánh với mô hình có sẵn `bmd1905/vietnamese-correction-v2` (BARTpho, Apache-2.0) | ✅ | Đã tải, nạp được (`HubCorrector`); thử nhanh: sửa tốt lỗi gõ nhưng không hiểu teencode (e, r, c, vs) và hay tự thêm dấu câu/viết hoa. Chờ GPU để chạy stress test + 3 tập test |
| 5 | Mô hình mức ký tự ByT5-small | 💤 | chuỗi dài gấp ~3 lần, huấn luyện chậm 2–3 lần trên GPU 6 GB |
| 6 | Đưa 2–3 phương án sửa (N-best) cho từ không chắc chắn trong demo | ✅ | `Corrector.nbest`, `uncertain_words`; demo hiện "Chưa chắc chắn: ngày (hoặc: người yêu)" |
| 7 | Lọc nghĩa gợi ý bằng NLI hai chiều (mDeBERTa-v3 XNLI, MIT) | ✅ | Ngưỡng 0,17 = phân vị 10% trên ViSP val (`calibrate_nli`). Thử tay: chặn được "Không nên mua sữa" (0,02) nhưng KHÔNG chặn được đảo vai "em gửi chị" -> "chị gửi em" (0,98) |
| 8 | Diễn đạt lại theo văn phong tin nhắn (dữ liệu sinh bằng LLM hoặc LLM nhỏ dùng prompt) | 💤 | tốn công nhất; đưa vào "hướng phát triển" |
| 9 | Hậu xử lý ký tự bị tokenizer chuẩn hóa ("…" -> "...", số lượng ")" trong "=))") | ✅ | `restore_symbols`; ViLexNorm v1: EM 69,1% -> 69,8%, WER 3,96% -> 3,72% |
| 10 | Huấn luyện thêm epoch cho mô hình diễn đạt lại (val loss còn giảm ở epoch 2) | ✅ | làm ở #16, không cải thiện |
| 11 | Quy tắc phủ định chặn nhầm phủ định kép ("Đừng quên" ⇔ "Nhớ") | 💤 | phát hiện khi viết test NLI; có thể bỏ quy tắc khi NLI đã bật |
| 12 | Phát hiện đảo vai (ai làm gì cho ai) trong gợi ý | 💤 | cả embedding lẫn NLI đều bỏ sót; cần quy tắc theo đại từ hoặc mô hình khác |
| 13 | Giảm sửa quá tay của v2+GĐ2 (xóa từ lặp hợp lệ, đổi tên riêng); thử giảm tỉ lệ lỗi "phím đúp"/tăng p_clean | 💤 | |
| 14 | **[Ưu tiên 1]** Trả lời RQ3 tự động: diễn đạt lại thẳng câu lỗi vs sửa lỗi rồi mới diễn đạt (dùng đầu vào stress test, so với câu chuẩn bằng similarity/NLI/self-BLEU) | ✅ | `src/pipeline/rq3.py`; sửa trước rồi diễn đạt tốt hơn hẳn, xem "Vòng 4" |
| 15 | **[Ưu tiên 1]** Hình và bảng cho báo cáo: điền 3 notebook trống (độ dài câu, phân bố kiểu lỗi, đường loss các lần train, cột stress test top-1/top-3) + bảng 20 lỗi tiêu biểu có phân loại (viết tắt mơ hồ, sai thành từ có thật, sửa quá tay, lỗi nhãn, mất nội dung) | ✅ | 3 notebook đã chạy; 9 hình `reports/figures/`, bảng `reports/tables/` (20 lỗi: `03_error_examples.md`) |
| 16 | **[Ưu tiên 2]** Huấn luyện thêm 1–2 epoch mô hình diễn đạt lại (#10) rồi đo lại ViSP + tập tích hợp | ✅ | Đã thử +2 epoch: val loss TĂNG 1,09 -> 1,20, giữ mô hình cũ; xem "Vòng 5" |
| 17 | **[Ưu tiên 3]** Đánh giá thủ công: chuẩn bị file + rubric 0/1 (giữ nghĩa, tự nhiên, không thêm/bỏ ý) cho 50–100 gợi ý; NGƯỜI DÙNG chấm (~1 giờ); tính Top-1/Top-3 chấp nhận | ✅ | Người dùng chấm 85 gợi ý: Top-1 35%, Top-3 52,5%; chấm tự động cho đạt 87% -> không tin được, xem "Vòng 6" |
| 18 | Duyệt tập kiểm thử tích hợp (41 câu `status=draft`) hoặc ghi rõ trong báo cáo là chỉ tham khảo | ✅ | Người dùng giữ cả 41 câu -> `status=approved`; kết quả tích hợp không đổi (EM 87,8%) |
| 19 | Viết báo cáo + slide từ mục 14 file plan và các kết quả trên | ⏳ | làm sau cùng |

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

## Kết quả vòng 2: fine-tune giai đoạn 2 (chỉ dữ liệu thật, 1 epoch, lr 1e-4)

| | ViLexNorm (WER / đúng hết / sửa quá tay) | VSEC | VEC | Stress "gõ nhanh" đúng hết |
|---|---|---|---|---|
| v1 | 3,72% / 69,8% / 10,9% | 1,24% / 67,7% / 4,4% | 8,84% / 51,4% / 7,3% | 6,5% |
| v2 | 5,00% / 66,5% / 12,3% | 1,22% / 68,8% / 4,7% | 8,19% / 51,3% / 9,6% | 26,8% |
| **v2 + GĐ2 (chọn)** | 3,74% / 68,4% / 14,3% | 1,16% / 70,1% / 4,1% | 7,69% / 52,6% / 9,1% | 26,5% |

Sửa quá tay tăng trên ViLexNorm: phần lớn là chuẩn hóa khoảng trắng/biến thể chính tả, nhưng có xóa từ lặp
("cấp 2 cấp 3" -> "cấp 3"), có thể do lỗi "phím đúp" trong dữ liệu nhân tạo -> việc để sau (#13).
Hai câu người dùng thử: "tí nữa mìn cùn nahu làm bài nhé" sửa đúng hoàn toàn; "ngy mai khi nà học a" ->
"ngày mai khi này học anh" kèm phương án "nào".


Đã cập nhật mục 14.9–14.13 trong file plan .docx.

## Vòng 3: cho người dùng chọn 1 trong tối đa 3 phương án sửa (demo)

Từ log demo: câu đúng ý người dùng không phải lúc nào cũng là phương án đầu ("nagyf mai…" -> đúng ở #3,
"…đau nhs" -> người dùng chọn #3 "đâu nhé") nhưng có trong danh sách. Demo hiện ô chọn khi mô hình không chắc,
gợi ý diễn đạt tính lại theo câu được chọn. Xác suất hiển thị dùng log-prob cả câu (trung bình theo token cho
27/25/25/24%, vô nghĩa); thứ tự giữ theo beam để phương án đầu = kết quả đã đánh giá.

Đo tự động (`top_options`, đúng các phương án demo hiển thị): câu đúng ở phương án đầu / nằm trong top-3.

| Kiểu lỗi (stress test) | v1 | v2 + GĐ2 (đang dùng) |
|---|---|---|
| Câu đã đúng | 90,0% / 93,0% | 87,0% / 92,5% |
| Không dấu cả câu | 23,8% / 36,8% | 45,8% / 59,5% |
| Đảo chữ | 34,8% / 43,0% | 68,2% / 78,8% |
| Bấm hụt | 22,2% / 27,5% | 42,0% / 50,7% |
| Phím bên cạnh | 30,0% / 40,0% | 58,2% / 68,2% |
| Phím đúp | 68,8% / 75,2% | 80,2% / 89,8% |
| Sai dấu | 24,8% / 33,0% | 58,2% / 69,8% |
| Gõ nhanh | 6,5% / 10,2% | 26,5% / 36,8% |

Tập test thật (phương án đầu / top-3): ViLexNorm v1 69,8% / 76,6%, v2+GĐ2 68,4% / 76,5%;
VSEC v1 67,7% / 76,3%, v2+GĐ2 70,1% / 78,2%; VEC v2+GĐ2 52,6% / 60,4%.

## Đánh giá mức sẵn sàng cho báo cáo (26/10/2026, sau khi gộp mọi thứ vào `main`)

Kết luận: phần kỹ thuật đạt MVP (mục 11 file plan) và có nhiều điểm cộng, nhưng CHƯA sẵn sàng viết báo cáo.

| Tiêu chí MVP | Tình trạng |
|---|---|
| Mô hình sửa lỗi có kết quả test | ✅ 3 tập test thật + stress test 8 kiểu lỗi (top-1/top-3) |
| Mô hình/baseline diễn đạt lại từ ViSP | ✅ |
| Pipeline hai bước chạy trên câu mới | ✅ |
| So sánh baseline, chỉ số phù hợp | ✅ |
| Phân tích 10–20 lỗi tiêu biểu | ⚠️ có ví dụ rải rác, chưa thành bảng có phân loại (#15) |
| Demo | ✅ có chọn 1 trong 3 phương án sửa |
| Báo cáo | ❌ chưa viết (#19); tư liệu ở mục 14.1–14.15 file plan |

Điểm mạnh nên nhấn mạnh trong báo cáo: quy trình chống rò rỉ chặt (test riêng từng dataset, ngưỡng NLI chọn trên
val), các phát hiện thật (BLEU thưởng việc chép câu gốc; VEC chứa 83% ViLexNorm; lỗi nhân tạo giúp lỗi gõ nhưng
gây sửa hăng, giai đoạn 2 khắc phục; mô hình có sẵn không chuyển sang miền tin nhắn), cải tiến xuất phát từ
phân tích lỗi demo.

Thứ tự làm tiếp đã thống nhất với người dùng: #14 + #15 (tự làm được) → #16 (GPU) → #17 (chuẩn bị file, người
dùng chấm) → #18 → #19. Sau #14–#17 là đủ chắc để viết báo cáo.

## Vòng 4: RQ3 — diễn đạt thẳng câu lỗi hay sửa lỗi trước? (27/10/2026)

`python -m src.pipeline.rq3`: 150 câu chuẩn ViLexNorm test, gây lỗi tự động như stress test (seed 2026), 5 kiểu lỗi.
Gợi ý (sau bộ lọc của ranker) được so với **câu chuẩn**: *đạt* = giữ nghĩa (cosine ≥ 0,8 và NLI hai chiều ≥ 0,17)
và không mang từ lạ (từ ngoài từ điển câu chuẩn train). Ô = gợi ý đầu đạt / có ít nhất 1 gợi ý đạt
(`outputs/metrics/rq3.md`).

| Kiểu lỗi | Diễn đạt thẳng câu lỗi | Sửa lỗi rồi diễn đạt (đang dùng) | Diễn đạt câu chuẩn (cận trên) |
|---|---|---|---|
| Câu đã đúng | 78,0% / 78,0% | 75,3% / 75,3% | 80,0% / 80,0% |
| Không dấu cả câu | 1,3% / 2,0% | 53,3% / 56,0% | 80,0% / 80,0% |
| Bấm hụt | 36,0% / 41,3% | 58,0% / 61,3% | 80,0% / 80,0% |
| Sai dấu | 28,0% / 32,7% | 66,0% / 67,3% | 80,0% / 80,0% |
| Gõ nhanh | 1,3% / 1,3% | 38,7% / 46,7% | 80,0% / 80,0% |

Nhận xét:
- Trả lời RQ3: **sửa lỗi trước** tốt hơn hẳn ở mọi kiểu lỗi; với câu không dấu/gõ nhanh, diễn đạt thẳng gần như
  không bao giờ cho gợi ý dùng được (1–2%): mô hình ViSP học trên văn bản chuẩn, gặp câu không dấu thì chép lại lỗi
  ("Duong Mich hin xua…" -> "Dương Mich hin xua trong treo qua.") hoặc bịa nội dung (cosine với câu chuẩn chỉ 0,44).
  Bộ lọc không chặn được vì nó so ứng viên với chính câu lỗi.
- Gợi ý của hệ hai bước hầu như không mang lỗi (sạch 98–100%), phần thua cận trên là do bước sửa lỗi sai
  (đổi nghĩa) — khớp với kết quả stress test.
- Với câu đã đúng, hai bước kém diễn đạt thẳng 2,7 điểm: đó là cái giá của sửa quá tay (#13).
- Cận trên chỉ 80% vì 20% câu không còn gợi ý nào qua bộ lọc (bộ lọc chặt). Với cận trên, tiêu chí "đạt" trùng
  với tiêu chí lọc nên đạt 100% số câu có gợi ý theo định nghĩa: chỉ dùng cột này làm mốc, so sánh thật là hai cột đầu.
- Giới hạn: chấm tự động bằng embedding/NLI, chưa bắt được gợi ý lặp ý ("Tôi không thích mặc đồ hiệu nà và không
  thích mặc đồ hiệu nà." vẫn "đạt") -> cần #17 chấm thủ công.

## Vòng 5: hình/bảng cho báo cáo (#15) và huấn luyện thêm mô hình diễn đạt lại (#16)

**#15.** Ba notebook (`notebooks/01_explore_vsec`, `02_explore_visp`, `03_error_analysis`) đã có nội dung và kết quả;
hình ở `reports/figures/` (độ dài câu, kiểu lỗi từng dataset, kiểu lỗi nhân tạo, ViSP, đường loss, stress test
top-1/top-3, RQ3), bảng ở `reports/tables/`. Phân bố kiểu lỗi (mẫu 8.000 câu/dataset): VSEC chủ yếu thiếu/sai dấu
(~65%), ViLexNorm chủ yếu viết tắt/teencode (~60%), VEC trộn cả hai. Bảng 20 lỗi tiêu biểu của v2+GĐ2
(`reports/tables/03_error_examples.md`, phân loại thủ công):

| Loại lỗi | Số ví dụ | Ví dụ |
|---|---|---|
| Viết tắt mơ hồ | 4 | "m" -> "mày" (đúng: mình), "c" -> "chị" (đúng: cậu) |
| Sửa thành từ có thật nhưng sai | 4 | "xịu" -> "chịu" (xịt), "dzú" -> "vợ" (vú) |
| Sửa quá tay | 4 | "ruby" -> "rực rỡ", "lane" -> "lăn", "quá hời" -> "quá trời" |
| Mất/đổi nội dung | 3 | "tuấn hoàn" -> "kiệt quệ" (tuần hoàn), tên "Mi nơ" -> "Mixi" |
| Bỏ sót lỗi | 2 | "gặt bỏ" (gạt bỏ), "dạy thì" (dậy thì): sai thành từ có thật |
| Lỗi nhãn | 3 | nhãn tự đổi "2005" -> "2006"; nhãn bỏ sót "Hà nội" |

**#16.** Huấn luyện tiếp mô hình diễn đạt lại thêm 2 epoch từ mô hình 2 epoch (`configs/paraphrase_continue.yaml`,
lr 2e-4, 43,7 phút) -> `models/paraphrase/vit5-base-ep4`. Kết quả **không tốt hơn**, giữ mô hình cũ:

| | val loss | BLEU tham chiếu ↑ | self-BLEU ↓ | iBLEU ↑ | cosine với câu gốc | Tích hợp: số gợi ý TB / giữ số-tên-phủ định |
|---|---|---|---|---|---|---|
| 2 epoch (đang dùng) | **1,089** | **75,9** | 74,2 | **45,9** | **0,968** | **2,49** / 96,1% |
| +2 epoch | 1,199 | 73,9 | **68,8** | 45,4 | 0,958 | 2,15 / 96,6% |

Mô hình mới diễn đạt khác câu gốc hơn (self-BLEU thấp hơn) nhưng xa câu người viết hơn và ít gợi ý qua bộ lọc hơn.
Val loss tăng ngay ở lần đo đầu (1,28): khởi động lại lr đẩy mô hình khỏi điểm tốt; train loss giảm mạnh ở epoch 3
(0,7, đã thấy dữ liệu 2 lần) -> học thuộc. Nhận xét "val loss còn giảm" lúc trước là do lr giảm dần về 0 ở cuối lần
huấn luyện đầu, không phải do còn chỗ để học.

## Vòng 6: chuẩn bị đánh giá thủ công (#17) và duyệt tập kiểm thử (#18)

`python -m src.pipeline.manual_eval prepare` chạy hệ thống trên 120 tin nhắn thật ngẫu nhiên của ViLexNorm test
(5–30 từ, seed 2026): 86/120 (72%) có ít nhất 1 gợi ý (còn lại bị chặn do còn từ lạ hoặc không ứng viên nào qua bộ
lọc). Lấy 40 tin nhắn có gợi ý -> 85 gợi ý cần chấm; bước sửa lỗi đúng hoàn toàn 31/40 câu. Gợi ý được chấm so với
**câu chuẩn của người gán nhãn** (ý người viết), nên đo chất lượng đầu-cuối của cả hai bước.
Rubric 0/1: đạt cả ba (đúng ý, tự nhiên, không thêm/bỏ ý); nếu 0 chọn lý do (đổi nghĩa, thêm/bỏ ý, đảo vai,
không tự nhiên, còn lỗi, khác). `score` tính Top-1 (gợi ý đầu đạt), Top-3 (có ít nhất 1 gợi ý đạt), tỉ lệ đạt từng
gợi ý và phân bố lý do -> `outputs/metrics/manual_eval.json`; đồng thời áp quyết định duyệt vào
`data/test/integration_test.csv` (Giữ/Sửa -> approved, Bỏ -> xóa). Sau đó chạy lại
`python -m src.pipeline.evaluate_integration` (không cần `--include_draft`).

### Kết quả chấm thủ công (27/10/2026)

Người dùng chấm đủ 85 gợi ý của 40 tin nhắn (`python -m src.pipeline.manual_eval score` -> `outputs/metrics/manual_eval.json`).
Lý do được ghi tự do; Claude gom thành nhóm trong `reports/manual_eval/ly_do_phan_loai.csv` (giữ nguyên câu gốc).

| | Số tin nhắn | Top-1 (gợi ý đầu đạt) | Top-3 (≥1 gợi ý đạt) | Tỉ lệ đạt mỗi gợi ý |
|---|---|---|---|---|
| Tất cả | 40 | **35,0%** | **52,5%** | 34,1% |
| Bước sửa lỗi đúng hoàn toàn | 31 | 38,7% | 61,3% | 40,9% |
| Bước sửa lỗi sai | 9 | 22,2% | 22,2% | 10,5% |

Tỉ lệ đạt theo vị trí gợi ý: #1 35%, #2 25%, #3 47% -> thứ tự xếp hạng không phản ánh chất lượng.

| Lý do bị chấm 0 (56 gợi ý) | Số |
|---|---|
| Lạc ý/không liên quan | 23 |
| Vô nghĩa, lủng củng, sai ngữ pháp | 19 |
| Đổi chủ ngữ/đối tượng (đảo vai) | 5 |
| Đổi kiểu câu/sắc thái (thành câu hỏi, thêm "!", mất từ cảm xúc) | 4 |
| Thêm hoặc bỏ ý | 4 |
| Sai từ do bước sửa lỗi | 1 |

**So với chấm tự động trên đúng 85 gợi ý này** (cosine ≥ 0,8 và NLI ≥ 0,17 so với câu chuẩn, như RQ3;
`outputs/metrics/manual_vs_auto.json`): tự động cho đạt 87,1%, người chỉ 34,1%; hai bên khớp 44,7%; trong số gợi ý
tự động cho đạt, người chỉ chấp nhận 37,8%. Tương quan Spearman với điểm người: cosine 0,27, NLI 0,14.

Nhận xét:
- Đây là kết quả quan trọng nhất cho báo cáo: **chỉ số tự động (embedding, NLI) đánh giá quá cao diễn đạt lại gấp
  khoảng 2,5 lần** trên tin nhắn MXH; các con số RQ3 (#14) chỉ dùng để so sánh tương đối giữa hai cách, không phải
  chất lượng tuyệt đối. Kết luận RQ3 vẫn đứng vững (hướng giống: sửa sai -> gợi ý đạt 22% so với 39% khi sửa đúng).
- Mô hình diễn đạt lại học trên ViSP (văn bản tin tức/chuẩn, câu dài trung vị 28 từ) không hợp với tin nhắn ngắn,
  văn nói, nhiều tiếng lóng: lỗi chính là lạc ý và câu vô nghĩa, không phải lỗi nhỏ. Hướng cải thiện đúng là #8
  (dữ liệu diễn đạt lại kiểu tin nhắn) chứ không phải huấn luyện thêm (#16 đã cho thấy không giúp).
- Bộ lọc NLI/embedding gần như không lọc được các lỗi này -> cân nhắc cho phép demo không đưa gợi ý khi không chắc,
  hoặc ưu tiên gợi ý gần câu gốc hơn.
- Người chấm nhận xét thêm: khi 3 gợi ý cùng nghĩa thì đưa 3 câu là thừa (M31).
- Giới hạn: một người chấm, 40 tin nhắn; không có độ đồng thuận giữa người chấm.
