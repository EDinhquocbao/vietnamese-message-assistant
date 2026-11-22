"""Sinh ứng viên cho từng từ và tìm các câu ghép tốt nhất (từ điển chỉ ĐỀ XUẤT, mô hình mới là bên chọn).

Điểm ứng viên theo mô hình kênh nhiễu: log P(người dùng gõ `t` | từ đúng là `c`) xấp xỉ theo nguồn gợi ra ứng viên
(bảng từ train, Telex, đổi dấu, gần giống, tách dính chữ). Chính từ gốc luôn là một ứng viên.
Câu được ghép bằng beam search: điểm kênh nhiễu * alpha + log P(từ | từ trước) theo bigram.
"""
import json
import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.lexicon.build import START
from src.lexicon.telex import decode
from src.utils.text_utils import normalize_text

SPAN = re.compile(r"\w+|[^\w\s]")  # cùng cách tách với src.utils.metrics.tokenize, nhưng giữ vị trí ký tự


def strip_marks(word: str) -> str:
    word = word.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", word) if not unicodedata.combining(c))


def match_case(raw: str, cand: str) -> str:
    """Áp chữ hoa của từ gốc lên ứng viên (chữ thường). Ứng viên trùng từ gốc thì giữ nguyên ("iPhone")."""
    if cand == raw.lower():
        return raw
    if len(raw) > 1 and raw.isupper():
        return cand.upper() if " " not in cand else cand.title()
    if raw[:1].isupper():
        return cand[:1].upper() + cand[1:]
    return cand


@dataclass
class Slot:
    start: int
    end: int
    raw: str
    options: list[tuple[str, float]]  # (ứng viên chữ thường, điểm kênh nhiễu), điểm cao trước


@dataclass
class Path_:
    text: str
    score: float


class Lexicon:
    def __init__(self, data: dict, use_nsw: bool = True, use_syllables: bool = True, min_vocab_count: int = 2):
        self.uni = data["unigram"]
        self.bi = {tuple(k.split("\t")): v for k, v in data["bigram"].items()}
        self.mapping = data["mapping"]
        self.nsw = data["nsw"] if use_nsw else {}
        self.total = sum(self.uni.values())
        self.vocab = {w for w, c in self.uni.items() if c >= min_vocab_count and w.isalpha()}
        if use_syllables:
            self.vocab |= set(data["syllables"])
        self.bases: dict[str, set[str]] = defaultdict(set)
        for w in self.vocab:
            self.bases[strip_marks(w)].add(w)
        self.deletes: dict[str, set[str]] = defaultdict(set)
        for b in self.bases:
            for d in self._del(b) | {b}:
                self.deletes[d].add(b)
        self._cache: dict[tuple[str, bool], dict[str, float]] = {}

    @classmethod
    def load(cls, path: str | Path = "data/processed/lexicon/lexicon.json", **kw) -> "Lexicon":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")), **kw)

    @classmethod
    def from_config(cls, cfg: dict) -> "Lexicon":
        return cls.load(cfg["lexicon_path"], use_syllables=cfg.get("use_syllables", True), use_nsw=cfg.get("use_nsw", True))

    @staticmethod
    def _del(w: str) -> set[str]:
        return {w[:i] + w[i + 1:] for i in range(len(w))}

    def _near_bases(self, word: str) -> set[str]:
        """Các dạng không dấu cách `word` khoảng một lỗi đảo/thiếu/thừa/thay ký tự (chỉ mục kiểu SymSpell)."""
        b = strip_marks(word)
        out = set(self.deletes.get(b, ()))
        for d in self._del(b):
            out |= self.deletes.get(d, set())
        out.discard(b)
        return out

    def channel(self, token: str, restrict: bool = False) -> dict[str, float]:
        """{ứng viên chữ thường: điểm}. restrict=True (từ viết hoa giữa câu, có thể là tên riêng): không dùng
        từ gần giống và tách chữ, để không biến tên riêng thành từ thông dụng."""
        t = token.lower()
        key = (t, restrict)
        if key in self._cache:
            return self._cache[key]
        if not any(c.isalpha() for c in t):
            return self._cache.setdefault(key, {t: 0.0})

        out: dict[str, float] = {}

        def add(c: str, score: float):
            # bảng từ train có nhãn nhiễu ("khôngo", "không ?"): chỉ nhận ứng viên gồm từ có trong từ điển hoặc số
            if c != t and not all(w in self.vocab or w.isdigit() for w in c.split()):
                return
            if score > out.get(c, -math.inf):
                out[c] = score

        known = t in self.vocab
        table = self.mapping.get(t, {})
        total = sum(table.values())
        if t in table:
            add(t, math.log(table[t] / total))
        else:
            add(t, math.log(0.9 if known else 0.02))
        for c, n in table.items():
            if c != t:
                add(c, math.log(n / (total + 1)))
        for c in self.nsw.get(t, ()):
            add(c, math.log(0.2 / len(self.nsw[t])))
        for c in decode(t):
            if c in self.vocab:
                add(c, math.log(0.9 if not known else 0.05))
        if t.isalpha():
            forms = self.bases.get(strip_marks(t), set()) - {t}
            if forms:
                z = sum(self.uni.get(f, 0) + 1 for f in forms)
                w = 0.5 if t.isascii() else 0.1
                for f in forms:
                    add(f, math.log(w * (self.uni.get(f, 0) + 1) / z))
            if not restrict and len(t) >= 2:
                near = {f for b in self._near_bases(t) for f in self.bases[b]}
                z = sum(self.uni.get(f, 0) + 1 for f in near) or 1
                w = 0.005 if known else 0.05
                for f in near:
                    add(f, math.log(w * (self.uni.get(f, 0) + 1) / z))
            if not restrict and not known and len(t) >= 4:
                for i in range(1, len(t)):
                    a, b = t[:i], t[i:]
                    if a in self.vocab and b in self.vocab and self.uni.get(a, 0) >= 20 and self.uni.get(b, 0) >= 20:
                        add(f"{a} {b}", math.log(0.05))
        self._cache[key] = out
        return out

    def options(self, token: str, k: int | None, restrict: bool = False) -> list[tuple[str, float]]:
        """Tối đa k ứng viên điểm cao nhất, luôn gồm chính từ gốc."""
        ch = self.channel(token, restrict)
        ranked = sorted(ch.items(), key=lambda x: -x[1])
        if k is None or len(ranked) <= k:
            return ranked
        top = ranked[:k]
        t = token.lower()
        if not any(c == t for c, _ in top):
            top[-1] = (t, ch[t])
        return top

    def lm(self, prev: str, word: str) -> float:
        p = 0.9 * self.bi.get((prev, word), 0) / max(self.uni.get(prev, 0), 1)
        return math.log(p + 0.1 * (self.uni.get(word, 0) + 0.01) / (self.total + 1) + 1e-12)

    def slots(self, text: str, k: int | None) -> list[Slot]:
        out = []
        for idx, m in enumerate(SPAN.finditer(text)):
            raw = m.group()
            restrict = idx > 0 and raw[:1].isupper()
            out.append(Slot(m.start(), m.end(), raw, self.options(raw, k, restrict)))
        return out

    @staticmethod
    def render(text: str, slots: list[Slot], picks: list[str]) -> str:
        pieces, last = [], 0
        for s, c in zip(slots, picks):
            pieces += [text[last:s.start], match_case(s.raw, c)]
            last = s.end
        return normalize_text("".join(pieces + [text[last:]]))

    def best_paths(self, text: str, k: int = 8, n: int = 8, alpha: float = 1.0, beam: int | None = None) -> list[Path_]:
        """n câu ghép điểm cao nhất, khác nhau về nội dung."""
        text = normalize_text(text)
        slots = self.slots(text, k)
        states: list[tuple[float, str, tuple]] = [(0.0, START, ())]
        width = beam or max(n * 5, 40)
        for s in slots:
            grown = []
            for score, prev, picks in states:
                for cand, ch in s.options:
                    words = cand.split()
                    lm, p = 0.0, prev
                    for w in words:
                        lm += self.lm(p, w)
                        p = w
                    grown.append((score + alpha * ch + lm, p, picks + (cand,)))
            grown.sort(key=lambda x: -x[0])
            states = grown[:width]
        seen, out = set(), []
        for score, _, picks in states:
            sent = self.render(text, slots, list(picks))
            if sent not in seen:
                seen.add(sent)
                out.append(Path_(sent, score))
            if len(out) == n:
                break
        return out
