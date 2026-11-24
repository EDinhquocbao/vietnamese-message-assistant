"""Điền nội dung đồ án vào mẫu slide của giảng viên -> reports/Slide_do_an_Dinh_Quoc_Bao.pptx

Chạy từ thư mục gốc repo (python-pptx không có trong .venv):
    uv run --no-project --with python-pptx python reports/build_slides.py
Giữ màu và phông của mẫu (Cambria/Calibri). Phần lớn trang chỉ thay chữ, bảng, biểu đồ và chèn hình; 3 trang thẻ cột được
dựng lại dạng dòng và có thêm 4 trang có hình (xem reports/slide_layouts.py) để bố cục không lặp lại.
"""
import copy
import re
import struct
import sys
import unicodedata
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches

import slide_layouts as L

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "Slide_do_an_Dinh_Quoc_Bao.pptx"
TITLE = "Hệ thống sửa lỗi chính tả và gợi ý diễn đạt cho tin nhắn tiếng Việt"
NAME = "Đinh Quốc Bảo"


def template() -> Path:
    for p in ROOT.glob("*.pptx"):
        if unicodedata.normalize("NFC", p.name).startswith("Mau_Slide"):
            return p
    sys.exit("Không thấy mẫu slide Mau_Slide_*.pptx")


def _runs(line: str):
    """'**đậm** thường' -> [(chữ, đậm?)]"""
    out = []
    for part in re.split(r"(\*\*.+?\*\*)", line):
        if part:
            out.append((part[2:-2], True) if part.startswith("**") else (part, None))
    return out


def set_lines(tf, lines: list[str]) -> None:
    """Thay chữ trong khung, giữ định dạng đoạn và chữ của mẫu (đoạn thứ i lấy định dạng đoạn thứ i của mẫu)."""
    protos = [p._p for p in tf.paragraphs]
    body = protos[0].getparent()
    for p in protos:
        body.remove(p)
    for i, line in enumerate(lines):
        newp = copy.deepcopy(protos[min(i, len(protos) - 1)])
        runs = newp.findall(qn("a:r"))
        base = copy.deepcopy(runs[0].find(qn("a:rPr"))) if runs and runs[0].find(qn("a:rPr")) is not None else None
        for child in list(newp):
            if child.tag in (qn("a:r"), qn("a:br"), qn("a:fld")):
                newp.remove(child)
        # mẫu (sinh bằng pptxgenjs) có <a:pPr> thừa giữa các run; bỏ đi, nếu không hai pPr nằm cạnh nhau làm hỏng file
        for extra in newp.findall(qn("a:pPr"))[1:]:
            newp.remove(extra)
        end = newp.find(qn("a:endParaRPr"))
        marked = "**" in line
        for text, bold in _runs(line):
            r = etree.Element(qn("a:r"))
            rpr = copy.deepcopy(base) if base is not None else etree.Element(qn("a:rPr"))
            if marked:                      # dòng có **nhãn**: chỉ nhãn đậm, phần còn lại thường
                rpr.set("b", "1" if bold else "0")
            r.append(rpr)
            t = etree.SubElement(r, qn("a:t"))
            t.text = text
            if end is not None:
                end.addprevious(r)
            else:
                newp.append(r)
        body.append(newp)


def shape(slide, name: str):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    sys.exit(f"Không thấy hình '{name}' trên slide")


def text(slide, name: str, *lines: str) -> None:
    set_lines(shape(slide, name).text_frame, list(lines))


def remove(slide, *names: str) -> None:
    for n in names:
        el = shape(slide, n)._element
        el.getparent().remove(el)


def picture(slide, frame_name: str, path: str, remove_names=(), keep_frame=False) -> None:
    fr = shape(slide, frame_name)
    data = (ROOT / path).read_bytes()
    w, h = struct.unpack(">II", data[16:24])
    pad = Inches(0.1)
    bw, bh = fr.width - 2 * pad, fr.height - 2 * pad
    scale = min(bw / w, bh / h)
    pw, ph = int(w * scale), int(h * scale)
    left = fr.left + (fr.width - pw) // 2
    top = fr.top + (fr.height - ph) // 2
    remove(slide, *remove_names)
    if not keep_frame:
        remove(slide, frame_name)
    slide.shapes.add_picture(str(ROOT / path), Emu(left), Emu(top), Emu(pw), Emu(ph))


def section_subtitle(slide, line: str) -> None:
    """Slide mở chương: các ô đều tên 'Text 0' nên chọn theo thứ tự (số, tên chương, mô tả)."""
    shs = [sh for sh in slide.shapes if sh.has_text_frame and "Slide Number" not in sh.name]
    set_lines(shs[2].text_frame, [line])


def table(slide, name: str, rows: list[list[str]]) -> None:
    t = shape(slide, name).table
    if len(rows) != len(t.rows) or any(len(r) != len(t.columns) for r in rows):
        sys.exit(f"Bảng '{name}': mẫu có {len(t.rows)}x{len(t.columns)} ô")
    for r, row in zip(t.rows, rows):
        for c, val in zip(r.cells, row):
            set_lines(c.text_frame, [val])


def build() -> None:
    prs = Presentation(str(template()))
    icons = L.load_icons(Presentation(str(template())))
    s = list(prs.slides)

    # chân trang của layout nội dung
    for layout in prs.slide_layouts:
        for sh in layout.shapes:
            if sh.has_text_frame and "[Tên đề tài]" in sh.text_frame.text:
                set_lines(sh.text_frame, [f"Xử lý ngôn ngữ tự nhiên  ·  Sửa lỗi và gợi ý diễn đạt tin nhắn tiếng Việt  ·  {NAME}"])

    # 1. Bìa
    sl = s[0]
    shs = [sh for sh in sl.shapes if sh.has_text_frame]
    set_lines(shs[0].text_frame, ["TRƯỜNG ĐẠI HỌC TƯ THỤC QUỐC TẾ SÀI GÒN", "KHOA KỸ THUẬT & KHOA HỌC MÁY TÍNH"])
    set_lines(shs[1].text_frame, [TITLE.upper()])
    set_lines(shs[2].text_frame, ["Đồ án môn học: Xử lý ngôn ngữ tự nhiên  |  Lớp: 24DAI"])
    set_lines(shs[3].text_frame, ["**Giảng viên hướng dẫn:** Th.S Trần Hàm Dương",
                                  f"**Sinh viên thực hiện:** {NAME} – MSSV: 34802403236",
                                  "Tp. Hồ Chí Minh, tháng 11 năm 2026"])

    # 2. Nội dung trình bày
    sl = s[1]
    for title, desc, (nt, nd) in [
        ("Giới thiệu bài toán", "Lý do, phát biểu bài toán, mục tiêu và phạm vi", ("Text 3", "Text 4")),
        ("Cơ sở lý thuyết", "Kênh nhiễu, Transformer, ViT5 và công cụ", ("Text 7", "Text 8")),
        ("Dữ liệu & phương pháp", "4 bộ dữ liệu, luồng xử lý, kiến trúc hệ thống", ("Text 11", "Text 12")),
        ("Thực nghiệm & kết quả", "So sánh mô hình, chấm thủ công, demo", ("Text 15", "Text 16")),
        ("Kết luận", "Kết quả, hạn chế, hướng phát triển", ("Text 19", "Text 20"))]:
        text(sl, nt, title)
        text(sl, nd, desc)

    # 4. Lý do chọn đề tài
    sl = s[3]
    text(sl, "Text 3", "Tin nhắn tiếng Việt thường gõ nhanh: bỏ dấu, viết tắt (ko, dc, mn), gõ Telex dở (nguowif), bấm nhầm phím.")
    text(sl, "Text 6", "Bỏ dấu gây mơ hồ: “con yeu qua” = con yêu quá / còn yêu quá; viết tắt nhiều nghĩa; sửa nhầm làm đổi ý người viết.")
    text(sl, "Text 9", "Tin nhắn rõ ràng, đúng chính tả; chạy hoàn toàn trên máy cá nhân nên giữ riêng tư.")
    text(sl, "Text 13", "Tin nhắn có lỗi, ví dụ: “mai e nghi hoc nha c”")
    text(sl, "Text 15", "Câu đã sửa (tối đa 3 phương án) + 1 câu diễn đạt lại; gợi ý cả câu ngay khi gõ")
    text(sl, "Text 16", "Loại bài toán: sinh văn bản seq2seq (sửa lỗi chính tả, chuẩn hóa, diễn đạt lại)")

    # 5. Mục tiêu và phạm vi: 3 hàng ngang thay cho 3 thẻ cột
    L.goals(s[4], icons)

    # 6. Section 02
    section_subtitle(s[5], "Kênh nhiễu, Transformer, ViT5 và công cụ sử dụng")

    # 7. Kỹ thuật và công cụ: danh sách dòng có icon, chia 2 cột
    L.tools(s[6], icons)

    # 8. Section 03
    section_subtitle(s[7], "4 bộ dữ liệu, luồng xử lý và kiến trúc hệ thống")

    # 9. Bộ dữ liệu
    sl = s[8]
    text(sl, "Text 2", "65.297")
    text(sl, "Text 3", "cặp câu thật để train sửa lỗi")
    text(sl, "Text 5", "89.190")
    text(sl, "Text 6", "câu lỗi nhân tạo (chỉ train)")
    text(sl, "Text 8", "91.566")
    text(sl, "Text 9", "cặp câu diễn đạt lại (ViSP)")
    text(sl, "Text 10", "Ví dụ mẫu dữ liệu")
    table(sl, "Bảng mẫu dữ liệu", [["Đầu vào có lỗi", "Câu chuẩn"],
                                   ["Mk cũng k ăn dk thịt mỡ (ViLexNorm)", "Mình cũng không ăn được thịt mỡ"],
                                   ["Kinh tế tuấn hoàn tại Việt Nam. (VSEC)", "Kinh tế tuần hoàn tại Việt Nam."],
                                   ["o qnh sep dang eyu the (nhân tạo)", "ơ anh sếp đáng yêu thế"]])
    text(sl, "Text 11", "**Nguồn:** VSEC, ViLexNorm (test chính), VEC (chỉ train), ViSP (diễn đạt lại)",
         "**Chia dữ liệu:** theo nhóm + bỏ câu trùng; test giữ riêng từng bộ; bỏ 8.665 câu VEC trùng ViLexNorm")

    # 10. Pipeline
    sl = s[9]
    for nt, nd, title, desc in [("Text 4", "Text 5", "Thu thập dữ liệu", "Tải 4 bộ dữ liệu, ghim theo commit"),
                                ("Text 8", "Text 9", "Tiền xử lý", "NFC, chia tập chống rò rỉ, sinh lỗi nhân tạo"),
                                ("Text 12", "Text 13", "Biểu diễn", "Tokenizer ViT5; từ điển + bigram"),
                                ("Text 16", "Text 17", "Huấn luyện", "GĐ1: thật + nhân tạo; GĐ2: chỉ dữ liệu thật"),
                                ("Text 20", "Text 21", "Đánh giá", "3 tập test, stress test, chấm thủ công")]:
        text(sl, nt, title)
        text(sl, nd, desc)

    # 11. Kiến trúc
    sl = s[10]
    text(sl, "Text 3", "Thành phần chính")
    text(sl, "Text 6", "Gợi ý khi gõ")
    text(sl, "Text 7", "Từ điển đề xuất (< 1 ms), ViT5 chọn khi dừng tay")
    text(sl, "Text 10", "Sửa lỗi khi gửi")
    text(sl, "Text 11", "ViT5 sinh N-best, tối đa 3 câu đã sửa")
    text(sl, "Text 14", "Diễn đạt lại")
    text(sl, "Text 15", "8 ứng viên; lọc số/tên/phủ định, NLI; xếp hạng MMR")
    picture(sl, "Khung sơ đồ", "reports/figures/04_kien_truc_he_thong.png", remove_names=("Biểu tượng sơ đồ", "Text 2"))

    # 12. Section 04
    section_subtitle(s[11], "Thiết lập, so sánh mô hình, chấm thủ công và demo")

    # 13. Thiết lập thực nghiệm
    sl = s[12]
    text(sl, "Text 1", "Siêu tham số (mô hình sửa lỗi)")
    table(sl, "Bảng siêu tham số", [["Tham số", "Giá trị"], ["Mô hình", "ViT5-base (226M)"],
                                    ["Batch size", "16 × tích lũy 2"], ["Số epoch", "GĐ1: 2, GĐ2: 1 (lr 1e-4)"],
                                    ["Độ dài tối đa", "128 token"], ["Optimizer", "Adafactor, bf16"]])
    text(sl, "Text 4", "Các hệ thống so sánh")
    text(sl, "Text 5", "Mốc: chép nguyên đầu vào", "Mô hình có sẵn (BARTpho)", "ViT5: v1, v2, v2 + GĐ2",
         "Kết hợp từ điển: lá chắn, chọn lại")
    text(sl, "Text 6", "**Phần cứng:** RTX 3050 6 GB; huấn luyện sửa lỗi 77 + 100 + 19 phút, diễn đạt lại 48 phút")

    # 14. Kết quả so sánh
    sl = s[13]
    table(sl, "Bảng kết quả", [["Hệ thống", "WER tin nhắn", "Câu đúng", "WER VSEC", "Sửa quá tay"],
                               ["Chép đầu vào", "16,9", "0,0", "3,81", "0,0"],
                               ["BARTpho có sẵn", "31,0", "0,3", "3,87", "93,9"],
                               ["ViT5 v1", "3,72", "69,8", "1,24", "10,9"],
                               ["ViT5 v2 + GĐ2", "3,74", "68,4", "1,16", "14,3"]])
    text(sl, "Text 2", "**Nhận xét:** WER tin nhắn 16,9% → 3,74%; gõ nhanh 6,5% → 26,5%. Diễn đạt lại: máy chấm đạt 87% "
                       "nhưng người chỉ 34% → không tin được chỉ số tự động.")
    chart = [sh for sh in sl.shapes if sh.has_chart][0].chart
    data = CategoryChartData()
    data.categories = ["Chép đầu vào", "BARTpho", "ViT5 v1", "ViT5 v2 + GĐ2"]
    data.add_series("Câu đúng (%)", (0.0, 0.0, 6.5, 26.5), number_format="0.0")
    chart.replace_data(data)
    # mẫu cài nhãn của chuỗi dạng số nguyên (#,##0): 6,5 bị hiện thành 7
    for fmt in chart._chartSpace.xpath(".//c:ser/c:dLbls/c:numFmt"):
        fmt.set("formatCode", "0.0")
    set_lines(chart.chart_title.text_frame, ["Stress test “gõ nhanh”: câu sửa đúng hết (%)"])

    # 15. Demo và phân tích lỗi
    sl = s[14]
    picture(sl, "Khung ảnh demo", "reports/figures/demo_tin_nhan_sau_khi_gui.png", remove_names=("Biểu tượng ảnh", "Text 2"))
    text(sl, "Text 3", "Hình 1. Demo chế độ tin nhắn (HTML/JS + WebSocket); có thêm chế độ văn bản như Word")
    text(sl, "Text 4", "Một số trường hợp sửa sai")
    text(sl, "Text 6", "“Việc c cần làm không phải là thay đổi bản thân…”")
    text(sl, "Text 7", "**Nhãn đúng:** cậu   **Dự đoán:** chị")
    text(sl, "Text 8", "**Nguyên nhân:** viết tắt một chữ cái có nhiều nghĩa")
    text(sl, "Text 10", "“Kinh tế tuấn hoàn tại Việt Nam.”")
    text(sl, "Text 11", "**Nhãn đúng:** tuần hoàn   **Dự đoán:** kiệt quệ")
    text(sl, "Text 12", "**Nguyên nhân:** sửa thành từ có thật, đổi nghĩa")

    # 16. Section 05 giữ nguyên chữ của mẫu; 17. Kết luận: khối đậm bên trái, 2 khối xếp chồng bên phải
    L.conclusion(s[16], icons)

    # 18. Tài liệu tham khảo (trích các tài liệu chính, đầy đủ trong báo cáo)
    text(s[17], "Text 2",
         "[1]  L. Phan, H. Tran, H. Nguyen, and T. H. Trinh, “ViT5: Pretrained text-to-text transformer for Vietnamese language generation,” in Proc. NAACL-HLT 2022: Student Research Workshop, 2022, pp. 136–142.",
         "[2]  T.-N. Nguyen, T.-P. Le, and K. V. Nguyen, “ViLexNorm: A lexical normalization corpus for Vietnamese social media text,” in Proc. EACL 2024, 2024, pp. 1421–1437.",
         "[3]  D.-T. Do, H. T. Nguyen, T. N. Bui, and D. H. Vo, “VSEC: Transformer-based model for Vietnamese spelling correction,” in PRICAI 2021, Springer, 2021, pp. 259–272.",
         "[4]  S. Q. Nguyen and K. V. Nguyen, “A large-scale benchmark for Vietnamese sentence paraphrases,” in Findings of NAACL 2025, 2025, pp. 1045–1060.",
         "[5]  C. Raffel et al., “Exploring the limits of transfer learning with a unified text-to-text transformer,” JMLR, vol. 21, no. 140, pp. 1–67, 2020.",
         "[6]  A. Vaswani et al., “Attention is all you need,” in Proc. NeurIPS, 2017, pp. 5998–6008.")

    # 19. Kết thúc
    shs = [sh for sh in s[18].shapes if sh.has_text_frame]
    set_lines(shs[1].text_frame, [f"Hỏi & Đáp  ·  {NAME}  ·  MSSV 34802403236"])

    # Trang mới có hình, rồi sắp lại thứ tự: không trang nào liền nhau cùng một kiểu bố cục
    typing = L.new_slide(prs, "Gợi ý cả câu ngay khi gõ", s[10])
    L.typing(typing, icons)
    highlights = L.new_slide(prs, "Kết quả nổi bật", s[10])
    L.highlights(highlights, icons)
    evaluation = L.new_slide(prs, "Phát hiện về cách đánh giá", s[10])
    L.evaluation(evaluation, icons)
    docmode = L.new_slide(prs, "Chế độ văn bản: dùng được khi soạn thảo", s[10])
    L.document_mode(docmode, icons)
    L.reorder(prs, s[:11] + [typing, s[11], highlights, s[12], s[13], evaluation, s[14], docmode] + s[15:])

    lock = OUT.with_name("~$" + OUT.name)
    if lock.exists():
        sys.exit(f"File đang mở trong PowerPoint: {OUT.name}. Hãy đóng file rồi chạy lại.")
    prs.save(str(OUT))
    print("Đã ghi", OUT)


if __name__ == "__main__":
    build()
