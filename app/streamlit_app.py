"""Demo: sửa lỗi và gợi ý cách diễn đạt cho tin nhắn tiếng Việt.

Chạy từ thư mục gốc repo:  .venv/Scripts/streamlit.exe run app/streamlit_app.py
"""
import html
import json
import sys
import time
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

HISTORY = Path("outputs/logs/demo_history.jsonl")  # lưu mỗi lần xử lý để phân tích lỗi sau

st.set_page_config(page_title="Hệ thống sửa lỗi tin nhắn tiếng Việt", page_icon="✍️")


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

def log(entry: dict) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%d %H:%M:%S"), **entry}, ensure_ascii=False) + "\n")


state = st.session_state
if st.button("Xử lý", type="primary", disabled=not text.strip()):
    try:
        assistant = load_assistant()
    except OSError as e:
        st.error(f"Chưa có mô hình đã huấn luyện ({e}). Chạy src.correction.train và src.paraphrase.train trước.")
        st.stop()
    with st.spinner("Đang sửa lỗi..."):
        state.corr = assistant.correct(text)
    state.suggestions = {}  # gợi ý diễn đạt theo từng phương án sửa, tính khi được chọn
    state.logged_choices = set()
    log({"input": text, "choices": state.corr["choices"]})

corr = state.get("corr")
if corr and corr["input"] == text:
    assistant = load_assistant()
    opts = corr["choices"]
    st.subheader("1. Câu đã sửa")
    if len(opts) == 1:
        idx = 0
        st.success(opts[0]["text"])
    else:
        idx = st.radio(
            "Mô hình chưa chắc chắn, chọn câu đúng ý bạn:", range(len(opts)), key=f"choice::{text}",
            format_func=lambda i: f"{opts[i]['text']}   ·   {opts[i]['prob']:.0%}",
        )
        if idx and idx not in state.logged_choices:  # ghi lại lựa chọn khác phương án đầu, để đánh giá sau
            state.logged_choices.add(idx)
            log({"input": text, "chosen": opts[idx]["text"], "rank": idx})
    chosen = opts[idx]["text"]
    if chosen not in state.suggestions:
        with st.spinner("Đang gợi ý cách diễn đạt..."):
            state.suggestions[chosen] = assistant.suggest(text, chosen)
    r = state.suggestions[chosen]

    st.markdown(highlight(r["edits"]))
    if r["unknown_words"]:
        st.warning(f"Từ có thể vẫn còn lỗi: **{', '.join(r['unknown_words'])}**. Hãy kiểm tra lại các từ này.")

    st.subheader("2. Gợi ý diễn đạt")
    if r["unknown_words"]:
        st.info("Không đưa gợi ý vì câu đã sửa còn từ nghi lỗi (gợi ý sinh từ câu sai thường vô nghĩa).")
    elif not r["suggestions"]:
        st.info("Không có gợi ý nào vừa giữ nghĩa vừa khác câu gốc đủ nhiều.")
    for i, sg in enumerate(r["suggestions"], 1):
        st.markdown(f"**{i}.** {html.escape(sg['text'])}  \n"
                    f"<small>giống nghĩa {sg['similarity']:.2f} · trùng từ {sg['overlap']:.2f}</small>",
                    unsafe_allow_html=True)

    with st.expander("Xem từng bước: mọi ứng viên và lý do bị loại"):
        st.dataframe(
            [{"ứng viên": c["text"], "giống nghĩa": round(c["similarity"], 3), "trùng từ": round(c["overlap"], 3),
              "NLI": None if c["entailment"] is None else round(c["entailment"], 3),
              "bị loại vì": c["rejected"] or ""} for c in r["candidates"]],
        )
