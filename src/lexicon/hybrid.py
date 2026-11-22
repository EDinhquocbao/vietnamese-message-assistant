"""Kết hợp từ điển và mô hình sửa lỗi. Có __call__ và nbest nên dùng thẳng được với evaluate() và top_options().

Bốn chế độ để so sánh:
- model:   mô hình hiện tại, làm mốc.
- lexicon: chỉ từ điển + bigram.
- guard:   mô hình sửa trước; phép sửa nào không nằm trong ứng viên của từ điển thì trả về từ gốc.
- rerank:  gộp câu ghép từ từ điển và kết quả beam của mô hình, mô hình chấm log P(câu | nguồn), cộng điểm kênh nhiễu.
"""
import math
from difflib import SequenceMatcher

from src.lexicon.candidates import SPAN, Lexicon
from src.utils.text_utils import normalize_text


def _is_word(tok: str) -> bool:
    return any(c.isalnum() for c in tok)


class CachedModel:
    """Bọc Corrector, nhớ kết quả theo câu để nhiều chế độ/tham số không chạy lại mô hình."""

    def __init__(self, corrector):
        self.corrector = corrector
        self._nbest: dict[str, list[dict]] = {}
        self._scores: dict[tuple[str, str], float] = {}

    def nbest(self, texts: list[str]) -> list[list[dict]]:
        missing = [t for t in dict.fromkeys(texts) if t not in self._nbest]
        if missing:
            self._nbest.update(zip(missing, self.corrector.nbest(missing)))
        return [self._nbest[t] for t in texts]

    def __call__(self, texts: list[str]) -> list[str]:
        return [a[0]["text"] for a in self.nbest(texts)]

    def score_pairs(self, sources: list[str], candidates: list[str]) -> list[float]:
        pairs = list(zip(sources, candidates))
        missing = [p for p in dict.fromkeys(pairs) if p not in self._scores]
        if missing:
            self._scores.update(zip(missing, self.corrector.score_pairs([p[0] for p in missing], [p[1] for p in missing])))
        return [self._scores[p] for p in pairs]


def _softmax(rows: list[tuple[str, float]]) -> list[dict]:
    """Gộp câu trùng, giữ thứ tự xuất hiện; xác suất chỉ để hiển thị."""
    m = max(s for _, s in rows)
    probs: dict[str, float] = {}
    for text, s in rows:
        probs[text] = probs.get(text, 0.0) + math.exp(s - m)
    z = sum(probs.values())
    return [{"text": t, "prob": p / z} for t, p in probs.items()]


class HybridCorrector:
    def __init__(self, mode: str, lex: Lexicon | None = None, model=None, k: int = 8, n: int = 8, alpha: float = 1.0,
                 beta: float = 1.0, penalty: float = -8.0, guard_k: int | None = None):
        if mode not in {"model", "lexicon", "guard", "rerank"}:
            raise ValueError(mode)
        self.mode, self.lex, self.model = mode, lex, model
        self.k, self.n, self.alpha, self.beta, self.penalty, self.guard_k = k, n, alpha, beta, penalty, guard_k

    # ------------------------------------------------------------------ đối chiếu với từ điển
    def _allowed(self, raw: str, restrict: bool) -> set[str]:
        return {c for c, _ in self.lex.options(raw, self.guard_k, restrict)}

    def _segment(self, src: list[tuple[str, bool]], rep: list[str], allow=None) -> float | None:
        """Chia `rep` thành len(src) đoạn, mỗi đoạn phải là ứng viên của từ nguồn tương ứng.
        Trả tổng điểm kênh nhiễu tốt nhất, None nếu không chia được."""
        if not src:
            return 0.0 if not rep else None
        (raw, restrict), rest = src[0], src[1:]
        channel = self.lex.channel(raw, restrict)
        ok = allow(raw, restrict) if allow else channel
        best = None
        for cut in range(1, len(rep) - len(rest) + 1):
            head = " ".join(rep[:cut])
            if head in ok:
                tail = self._segment(rest, rep[cut:], allow)
                if tail is not None and (best is None or channel[head] + tail > best):
                    best = channel[head] + tail
        return best

    def guard(self, source: str, pred: str) -> str:
        """Trả về từ gốc ở những phép sửa của mô hình mà từ điển không xem là ứng viên."""
        source, pred = normalize_text(source), normalize_text(pred)
        s = list(SPAN.finditer(source))
        p = list(SPAN.finditer(pred))
        low_s = [m.group().lower() for m in s]
        low_p = [m.group().lower() for m in p]
        out = pred
        ops = SequenceMatcher(a=low_s, b=low_p, autojunk=False).get_opcodes()
        for tag, i1, i2, j1, j2 in reversed(ops):
            if tag == "equal":
                continue
            src_text = source[s[i1].start():s[i2 - 1].end()] if i2 > i1 else ""
            if j2 > j1:
                a, b = p[j1].start(), p[j2 - 1].end()
            else:
                a = b = p[j1].start() if j1 < len(p) else len(pred)
            if i1 == i2 or j1 == j2:  # chèn hoặc xóa: dấu câu thì giữ theo mô hình, từ thì trả về như nguồn
                if not any(_is_word(t) for t in (low_s[i1:i2] or low_p[j1:j2])):
                    continue
                out = f"{out[:a]} {src_text} {out[b:]}"
                continue
            src = [(s[i].group(), i > 0 and s[i].group()[:1].isupper()) for i in range(i1, i2)]
            if i2 - i1 == j2 - j1:  # thay từng từ: chỉ trả lại những từ không hợp lệ, giữ các từ còn lại
                for off in range(i2 - i1 - 1, -1, -1):
                    if low_p[j1 + off] not in self._allowed(*src[off]):
                        m = p[j1 + off]
                        out = out[:m.start()] + src[off][0] + out[m.end():]
            elif self._segment(src, low_p[j1:j2], self._allowed) is None:
                out = out[:a] + src_text + out[b:]
        return normalize_text(out)

    def prior(self, source: str, cand: str) -> float:
        """Tổng điểm kênh nhiễu của các phép biến nguồn thành ứng viên; phép ngoài từ điển bị trừ `penalty`."""
        s, c = [m.group() for m in SPAN.finditer(source)], [m.group().lower() for m in SPAN.finditer(cand)]
        low = [x.lower() for x in s]
        total = 0.0
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=low, b=c, autojunk=False).get_opcodes():
            if tag == "equal":
                total += sum(self.lex.channel(x)[x.lower()] for x in s[i1:i2])
            elif i1 == i2 or j1 == j2:
                total += self.penalty * max(i2 - i1, j2 - j1)
            else:
                v = self._segment([(x, False) for x in s[i1:i2]], c[j1:j2])
                total += v if v is not None else self.penalty * max(i2 - i1, j2 - j1)
        return total

    # ------------------------------------------------------------------ dự đoán
    def nbest(self, texts: list[str]) -> list[list[dict]]:
        if self.mode == "model":
            return self.model.nbest(texts)
        if self.mode == "lexicon":
            return [_softmax([(p.text, p.score) for p in self.lex.best_paths(t, self.k, self.n, self.alpha)]) for t in texts]
        alts = self.model.nbest(texts)
        if self.mode == "guard":
            return [_softmax([(self.guard(t, a["text"]), math.log(max(a["prob"], 1e-12))) for a in al])
                    for t, al in zip(texts, alts)]
        pools = []
        for t, al in zip(texts, alts):
            pool = dict.fromkeys([normalize_text(t)] + [a["text"] for a in al]
                                 + [p.text for p in self.lex.best_paths(t, self.k, self.n, self.alpha)])
            pools.append(list(pool))
        flat_s = [t for t, pool in zip(texts, pools) for _ in pool]
        flat_c = [c for pool in pools for c in pool]
        scores = iter(self.model.score_pairs(flat_s, flat_c))
        out = []
        for t, pool in zip(texts, pools):
            rows = [(c, next(scores) + self.beta * self.prior(t, c)) for c in pool]
            rows.sort(key=lambda x: -x[1])
            out.append(_softmax(rows))
        return out

    def __call__(self, texts: list[str]) -> list[str]:
        return [a[0]["text"] for a in self.nbest(texts)]
