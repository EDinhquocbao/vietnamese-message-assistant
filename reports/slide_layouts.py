"""Các bố cục bổ sung cho slide, để không trang nào cũng là thẻ xếp cột (góp ý của giảng viên qua người dùng).

Dựng bằng hình khối của python-pptx; màu dùng màu chủ đề của mẫu (xanh đậm tx2, xanh ngọc accent1, cam accent2, nền bg2),
phông theo chủ đề (Cambria cho số lớn, Calibri cho chữ), icon lấy lại từ chính các slide mẫu.
"""
import io
import re
import struct
from pathlib import Path

from pptx.enum.dml import MSO_THEME_COLOR as T
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
DARK, TEAL, ORANGE, RED, GRAY, LIGHT, WHITE, INK = (T.TEXT_2, T.ACCENT_1, T.ACCENT_2, T.ACCENT_4, T.ACCENT_5,
                                                     T.BACKGROUND_2, T.BACKGROUND_1, T.TEXT_1)

# icon trắng trong mẫu: (slide, tên hình)
ICONS = {
    "globe": (3, "Bối cảnh icon"), "warning": (3, "Thách thức icon"), "bulb": (3, "Ý nghĩa icon"),
    "target": (4, "Mục tiêu icon"), "crosshair": (4, "Phạm vi icon"), "flask": (4, "Phương pháp icon"),
    "scissors": (6, "Tiền xử lý văn bản icon"), "frame": (6, "Biểu diễn văn bản icon"), "brain": (6, "Mô hình icon"),
    "code": (6, "Thư viện icon"), "ruler": (6, "Độ đo đánh giá icon"), "server": (6, "Môi trường icon"),
    "database": (9, "Thu thập dữ liệu icon"), "gears": (9, "Huấn luyện icon"), "chart": (9, "Đánh giá icon"),
    "scale": (12, "Mô hình so sánh icon"), "chat": (13, "Nhận xét icon"),
    "check": (16, "Đạt được icon"), "minus": (16, "Hạn chế icon"), "rocket": (16, "Hướng phát triển icon"),
}


def load_icons(tpl) -> dict[str, bytes]:
    out = {}
    for key, (si, name) in ICONS.items():
        sh = next(s for s in tpl.slides[si].shapes if s.name == name)
        out[key] = sh.image.blob
    return out


# ============================================================== khối cơ bản
def _segments(line: str):
    for part in re.split(r"(\*\*.+?\*\*)", line):
        if part:
            yield (part[2:-2], True) if part.startswith("**") else (part, False)


def box(slide, x, y, w, h, fill=LIGHT, kind=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05, line=None):
    sh = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    style = sh._element.find(qn("p:style"))      # bỏ kiểu mặc định (viền, bóng) để hình phẳng như mẫu
    if style is not None:
        sh._element.remove(style)
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.theme_color = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.theme_color = line
        sh.line.width = Pt(1.25)
    return sh


def write(slide, x, y, w, h, lines, size=15, color=INK, bold=False, italic=False, align=PP_ALIGN.LEFT,
          anchor=MSO_ANCHOR.TOP, heading=False, space=6):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, line in enumerate([lines] if isinstance(lines, str) else lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space)
        for text, b in _segments(line):
            r = p.add_run()
            r.text = text
            f = r.font
            f.size, f.bold, f.italic = Pt(size), bold or b, italic
            f.color.theme_color = color
            if heading:
                f.name = "+mj-lt"
    return tb


def icon(slide, icons, name, x, y, d=0.75, fill=TEAL):
    box(slide, x, y, d, d, fill=fill, kind=MSO_SHAPE.OVAL)
    slide.shapes.add_picture(io.BytesIO(icons[name]), Inches(x + d * 0.25), Inches(y + d * 0.25), Inches(d * 0.5),
                             Inches(d * 0.5))


def badge(slide, n, x, y, d=0.5, fill=ORANGE):
    sh = box(slide, x, y, d, d, fill=fill, kind=MSO_SHAPE.OVAL)
    tf = sh.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(n)
    r.font.size, r.font.bold = Pt(16), True
    r.font.color.theme_color = WHITE


def framed_picture(slide, path, x, y, w, h, pad=0.14):
    box(slide, x, y, w, h, fill=LIGHT, radius=0.03)
    data = (ROOT / path).read_bytes()
    pw, ph = struct.unpack(">II", data[16:24])
    scale = min((w - 2 * pad) / pw, (h - 2 * pad) / ph)
    iw, ih = pw * scale, ph * scale
    slide.shapes.add_picture(str(ROOT / path), Inches(x + (w - iw) / 2), Inches(y + (h - ih) / 2), Inches(iw), Inches(ih))


def clear(slide):
    """Bỏ mọi hình trừ placeholder (tiêu đề, số trang) để dựng lại bố cục."""
    for sh in list(slide.shapes):
        if not sh.is_placeholder:
            sh._element.getparent().remove(sh._element)


def row(slide, icons, x, y, w, name, fill, title, desc, d=0.7, title_size=18, desc_size=14):
    """Một dòng: icon tròn bên trái, tiêu đề đậm và mô tả bên phải."""
    icon(slide, icons, name, x, y, d, fill)
    write(slide, x + d + 0.25, y - 0.02, w - d - 0.25, 0.4, title, title_size, DARK, bold=True)
    write(slide, x + d + 0.25, y + 0.42, w - d - 0.25, 0.9, desc, desc_size, INK)


# ============================================================== các trang làm lại
def goals(slide, icons):
    clear(slide)
    items = [("target", TEAL, "Mục tiêu",
              "Sửa lỗi tin nhắn tiếng Việt, so với mốc chép đầu vào và mô hình có sẵn; gợi ý cả câu ngay khi gõ "
              "(dưới 500 ms); diễn đạt lại giữ nghĩa, đánh giá cả tự động lẫn thủ công."),
             ("crosshair", ORANGE, "Phạm vi",
              "Tin nhắn tiếng Việt ngắn, ngữ cảnh trong một tin; chạy cục bộ trên GPU 6 GB. "
              "Không làm: hội thoại nhiều lượt, huấn luyện mô hình từ đầu."),
             ("flask", TEAL, "Phương pháp",
              "Tinh chỉnh ViT5 với lỗi nhân tạo và huấn luyện 2 giai đoạn; từ điển đề xuất, mô hình chọn; "
              "chia tập chống rò rỉ, điều kiện giữ đặt trước khi chạy test.")]
    for i, (name, fill, title, desc) in enumerate(items):
        y = 1.6 + i * 1.62
        box(slide, 0.6, y, 12.13, 1.42)
        icon(slide, icons, name, 0.95, y + 0.31, 0.8, fill)
        write(slide, 2.05, y, 2.3, 1.42, title, 22, DARK, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        write(slide, 4.3, y + 0.1, 8.1, 1.22, desc, 16, INK, anchor=MSO_ANCHOR.MIDDLE)


def tools(slide, icons):
    clear(slide)
    cols = [[("scissors", TEAL, "Tiền xử lý văn bản", "NFC, giữ chữ hoa và dấu; chia tập theo nhóm, bỏ câu trùng giữa các tập"),
             ("frame", ORANGE, "Biểu diễn văn bản", "Tokenizer SentencePiece của ViT5; nhúng câu MiniLM đa ngôn ngữ"),
             ("brain", TEAL, "Mô hình", "ViT5-base (226M) sửa lỗi và diễn đạt; NLI mDeBERTa-v3; từ điển + bigram")],
            [("code", TEAL, "Thư viện", "Python 3.14, PyTorch 2.14, Transformers 5.20, sentence-transformers, websockets"),
             ("ruler", ORANGE, "Độ đo đánh giá", "CER, WER, câu đúng hết, P/R/F0.5, sửa quá tay; BLEU, iBLEU; chấm thủ công"),
             ("server", TEAL, "Môi trường", "Laptop RTX 3050 6 GB, Core i5-12450HX, RAM 16 GB, Windows 11")]]
    for c, items in enumerate(cols):
        x = 0.6 + c * 6.35
        for i, (name, fill, title, desc) in enumerate(items):
            row(slide, icons, x, 1.75 + i * 1.6, 5.8, name, fill, title, desc)


def conclusion(slide, icons):
    clear(slide)
    box(slide, 0.6, 1.6, 5.7, 4.85, fill=DARK, radius=0.03)
    icon(slide, icons, "check", 1.0, 2.0, 0.75, TEAL)
    write(slide, 1.95, 2.05, 4.0, 0.6, "Đạt được", 24, WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    write(slide, 1.0, 3.05, 4.95, 3.2, ["**3,74%** WER trên tin nhắn thật (mốc 16,9%), 68,4% câu đúng hết",
                                        "**96,6%** từ sai có đáp án trong 3 gợi ý khi gõ, dưới 150 ms",
                                        "**2 chế độ** tin nhắn và văn bản, chạy hoàn toàn trên máy"], 16, WHITE, space=14)
    for i, (name, fill, title, lines) in enumerate([
            ("minus", RED, "Hạn chế", ["Diễn đạt lại: chỉ 35% gợi ý đầu đạt theo người chấm",
                                       "Câu bỏ hết dấu cần khoảng 8 lần chạm",
                                       "Một người chấm; dữ liệu MXH chưa giống tin nhắn riêng"]),
            ("rocket", ORANGE, "Hướng phát triển", ["Dữ liệu diễn đạt lại theo văn phong tin nhắn",
                                                     "Gợi ý theo từng ký tự, học thói quen người dùng",
                                                     "Mô hình nhẹ hơn, đóng gói thành bàn phím"])]):
        y = 1.6 + i * 2.5
        box(slide, 6.6, y, 6.13, 2.35)
        icon(slide, icons, name, 6.9, y + 0.3, 0.65, fill)
        write(slide, 7.8, y + 0.33, 4.7, 0.5, title, 20, DARK, bold=True)
        write(slide, 7.8, y + 0.88, 4.75, 1.4, lines, 14, INK, space=4)


# ============================================================== trang mới
def typing(slide, icons):
    framed_picture(slide, "reports/figures/demo_tin_nhan_dang_go.png", 0.6, 1.75, 6.7, 3.45)
    write(slide, 0.6, 5.35, 6.7, 0.6, "Ảnh chụp demo: gõ “con yeu qua nguowif hok” → “nguowif” tự đổi thành “người”, "
                                      "danh sách đưa 3 câu hoàn chỉnh", 12, GRAY, italic=True)
    steps = [("Gõ xong một từ", "Từ điển đề xuất ứng viên, xếp bằng bigram: dưới 1 ms"),
             ("Dừng tay 350 ms", "ViT5 chấm lại cả câu: khoảng 60–120 ms"),
             ("Chọn cả câu", "Tối đa 3 câu hoàn chỉnh, từ khác được in đậm"),
             ("Gõ . ! ? hoặc xuống dòng", "Chuyển sang câu mới; bấm vào câu cũ để sửa lại")]
    for i, (title, desc) in enumerate(steps):
        y = 1.75 + i * 1.12
        badge(slide, i + 1, 7.75, y, 0.5, ORANGE if i % 2 == 0 else TEAL)
        write(slide, 8.5, y - 0.02, 4.2, 0.4, title, 17, DARK, bold=True)
        write(slide, 8.5, y + 0.38, 4.2, 0.6, desc, 14, INK)


def highlights(slide, icons):
    stats = [("3,74%", "WER trên tin nhắn thật (mốc chép đầu vào: 16,9%)"),
             ("26,5%", "câu “gõ nhanh” sửa đúng hết (bản đầu chỉ 6,5%)"),
             ("96,6%", "từ sai có đáp án nằm trong 3 gợi ý khi gõ"),
             ("< 150 ms", "độ trễ chấm lại bằng ViT5 khi dừng tay")]
    for i, (num, label) in enumerate(stats):
        x = 0.6 + i * 3.08
        box(slide, x, 1.7, 2.9, 2.55)
        write(slide, x + 0.28, 1.95, 2.4, 0.95, num, 40, ORANGE if i % 2 == 0 else TEAL, bold=True, heading=True)
        write(slide, x + 0.28, 3.0, 2.4, 1.1, label, 14, GRAY)
    box(slide, 0.6, 4.6, 12.13, 1.75, fill=DARK, radius=0.04)
    icon(slide, icons, "chat", 0.95, 5.08, 0.8, ORANGE)
    write(slide, 2.05, 4.75, 10.3, 1.45,
          "**Điểm mấu chốt:** tinh chỉnh ViT5 kèm lỗi nhân tạo và huấn luyện 2 giai đoạn giúp sửa tốt tin nhắn thật mà "
          "vẫn xử lý được lỗi gõ nhanh. Phần còn yếu là diễn đạt lại: chỉ 35% gợi ý đầu được người chấm chấp nhận.",
          17, WHITE, anchor=MSO_ANCHOR.MIDDLE)


def evaluation(slide, icons):
    write(slide, 0.6, 1.7, 5.9, 0.5, "Chấm 85 gợi ý diễn đạt lại của 40 tin nhắn thật", 18, DARK, bold=True)
    for i, (label, pct, fill) in enumerate([("Máy chấm (cosine + NLI)", 0.871, GRAY), ("Người chấm", 0.341, ORANGE)]):
        y = 2.45 + i * 1.25
        write(slide, 0.6, y, 5.6, 0.35, label, 15, INK)
        box(slide, 0.6, y + 0.42, 5.6, 0.55, fill=LIGHT, radius=0.1)
        box(slide, 0.6, y + 0.42, 5.6 * pct, 0.55, fill=fill, radius=0.1)
        write(slide, 0.6 + 5.6 * pct + 0.12, y + 0.42, 1.2, 0.55, f"{pct * 100:.1f}%".replace(".", ","), 18, DARK,
              bold=True, anchor=MSO_ANCHOR.MIDDLE)
    write(slide, 0.6, 5.1, 5.7, 1.2, ["Chỉ số tự động đánh giá quá cao khoảng **2,5 lần**; hai bên chỉ cùng kết luận ở "
                                      "44,7% gợi ý → kết luận về diễn đạt lại phải dựa vào người chấm."], 14, INK)
    items = [("warning", ORANGE, "BLEU thưởng việc chép câu", "Chép nguyên câu gốc đạt BLEU 76,1, cao hơn cả câu do người viết (74,2)"),
             ("database", TEAL, "VEC chứa 83% ViLexNorm", "Bỏ 8.665 câu trùng để tập test không lọt vào dữ liệu huấn luyện"),
             ("scale", TEAL, "Điều kiện giữ đặt trước", "Hai cách ghép từ điển tốt hơn trên tin nhắn thật nhưng tụt ở câu gõ "
                                                       "nhanh → giữ mô hình cũ")]
    for i, (name, fill, title, desc) in enumerate(items):
        row(slide, icons, 7.0, 1.75 + i * 1.6, 5.73, name, fill, title, desc)


def document_mode(slide, icons):
    framed_picture(slide, "reports/figures/demo_van_ban.png", 0.6, 1.65, 8.3, 4.6)
    items = [("code", TEAL, "Gõ nhiều đoạn", "Như phần mềm soạn thảo; xuống dòng hoặc . ! ? là sang câu mới"),
             ("check", ORANGE, "Chỉ sửa chính tả", "Không có nút Gửi, không diễn đạt lại"),
             ("chat", TEAL, "Gợi ý dưới dòng đang gõ", "Bấm vào câu bất kỳ để xem và sửa riêng câu đó")]
    for i, (name, fill, title, desc) in enumerate(items):
        row(slide, icons, 9.2, 1.75 + i * 1.55, 3.55, name, fill, title, desc, d=0.6, title_size=16, desc_size=13)


# ============================================================== thêm và sắp xếp slide
def new_slide(prs, title: str, number_from):
    layout = next(l for l in prs.slide_layouts if l.name == "CONTENT")
    import copy
    sl = prs.slides.add_slide(layout)
    # layout của mẫu không tự sinh ô tiêu đề và số trang cho slide mới: chép từ một slide nội dung có sẵn
    for donor in number_from.shapes:
        if donor.is_placeholder and ("Slide Number" in donor.name or donor.placeholder_format.idx == 100):
            el = copy.deepcopy(donor._element)
            if donor.placeholder_format.idx == 100:
                ts = el.findall(".//" + qn("a:t"))
                ts[0].text = title
                for t in ts[1:]:
                    t.text = ""
            sl.shapes._spTree.append(el)
    return sl


def reorder(prs, order: list) -> None:
    ids = prs.slides._sldIdLst
    by_part = {prs.part.related_part(s.rId): s for s in ids}
    wanted = [next(e for p, e in by_part.items() if p is sl.part) for sl in order]
    if len(wanted) != len(ids):
        raise SystemExit("Thứ tự slide thiếu hoặc thừa")
    for e in list(ids):
        ids.remove(e)
    for e in wanted:
        ids.append(e)
