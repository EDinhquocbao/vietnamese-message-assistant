import re
import unicodedata

import yaml

_ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]")
_SPACES = re.compile(r"\s+")


def normalize_text(text) -> str:
    """Chuẩn hóa nhẹ: NFC, bỏ ký tự vô hình, gộp khoảng trắng.

    Cố ý KHÔNG hạ chữ thường và KHÔNG bỏ dấu, vì lỗi dấu là đối tượng cần sửa.
    """
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    text = _ZERO_WIDTH.sub("", text)
    text = text.replace("\u00a0", " ")
    text = _SPACES.sub(" ", text)
    return text.strip()


def load_config(path: str = "configs/data.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def pick_column(columns, preferred, candidates, role: str) -> str:
    """Chọn cột theo cấu hình; nếu chưa cấu hình thì dò theo tên gợi ý."""
    cols = list(columns)
    if preferred:
        if preferred not in cols:
            raise KeyError(f"Cột '{preferred}' ({role}) không có trong dữ liệu. Các cột hiện có: {cols}")
        return preferred
    lowered = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    raise KeyError(
        f"Không tự dò được cột {role}. Các cột hiện có: {cols}. "
        f"Hãy điền tên cột vào configs/data.yaml."
    )


VSEC_SOURCE_CANDS = ["text", "noisy", "wrong", "error", "errors", "incorrect", "misspelled", "input", "source", "src", "text"]
VSEC_TARGET_CANDS = ["corrected_text", "clean", "correct", "corrected", "target", "tgt", "label", "output", "gold", "truth"]
VISP_SOURCE_CANDS = ["original_text", "original", "source", "src", "sentence1", "input", "text"]
VISP_TARGET_CANDS = ["paraphrase_text", "paraphrase", "paraphrased", "target", "tgt", "sentence2", "output"]
