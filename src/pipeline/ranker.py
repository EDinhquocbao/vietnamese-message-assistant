"""Lọc và xếp hạng các câu diễn đạt lại ứng viên -> 2-3 gợi ý cuối.

Một ứng viên bị loại nếu:
- làm mất/đổi số, mã, giờ, ngày (8h, 200k, #A1023, 15/11), tên riêng (chữ hoa giữa câu),
  hoặc thêm/bỏ phủ định (không, chưa, chẳng, đừng...) -> đổi nghĩa dù embedding vẫn gần;
- độ tương đồng ngữ nghĩa với câu gốc (cosine embedding) < min_similarity;
- gần như chép lại câu gốc (độ trùng từ > max_overlap).
Điểm = similarity + diversity_weight * (1 - overlap): ưu tiên câu giữ nghĩa nhưng khác cách nói.
Các gợi ý được chọn lần lượt kiểu MMR để không na ná nhau.
"""
import re
from difflib import SequenceMatcher
from typing import Callable

import numpy as np

from src.utils.metrics import tokenize

NEGATIONS = {"không", "chưa", "chẳng", "chả", "đừng", "chớ", "ko", "k", "hông"}
_NUMBER = re.compile(r"[#\w./:,-]*\d[\w./:,-]*")
_SENT_END = {".", "!", "?", ":", "…"}


def protected_spans(text: str) -> dict:
    numbers = {m.group().rstrip(".,:-") for m in _NUMBER.finditer(text)}
    names, current, prev = set(), [], "."
    for tok in tokenize(text):
        is_cap = tok[:1].isupper() and tok.isalpha()
        if is_cap and (prev not in _SENT_END or current):  # bỏ chữ hoa đầu câu
            current.append(tok)
        else:
            if current:
                names.add(" ".join(current))
            current = []
        prev = tok
    if current:
        names.add(" ".join(current))
    negation = any(t.lower() in NEGATIONS for t in tokenize(text))
    return {"numbers": numbers, "names": names, "negation": negation}


def violates_protected(source: str, candidate: str) -> str | None:
    """Trả về lý do vi phạm (để hiển thị ở demo) hoặc None nếu ứng viên an toàn."""
    s, c = protected_spans(source), protected_spans(candidate)
    if missing := [n for n in s["numbers"] if n not in candidate]:
        return f"mất số/mã: {', '.join(sorted(missing))}"
    if extra := c["numbers"] - s["numbers"]:
        return f"thêm số/mã: {', '.join(sorted(extra))}"
    if missing := [n for n in s["names"] if n not in candidate]:
        return f"mất tên riêng: {', '.join(sorted(missing))}"
    if s["negation"] != c["negation"]:
        return "đổi phủ định"
    return None


def word_overlap(a: str, b: str) -> float:
    ta, tb = [t.lower() for t in tokenize(a)], [t.lower() for t in tokenize(b)]
    return SequenceMatcher(a=ta, b=tb, autojunk=False).ratio()


class Ranker:
    def __init__(self, encode: Callable[[list[str]], np.ndarray] | None = None,
                 model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                 top_k: int = 3, min_similarity: float = 0.8, max_overlap: float = 0.9,
                 diversity_weight: float = 0.3, redundancy_weight: float = 0.5):
        self._encode, self.model_name = encode, model_name
        self.top_k, self.min_similarity, self.max_overlap = top_k, min_similarity, max_overlap
        self.diversity_weight, self.redundancy_weight = diversity_weight, redundancy_weight

    def encode(self, texts: list[str]) -> np.ndarray:
        """Embedding đã chuẩn hóa L2 (tích vô hướng = cosine). Nạp mô hình khi cần lần đầu."""
        if self._encode is None:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.model_name)
            self._encode = lambda xs: model.encode(xs, normalize_embeddings=True, convert_to_numpy=True)
        return self._encode(texts)

    def score_all(self, source: str, candidates: list[str]) -> list[dict]:
        """Chấm mọi ứng viên; `rejected` là lý do bị loại (None nếu giữ)."""
        if not candidates:
            return []
        emb = self.encode([source] + candidates)
        sims = emb[1:] @ emb[0]
        rows = []
        for c, sim in zip(candidates, sims):
            ov = word_overlap(source, c)
            reason = violates_protected(source, c)
            if reason is None and sim < self.min_similarity:
                reason = f"khác nghĩa (similarity {sim:.2f})"
            if reason is None and ov > self.max_overlap:
                reason = "gần như chép lại câu gốc"
            rows.append({"text": c, "similarity": float(sim), "overlap": ov,
                         "score": float(sim) + self.diversity_weight * (1 - ov), "rejected": reason})
        return rows

    def select(self, rows: list[dict]) -> list[dict]:
        pool = [r for r in rows if r["rejected"] is None]
        chosen = []
        while pool and len(chosen) < self.top_k:
            def mmr(r):
                red = max((word_overlap(r["text"], c["text"]) for c in chosen), default=0.0)
                return r["score"] - self.redundancy_weight * red

            best = max(pool, key=mmr)
            pool.remove(best)
            if all(word_overlap(best["text"], c["text"]) <= self.max_overlap for c in chosen):
                chosen.append(best)
        return chosen

    def rank(self, source: str, candidates: list[str]) -> list[dict]:
        return self.select(self.score_all(source, candidates))
