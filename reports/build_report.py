"""Dựng báo cáo đồ án (.docx) từ mẫu của giảng viên, nội dung lấy từ reports/report_content.py.

Chạy từ thư mục gốc repo:  .venv/Scripts/python.exe reports/build_report.py
Kết quả: reports/Bao_cao_do_an_Dinh_Quoc_Bao.docx (mở bằng Word, cập nhật mục lục: scripts PowerShell ở cuối docstring này
hoặc nhấn Ctrl+A rồi F9).

Giữ nguyên từ mẫu: trang bìa (logo, khung viền), 3 section (bìa / phần đầu số La Mã / nội dung số thường), header, footer.
Thay toàn bộ phần còn lại. Quy ước định dạng theo yêu cầu người dùng: Times New Roman toàn bộ, đánh số đề mục
"Chương 1." (căn giữa) -> 1.1 -> 1.1.1 (sát lề trái, không thụt), giãn dòng 1,5, nội dung căn đều, trích dẫn IEEE,
công thức là Equation (OMML) của Word. Phiếu chấm lấy từ file phiếu chấm riêng của giảng viên.
"""
import re
import struct
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "Bao_cao_do_an_Dinh_Quoc_Bao.docx"
FONT = "Times New Roman"
BODY_SZ = 26          # 13 pt
TABLE_SZ = 24         # 12 pt
TEXT_WIDTH = 11906 - 1701 - 1134   # twips: A4 trừ lề trái 3 cm, phải 2 cm
NUM_HEAD, NUM_BULLET = 90, 91      # numId mới cho đề mục và gạch đầu dòng


def find_file(prefix: str) -> Path:
    for p in ROOT.glob("*.docx"):
        if unicodedata.normalize("NFC", p.name).startswith(prefix):
            return p
    sys.exit(f"Không thấy file bắt đầu bằng '{prefix}' ở thư mục gốc")


# ============================================================== chữ, đoạn
def rpr(b=False, i=False, sz=BODY_SZ, sup=False, sub=False) -> str:
    return (f'<w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:eastAsia="{FONT}" w:cs="{FONT}"/>'
            + ("<w:b/><w:bCs/>" if b else "") + ("<w:i/><w:iCs/>" if i else "")
            + ('<w:vertAlign w:val="superscript"/>' if sup else "") + ('<w:vertAlign w:val="subscript"/>' if sub else "")
            + f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>')


def run(text: str, **kw) -> str:
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


class Cites:
    """Đánh số trích dẫn theo thứ tự xuất hiện đầu tiên (IEEE)."""

    def __init__(self, refs: dict[str, str]):
        self.refs, self.order = refs, []

    def num(self, key: str) -> int:
        if key not in self.refs:
            sys.exit(f"Thiếu tài liệu tham khảo: {key}")
        if key not in self.order:
            self.order.append(key)
        return self.order.index(key) + 1


CITES: Cites | None = None
TOKEN = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`|\^\{.+?\}|_\{.+?\}|\[@[^\]]+\])")


def rich(text: str, sz=BODY_SZ, b=False, i=False) -> str:
    """Chữ có định dạng nhỏ: **đậm**, *nghiêng*, `tên tệp/lệnh` (nghiêng), ^{trên}, _{dưới}, [@khóa1; @khóa2] -> [1], [2]."""
    out = []
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**"):
            out.append(run(part[2:-2], b=True, i=i, sz=sz))
        elif part.startswith("`"):
            out.append(run(part[1:-1], b=b, i=True, sz=sz))
        elif part.startswith("*"):
            out.append(run(part[1:-1], b=b, i=True, sz=sz))
        elif part.startswith("^{"):
            out.append(run(part[2:-1], b=b, i=i, sz=sz, sup=True))
        elif part.startswith("_{"):
            out.append(run(part[2:-1], b=b, i=i, sz=sz, sub=True))
        elif part.startswith("[@"):
            keys = [k.strip().lstrip("@") for k in part[1:-1].split(";")]
            nums = sorted(CITES.num(k) for k in keys)
            out.append(run(", ".join(f"[{n}]" for n in nums), b=b, i=i, sz=sz))
        else:
            out.append(run(part, b=b, i=i, sz=sz))
    return "".join(out)


def ppr(jc="both", before=0, after=120, line=360, keep_next=False, extra="") -> str:
    return (f"<w:pPr>{extra}{'<w:keepNext/>' if keep_next else ''}"
            f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>'
            f'<w:ind w:left="0" w:firstLine="0"/><w:jc w:val="{jc}"/></w:pPr>')


def para(text: str, jc="both", **kw) -> str:
    b, i = kw.pop("b", False), kw.pop("i", False)
    sz = kw.pop("sz", BODY_SZ)
    return f"<w:p>{ppr(jc=jc, **kw)}{rich(text, sz=sz, b=b, i=i)}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def heading(level: int, text: str, numbered=True, page_break_before=None) -> str:
    extra = f'<w:pStyle w:val="Heading{level}"/>'
    if not numbered:
        extra += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="0"/></w:numPr>'
    if page_break_before is False:
        extra += '<w:pageBreakBefore w:val="0"/>'
    return f'<w:p><w:pPr>{extra}</w:pPr>{run(text, b=True, sz=28 if level == 1 else BODY_SZ)}</w:p>'


def bullets(items: list[str]) -> str:
    out = []
    for it in items:
        out.append(f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{NUM_BULLET}"/></w:numPr>'
                   f'<w:spacing w:before="0" w:after="60" w:line="360" w:lineRule="auto"/>'
                   f'<w:ind w:left="284" w:hanging="284"/><w:jc w:val="both"/></w:pPr>{rich(it)}</w:p>')
    return "".join(out)


def caption(kind: str, text: str) -> str:
    style = "ChuThichBang" if kind == "bang" else "ChuThichHinh"
    label, rest = text.split(" ", 2)[:2], text.split(" ", 2)[2] if text.count(" ") >= 2 else ""
    return (f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{run(" ".join(label) + " ", b=True, sz=TABLE_SZ)}'
            f"{rich(rest, sz=TABLE_SZ, i=True)}</w:p>")


# ============================================================== bảng
def table(header: list[str], rows: list[list[str]], widths: list[float], align: list[str] | None = None) -> str:
    total = TEXT_WIDTH
    cols = [int(total * w / sum(widths)) for w in widths]
    align = align or ["left"] * len(header)
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join(f'<w:gridCol w:w="{c}"/>' for c in cols)

    def cell(text, w, head, jc):
        jc = "both" if jc == "left" else jc    # người dùng yêu cầu mọi nội dung căn đều
        shade = '<w:shd w:val="clear" w:color="auto" w:fill="E7E6E6"/>' if head else ""
        paras = "".join(f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="276" w:lineRule="auto"/>'
                        f'<w:jc w:val="{"center" if head else jc}"/></w:pPr>{rich(line, sz=TABLE_SZ, b=head)}</w:p>'
                        for line in str(text).split("\n"))
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}<w:vAlign w:val="center"/></w:tcPr>{paras}</w:tc>'

    head = ('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>'
            + "".join(cell(h, c, True, "center") for h, c in zip(header, cols)) + "</w:tr>")
    body = "".join("<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(v, c, False, a) for v, c, a in zip(r, cols, align))
                   + "</w:tr>" for r in rows)
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{border}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/>'
            f'</w:tblCellMar><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" '
            f'w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{head}{body}</w:tbl>'
            + '<w:p><w:pPr><w:spacing w:before="0" w:after="60" w:line="240" w:lineRule="auto"/></w:pPr></w:p>')


# ============================================================== hình
class Media:
    def __init__(self):
        self.files: list[tuple[str, bytes, str]] = []   # (tên trong zip, dữ liệu, rId)
        self.next_id = 1000

    def add(self, path: Path) -> tuple[str, int, int]:
        data = path.read_bytes()
        w, h = struct.unpack(">II", data[16:24])          # PNG IHDR
        rid = f"rIdFig{len(self.files) + 1}"
        self.files.append((f"word/media/fig{len(self.files) + 1}.png", data, rid))
        return rid, w, h


MEDIA = Media()


def figure(path: str, width_cm: float = 15.0) -> str:
    rid, w, h = MEDIA.add(ROOT / path)
    cx = int(width_cm * 360000)
    cy = int(cx * h / w)
    MEDIA.next_id += 1
    n = MEDIA.next_id
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    pic = "http://schemas.openxmlformats.org/drawingml/2006/picture"
    drawing = (f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
               f'<wp:docPr id="{n}" name="Hinh {n}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{a}" noChangeAspect="1"/>'
               f'</wp:cNvGraphicFramePr><a:graphic xmlns:a="{a}"><a:graphicData uri="{pic}"><pic:pic xmlns:pic="{pic}">'
               f'<pic:nvPicPr><pic:cNvPr id="{n}" name="{escape(Path(path).name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect">'
               f'<a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>')
    return (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="60" w:line="240" w:lineRule="auto"/>'
            f'<w:jc w:val="center"/></w:pPr><w:r>{drawing}</w:r></w:p>')


# ============================================================== công thức (OMML)
def mr(t: str, plain=False) -> str:
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if plain else ""
    return f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{escape(t)}</m:t></m:r>'


def mt(t: str) -> str:
    """Chữ thường (không nghiêng) trong công thức, vd tên hàm hoặc chữ tiếng Việt."""
    return mr(t, plain=True)


def frac(n: str, d: str) -> str:
    return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"


def sub(b: str, s: str) -> str:
    return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"


def sup(b: str, s: str) -> str:
    return f"<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>"


def nary(ch: str, lo: str, hi: str, e: str) -> str:
    hide = ("" if lo else '<m:subHide m:val="1"/>') + ("" if hi else '<m:supHide m:val="1"/>')
    return (f'<m:nary><m:naryPr><m:chr m:val="{ch}"/><m:limLoc m:val="undOvr"/>{hide}</m:naryPr>'
            f"<m:sub>{lo}</m:sub><m:sup>{hi}</m:sup><m:e>{e}</m:e></m:nary>")


def paren(e: str, beg="(", end=")") -> str:
    return f'<m:d><m:dPr><m:begChr m:val="{escape(beg)}"/><m:endChr m:val="{escape(end)}"/></m:dPr><m:e>{e}</m:e></m:d>'


def sqrt(e: str) -> str:
    return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>'


def func(name: str, arg: str) -> str:
    return f"<m:func><m:fName>{mt(name)}</m:fName><m:e>{arg}</m:e></m:func>"


def lim_low(base: str, low: str) -> str:
    return f"<m:func><m:fName><m:limLow><m:e>{mt(base)}</m:e><m:lim>{low}</m:lim></m:limLow></m:fName><m:e></m:e></m:func>"


def hat(e: str) -> str:
    return f'<m:acc><m:accPr><m:chr m:val="&#770;"/></m:accPr><m:e>{e}</m:e></m:acc>'


def equation(omml: str, label: str) -> str:
    """Công thức kiểu hiển thị (phân số, tổng cỡ lớn) căn giữa trang, số thứ tự (x.y) sát lề phải.
    Dùng bảng 3 cột không viền: cột giữa chứa oMathPara, cột phải chứa số thứ tự."""
    side = 1000
    cols = [side, TEXT_WIDTH - 2 * side, side]
    none = "".join(f'<w:{s} w:val="nil"/>' for s in ("top", "left", "bottom", "right", "insideH", "insideV"))

    def cell(w, inner):
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>{inner}</w:tc>')

    sp = '<w:spacing w:before="60" w:after="140" w:line="240" w:lineRule="auto"/>'
    math =(f'<w:p><w:pPr>{sp}<w:jc w:val="center"/></w:pPr><m:oMathPara><m:oMathParaPr><m:jc m:val="center"/>'
            f'</m:oMathParaPr><m:oMath>{omml}</m:oMath></m:oMathPara></w:p>')
    num = f'<w:p><w:pPr>{sp}<w:jc w:val="right"/></w:pPr>{run(f"({label})")}</w:p>'
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{none}</w:tblBorders>'
            f'<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/>'
            f'</w:tblCellMar><w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>{"".join(f"<w:gridCol w:w=\"{c}\"/>" for c in cols)}'
            f'</w:tblGrid><w:tr><w:trPr><w:cantSplit/></w:trPr>{cell(cols[0], f"<w:p><w:pPr>{sp}</w:pPr></w:p>")}'
            f'{cell(cols[1], math)}{cell(cols[2], num)}</w:tr></w:tbl>')


# ============================================================== trường (mục lục)
def field(instr: str, placeholder: str) -> str:
    return (f'<w:p><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr>'
            f'<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve"> {escape(instr)} </w:instrText></w:r>'
            f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>{run(placeholder, i=True)}'
            f'<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')


# ============================================================== kiểu (styles.xml) và đánh số (numbering.xml)
def fix_styles(xml: str) -> str:
    tnr = f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:eastAsia="{FONT}" w:cs="{FONT}"/>'
    xml = re.sub(r"<w:rFonts\b[^>]*/>", tnr, xml)
    # bỏ định nghĩa cũ của Heading1-3, TOC1-3 rồi thêm lại theo quy ước
    for sid in ("Heading1", "Heading2", "Heading3", "TOC1", "TOC2", "TOC3", "ChuThichBang", "ChuThichHinh"):
        xml = re.sub(rf'<w:style [^>]*w:styleId="{sid}"[^>]*>.*?</w:style>', "", xml, flags=re.S)

    def head(level, name, sz, jc, before, after, pbb):
        return (f'<w:style w:type="paragraph" w:styleId="Heading{level}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
                f'<w:next w:val="Normal"/><w:link w:val="Heading{level}Char"/><w:uiPriority w:val="9"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:keepLines/>{"<w:pageBreakBefore/>" if pbb else ""}'
                f'<w:numPr><w:ilvl w:val="{level - 1}"/><w:numId w:val="{NUM_HEAD}"/></w:numPr>'
                f'<w:spacing w:before="{before}" w:after="{after}" w:line="360" w:lineRule="auto"/>'
                f'<w:ind w:left="0" w:firstLine="0"/><w:jc w:val="{jc}"/><w:outlineLvl w:val="{level - 1}"/></w:pPr>'
                f'<w:rPr>{tnr}<w:b/><w:bCs/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:style>')

    def toc(n):
        return (f'<w:style w:type="paragraph" w:styleId="TOC{n}"><w:name w:val="toc {n}"/><w:basedOn w:val="Normal"/>'
                f'<w:next w:val="Normal"/><w:uiPriority w:val="39"/><w:unhideWhenUsed/><w:pPr><w:tabs>'
                f'<w:tab w:val="right" w:leader="dot" w:pos="{TEXT_WIDTH}"/></w:tabs>'
                f'<w:spacing w:before="0" w:after="0" w:line="360" w:lineRule="auto"/><w:ind w:left="0" w:firstLine="0"/></w:pPr>'
                f'<w:rPr>{tnr}{"<w:b/>" if n == 1 else ""}<w:sz w:val="{BODY_SZ}"/><w:szCs w:val="{BODY_SZ}"/></w:rPr></w:style>')

    def cap(sid, name, keep_next):
        return (f'<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}"><w:name w:val="{name}"/>'
                f'<w:basedOn w:val="Normal"/><w:qFormat/><w:pPr>{"<w:keepNext/>" if keep_next else ""}'
                f'<w:spacing w:before="60" w:after="120" w:line="360" w:lineRule="auto"/><w:ind w:left="0" w:firstLine="0"/>'
                f'<w:jc w:val="center"/></w:pPr><w:rPr>{tnr}<w:sz w:val="{TABLE_SZ}"/><w:szCs w:val="{TABLE_SZ}"/></w:rPr></w:style>')

    new = (head(1, "heading 1", 28, "center", 0, 240, True) + head(2, "heading 2", BODY_SZ, "left", 240, 120, False)
           + head(3, "heading 3", BODY_SZ, "left", 180, 120, False) + toc(1) + toc(2) + toc(3)
           + cap("ChuThichBang", "Chu thich bang", True) + cap("ChuThichHinh", "Chu thich hinh", False))
    # cỡ chữ mặc định 13 pt
    xml = re.sub(r'(<w:rPrDefault><w:rPr>.*?)<w:sz w:val="\d+"/>', rf'\1<w:sz w:val="{BODY_SZ}"/>', xml, count=1, flags=re.S)
    return xml.replace("</w:styles>", new + "</w:styles>")


def fix_numbering(xml: str) -> str:
    def lvl(i, fmt, text, style=None):
        st = f'<w:pStyle w:val="{style}"/>' if style else ""
        return (f'<w:lvl w:ilvl="{i}"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/>{st}<w:lvlText w:val="{text}"/>'
                f'<w:lvlJc w:val="left"/><w:suff w:val="space"/><w:pPr><w:ind w:left="0" w:firstLine="0"/></w:pPr>'
                f'<w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:b/></w:rPr></w:lvl>')

    head = (f'<w:abstractNum w:abstractNumId="{NUM_HEAD}"><w:multiLevelType w:val="multilevel"/>'
            + lvl(0, "decimal", "Chương %1.", "Heading1") + lvl(1, "decimal", "%1.%2.", "Heading2")
            + lvl(2, "decimal", "%1.%2.%3.", "Heading3") + "</w:abstractNum>")
    bullet = (f'<w:abstractNum w:abstractNumId="{NUM_BULLET}"><w:multiLevelType w:val="singleLevel"/>'
              f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/>'
              f'<w:lvlJc w:val="left"/><w:pPr><w:ind w:left="284" w:hanging="284"/></w:pPr>'
              f'<w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/></w:rPr></w:lvl></w:abstractNum>')
    first_num = xml.index("<w:num ")
    xml = xml[:first_num] + head + bullet + xml[first_num:]
    nums = (f'<w:num w:numId="{NUM_HEAD}"><w:abstractNumId w:val="{NUM_HEAD}"/></w:num>'
            f'<w:num w:numId="{NUM_BULLET}"><w:abstractNumId w:val="{NUM_BULLET}"/></w:num>')
    return xml.replace("</w:numbering>", nums + "</w:numbering>")


# ============================================================== ghép tài liệu
def cover(xml_body_cover: str, info: dict) -> str:
    rep = {
        "PHÂN TÍCH TRỰC QUAN HÓA DỮ LIỆU VỀ WORLD CUP SỬ DỤNG PYTHON": info["title"].upper(),
        "SINH VIÊN: NGUYEN VAN A - MSSV": f"SINH VIÊN: {info['name'].upper()}",
        ">LỚP:<": f">MSSV: {info['mssv']} - LỚP: {info['class']}<",   # giữ đúng số dòng để bìa không tràn trang
        "GIẢNG VIÊN:                 ": f"GIẢNG VIÊN: {info['teacher'].upper()}",
    }
    for a, b in rep.items():
        if a not in xml_body_cover:
            sys.exit(f"Không thấy chữ '{a}' ở trang bìa mẫu")
        xml_body_cover = xml_body_cover.replace(a, escape(b) if not a.startswith(">") else b)
    return xml_body_cover


def rubric(info: dict) -> str:
    """Phiếu chấm riêng của giảng viên (giữ nguyên định dạng), điền sẵn thông tin sinh viên."""
    x = zipfile.ZipFile(find_file("Phiếu chấm")).read("word/document.xml").decode("utf-8")
    body = x[x.index("<w:body>") + len("<w:body>"):x.rindex("<w:sectPr")]
    fill = [(">:<", f">: {info['name']}<"), (">Mã số Sinh viên:<", f">Mã số Sinh viên: {info['mssv']}<"),
            (">Lớp:<", f">Lớp: {info['class']}<"), (">Tên Đồ án/Tiểu luận:<", f">Tên Đồ án/Tiểu luận: {escape(info['title'])}<")]
    for a, b in fill:
        if a not in body:
            sys.exit(f"Phiếu chấm: không thấy '{a}'")
        body = body.replace(a, b, 1)
    return body


def build(content_module) -> None:
    global CITES
    tpl = find_file("Mẫu Báo cáo")
    zin = zipfile.ZipFile(tpl)
    doc = zin.read("word/document.xml").decode("utf-8")
    secs = [m for m in re.finditer(r"<w:sectPr\b.*?</w:sectPr>", doc, re.S)]
    if len(secs) != 3:
        sys.exit(f"Mẫu có {len(secs)} section, cần 3")
    body_start = doc.index("<w:body>") + len("<w:body>")
    # đoạn chứa sectPr của bìa kết thúc ở </w:p> ngay sau sectPr thứ nhất
    cover_end = doc.index("</w:p>", secs[0].end()) + len("</w:p>")
    sect2, sect3 = secs[1].group(), secs[2].group()

    info = content_module.INFO
    CITES = Cites(content_module.REFERENCES)
    front = content_module.front_matter(rubric(info))
    main = content_module.main_matter()
    refs = "".join(para(f"[{n}] {content_module.REFERENCES[k]}", jc="both", after=60)
                   for n, k in enumerate(CITES.order, 1))
    unused = set(content_module.REFERENCES) - set(CITES.order)
    if unused:
        sys.exit(f"Tài liệu không được trích trong bài: {sorted(unused)}")
    back = content_module.back_matter(refs)

    new_doc = (doc[:body_start] + cover(doc[body_start:cover_end], info) + front
               + f"<w:p><w:pPr>{sect2}</w:pPr></w:p>" + main + back + sect3 + "</w:body></w:document>")

    rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
    rels = rels.replace("</Relationships>", "".join(
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="{name.split("word/")[1]}"/>' for name, _, rid in MEDIA.files) + "</Relationships>")
    ctypes = zin.read("[Content_Types].xml").decode("utf-8")
    if 'Extension="png"' not in ctypes:
        ctypes = ctypes.replace("<Default ", '<Default Extension="png" ContentType="image/png"/><Default ', 1)

    # không ghi đè file đang mở trong Word
    lock = OUT.with_name("~$" + OUT.name[2:])
    if lock.exists():
        sys.exit(f"File đang mở trong Word: {OUT.name}. Hãy đóng file rồi chạy lại.")
    if OUT.exists():
        try:
            OUT.open("r+b").close()
        except PermissionError:
            sys.exit(f"File đang bị khóa: {OUT.name}. Hãy đóng file rồi chạy lại.")

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = new_doc.encode("utf-8")
            elif item.filename == "word/styles.xml":
                data = fix_styles(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/numbering.xml":
                data = fix_numbering(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/_rels/document.xml.rels":
                data = rels.encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                data = ctypes.encode("utf-8")
            zout.writestr(item, data)
        for name, data, _ in MEDIA.files:
            zout.writestr(name, data)
    print(f"Đã ghi {OUT.relative_to(ROOT)}: {len(CITES.order)} tài liệu tham khảo, {len(MEDIA.files)} hình")


if __name__ == "__main__":
    # chạy qua module "build_report" (không phải __main__) để report_content dùng chung trạng thái trích dẫn và hình
    sys.path.insert(0, str(Path(__file__).parent))
    import build_report as engine
    import report_content
    engine.build(report_content)
