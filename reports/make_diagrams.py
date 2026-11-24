"""Vẽ sơ đồ cho báo cáo -> reports/figures/04_*.png.  Chạy: .venv/Scripts/python.exe reports/make_diagrams.py"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "figures"
plt.rcParams["font.family"] = "Times New Roman"
EDGE, FILL, ACCENT = "#333333", "#F4F4F4", "#DCE6F0"


def box(ax, x, y, w, h, text, fill=FILL, size=11, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fill, ec=EDGE, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, weight="bold" if bold else "normal",
            wrap=True, linespacing=1.3)


def arrow(ax, x1, y1, x2, y2, text=None, both=False):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="<|-|>" if both else "-|>", mutation_scale=12,
                                 lw=1.1, color=EDGE))
    if text:
        ax.text((x1 + x2) / 2 + 0.08, (y1 + y2) / 2, text, fontsize=9.5, va="center", style="italic")


def architecture():
    fig, ax = plt.subplots(figsize=(10, 7.2))
    ax.set_xlim(0, 10), ax.set_ylim(0, 7.2), ax.axis("off")
    box(ax, 0.3, 6.1, 9.4, 0.8, "Giao diện trình duyệt (app/realtime/index.html)\nChế độ tin nhắn  |  Chế độ văn bản (như Word)",
        ACCENT, 11.5, True)
    arrow(ax, 5, 6.1, 5, 5.45, "WebSocket: update / pause / pick / send", both=True)
    box(ax, 0.3, 4.65, 9.4, 0.8, "Máy chủ (app/realtime/server.py): mỗi kết nối một phiên; GPU chạy một việc một lúc",
        FILL, 11.5, True)
    # nhánh trái: gợi ý khi gõ
    arrow(ax, 2.6, 4.65, 2.6, 4.1)
    box(ax, 0.3, 3.1, 4.6, 1.0, "Gợi ý khi gõ (src/realtime/session.py)\nTách câu theo . ! ? và xuống dòng", FILL, 10.5)
    arrow(ax, 1.4, 3.1, 1.4, 2.55)
    arrow(ax, 3.8, 3.1, 3.8, 2.55)
    box(ax, 0.3, 1.5, 2.2, 1.05, "Tầng từ điển\nứng viên + bigram\n(< 1 ms)", FILL, 10)
    box(ax, 2.7, 1.5, 2.2, 1.05, "Tầng ViT5\nchấm lại khi dừng tay\n(~60–120 ms)", FILL, 10)
    # nhánh phải: gửi
    arrow(ax, 7.4, 4.65, 7.4, 4.1, "Gửi (chỉ chế độ tin nhắn)")
    box(ax, 5.1, 3.1, 4.6, 1.0, "Sửa lỗi cả câu: ViT5 fine-tune\nN-best -> tối đa 3 câu đã sửa", FILL, 10.5)
    arrow(ax, 7.4, 3.1, 7.4, 2.55)
    box(ax, 5.1, 1.5, 4.6, 1.05, "Diễn đạt lại: ViT5 (ViSP), 8 ứng viên\nLọc: số/tên/phủ định, cosine MiniLM,\nNLI hai chiều; xếp hạng MMR -> 1 câu",
        FILL, 10)
    # tầng dữ liệu
    box(ax, 0.3, 0.15, 9.4, 0.85, "Dữ liệu và mô hình trên máy: models/ (ViT5 sửa lỗi, ViT5 diễn đạt lại),\n"
        "data/processed/lexicon/lexicon.json (từ điển), outputs/logs/realtime_history.jsonl (log lựa chọn)", ACCENT, 10)
    for x in (1.4, 3.8, 7.4):
        arrow(ax, x, 1.5, x, 1.0)
    fig.savefig(OUT / "04_kien_truc_he_thong.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def data_flow():
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_xlim(0, 10), ax.set_ylim(0, 4.6), ax.axis("off")
    steps = [
        (0.2, "Tải dữ liệu\n(ghim theo commit)\nVSEC, ViLexNorm,\nVEC, ViSP"),
        (2.15, "Làm sạch\nNFC, gộp khoảng trắng\n(không hạ chữ thường,\nkhông bỏ dấu)"),
        (4.1, "Chia tập theo nhóm\n+ loại câu trùng\ngiữa train/val/test\n(kiểm tra rò rỉ)"),
        (6.05, "Gộp train/val sửa lỗi\nloại mọi câu thuộc test\ncủa bất kỳ dataset nào"),
        (8.0, "Thêm lỗi nhân tạo\n(chỉ từ câu chuẩn\ncủa TRAIN)"),
    ]
    for x, t in steps:
        box(ax, x, 2.4, 1.6, 1.7, t, FILL, 9)
    for (x1, _), (x2, _) in zip(steps, steps[1:]):
        arrow(ax, x1 + 1.62, 3.25, x2 - 0.02, 3.25)
    box(ax, 1.2, 0.3, 4.4, 1.3, "Tập test giữ riêng từng dataset:\nViLexNorm (chính), VSEC, VEC (tham khảo), ViSP\n"
        "-> báo cáo kết quả riêng", ACCENT, 9.5)
    box(ax, 6.0, 0.3, 3.7, 1.3, "Huấn luyện ViT5 sửa lỗi\nGĐ1: thật + nhân tạo (2 epoch)\nGĐ2: chỉ dữ liệu thật (1 epoch)",
        ACCENT, 9.5)
    arrow(ax, 4.9, 2.4, 4.0, 1.6)
    arrow(ax, 8.8, 2.4, 8.0, 1.6)
    fig.savefig(OUT / "04_luong_du_lieu.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    architecture()
    data_flow()
    print("Đã vẽ:", sorted(p.name for p in OUT.glob("04_*.png")))
