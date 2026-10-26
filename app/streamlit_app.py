"""Demo: sửa lỗi và gợi ý cách diễn đạt cho tin nhắn tiếng Việt.

Chạy từ thư mục gốc repo:  .venv/Scripts/streamlit.exe run app/streamlit_app.py
"""
import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để import được `src` khi chạy bằng streamlit

from src.pipeline.assistant import from_config  # noqa: E402

EXAMPLES = [
    "mai di hoc ko",
    "chị ơi e gửi bài r ạ, c check giúp e vs",
    "Mình đã chuyễn khoản 200k rồi nha",
    "Do vì trời mưa to cho nên mình không đi được",
    "Anh ơi cho em hỏi cái deadline của bài tập lớn là khi nào vậy anh",
]

st.set_page_config(page_title="Trợ lý tin nhắn tiếng Việt", page_icon="✍️")


@st.cache_resource(show_spinner="Đang nạp mô hình...")
def load_assistant():
    return from_config()


def highlight(edits: list[dict]) -> str:
    """Hiển thị các phép sửa dạng ~~cũ~~ → **mới**."""
    if not edits:
        return "_Không phát hiện lỗi._"
    return " · ".join(f"~~{html.escape(e['from'])}~~ → **{html.escape(e['to'])}**" if e["from"]
                      else f"+ **{html.escape(e['to'])}**" for e in edits)


st.title("✍️ Trợ lý tin nhắn tiếng Việt")
st.caption("Sửa lỗi chính tả (ViT5 fine-tune trên VSEC + ViLexNorm + VEC) và gợi ý 2–3 cách diễn đạt lại (ViT5 fine-tune trên ViSP).")

example = st.selectbox("Câu ví dụ", ["(tự nhập)"] + EXAMPLES)
text = st.text_area("Tin nhắn", value="" if example == "(tự nhập)" else example, height=90)

if st.button("Xử lý", type="primary", disabled=not text.strip()):
    try:
        assistant = load_assistant()
    except OSError as e:
        st.error(f"Chưa có mô hình đã huấn luyện ({e}). Chạy src.correction.train và src.paraphrase.train trước.")
        st.stop()
    with st.spinner("Đang xử lý..."):
        r = assistant.run(text)

    st.subheader("1. Câu đã sửa")
    st.success(r["corrected"])
    st.markdown(highlight(r["edits"]))

    st.subheader("2. Gợi ý diễn đạt")
    if not r["suggestions"]:
        st.info("Không có gợi ý nào vừa giữ nghĩa vừa khác câu gốc đủ nhiều.")
    for i, s in enumerate(r["suggestions"], 1):
        st.markdown(f"**{i}.** {s['text']}  \n<small>giống nghĩa {s['similarity']:.2f} · trùng từ {s['overlap']:.2f}</small>",
                    unsafe_allow_html=True)

    with st.expander("Xem từng bước: mọi ứng viên và lý do bị loại"):
        st.dataframe(
            [{"ứng viên": c["text"], "giống nghĩa": round(c["similarity"], 3), "trùng từ": round(c["overlap"], 3),
              "điểm": round(c["score"], 3), "bị loại vì": c["rejected"] or ""} for c in r["candidates"]],
            use_container_width=True,
        )
