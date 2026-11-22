"""Gợi ý sau mỗi từ: giữ trạng thái câu đang gõ, không phụ thuộc giao diện.

- Chỉ xử lý từ đã gõ xong; từ đang gõ dở không bị đụng tới.
- Tầng nhanh (mỗi từ): ứng viên từ điển + bigram, dùng ngữ cảnh cả hai phía khi đã có từ sau.
- Tầng chậm (`refine`, khi người dùng dừng tay): mô hình ViT5 chấm lại các từ chưa khóa.
- Chỉ tự đổi trường hợp chắc chắn (Telex giải mã ra đúng một từ có thật, từ gốc không có trong từ điển). Còn lại giữ chữ
  gốc, gạch chân và đưa lựa chọn. Từ đã khóa (người dùng chọn, hoặc đã cách từ đang gõ `lock_after` từ) không đổi nữa.
"""
from dataclasses import dataclass, field

from src.lexicon.build import START
from src.lexicon.candidates import SPAN, Lexicon, match_case
from src.lexicon.telex import decode

END = {".", "!", "?", "…"}  # dấu kết thúc câu: gõ xong là danh sách gợi ý chuyển sang câu mới


@dataclass
class Word:
    raw: str
    start: int
    end: int
    restrict: bool
    shown: str = ""                                  # chữ đang hiển thị trong câu
    options: list[tuple[str, float]] = field(default_factory=list)  # (chữ thường, điểm), điểm cao trước
    auto: bool = False                               # đã tự đổi bằng Telex
    locked: bool = False
    chosen: str | None = None                        # chữ người dùng chọn

    @property
    def best(self) -> str:
        return self.chosen or (self.options[0][0] if self.options else self.raw.lower())


class Session:
    def __init__(self, lex: Lexicon, k: int = 8, top: int = 3, alpha: float = 1.0, beta: float = 1.0, lock_after: int = 2,
                 min_margin: float = 2.0):
        self.lex, self.k, self.top, self.alpha, self.beta, self.lock_after, self.min_margin = lex, k, top, alpha, beta, lock_after, min_margin
        self.words: list[Word] = []
        self.text_now = ""     # chữ trong ô nhập lúc `sync` gần nhất
        self.best_changes = 0  # số lần gợi ý đầu của một từ bị đổi sau khi đã hiện, để đo độ ổn định

    # ------------------------------------------------------------------ cập nhật theo chữ người dùng gõ
    def sync(self, text: str) -> None:
        """Đồng bộ với toàn bộ nội dung ô nhập: giữ trạng thái các từ không đổi, xử lý lại từ chỗ khác đầu tiên.
        Từ cuối chưa có khoảng trắng hoặc dấu câu theo sau được coi là đang gõ dở."""
        self.text_now = text
        spans = list(SPAN.finditer(text))
        if spans and spans[-1].end() == len(text) and spans[-1].group()[-1:].isalnum():
            spans = spans[:-1]
        tokens = [m.group() for m in spans]
        keep = pos = 0
        for w in self.words:
            shown = SPAN.findall(w.shown)  # phương án đã chọn có thể nhiều từ ("không có gì")
            if tokens[pos:pos + len(shown)] == shown:
                n = len(shown)
            elif pos < len(tokens) and tokens[pos] == w.raw:
                n = 1
            else:
                break
            w.start, w.end = spans[pos].start(), spans[pos + n - 1].end()
            pos += n
            keep += 1
        del self.words[keep:]
        for m in spans[pos:]:
            self._push(m.group(), m.start(), m.end())
        self._apply_locks()

    def _left(self, i: int) -> str:
        if i == 0:
            return START
        return self.words[i - 1].best.split()[-1]

    def _rank(self, i: int) -> None:
        w = self.words[i]
        if w.locked:
            return
        channel = self.lex.options(w.raw, self.k, w.restrict)
        left = self._left(i)
        right = self.words[i + 1].best.split()[0] if i + 1 < len(self.words) else None

        def score(item):
            words = item[0].split()
            s, p = self.alpha * item[1], left
            for x in words:
                s += self.lex.lm(p, x)
                p = x
            return s + (self.lex.lm(p, right) if right else 0.0)

        ranked = sorted(((c, score((c, ch))) for c, ch in channel), key=lambda x: -x[1])
        self._set_options(w, ranked)

    def _set_options(self, w: Word, ranked: list[tuple[str, float]]) -> None:
        if w.options and w.options[0][0] != ranked[0][0]:
            self.best_changes += 1
        w.options = ranked

    def _push(self, raw: str, start: int, end: int) -> None:
        # viết hoa giữa câu có thể là tên riêng; viết hoa đầu câu (sau . ! ?) thì không
        mid = bool(self.words) and self.words[-1].raw not in END
        w = Word(raw, start, end, restrict=mid and raw[:1].isupper(), shown=raw)
        self.words.append(w)
        self._rank(len(self.words) - 1)
        if len(self.words) > 1:
            self._rank(len(self.words) - 2)  # có từ sau rồi thì xếp lại từ trước
        t = raw.lower()
        if t not in self.lex.vocab and t not in self.lex.mapping:
            forms = [f for f in decode(t) if f in self.lex.vocab]
            if len(forms) == 1:
                w.shown, w.auto = match_case(raw, forms[0]), True
                w.options = [(forms[0], 0.0)] + [o for o in w.options if o[0] != forms[0]]

    def _apply_locks(self) -> None:
        for w in self.words[:-self.lock_after] if self.lock_after else self.words:
            w.locked = True

    def choose(self, i: int, option: str) -> None:
        """Người dùng chọn một phương án: từ này khóa lại, chữ hiển thị đổi theo."""
        w = self.words[i]
        w.chosen, w.locked = option, True
        w.shown = match_case(w.raw, option)
        w.options = [(option, 0.0)] + [o for o in w.options if o[0] != option]

    # ------------------------------------------------------------------ tầng ViT5
    def refine_requests(self) -> list[tuple[int, str, list[str], list[float]]]:
        """Các từ chưa khóa cần mô hình chấm: (vị trí, câu nguồn, các câu ứng viên, điểm từ điển).
        Mô hình chỉ thấy câu chứa từ đó (tách theo . ! ?), không phải cả tin nhắn."""
        out = []
        for i0, i1 in self.segments():
            seg = self.words[i0:i1]
            src = " ".join(w.raw for w in seg)
            for j, w in enumerate(seg):
                if w.locked or len(w.options) < 2:
                    continue
                base = [x.best for x in seg]
                cands, priors = [], []
                for c, s in w.options[:self.k]:
                    base[j] = c
                    cands.append(" ".join(base))
                    priors.append(s)
                out.append((i0 + j, src, cands, priors))
        return out

    def apply_refine(self, requests, scores: list[list[float]]) -> None:
        for (i, _, _, priors), row in zip(requests, scores):
            w = self.words[i]
            ranked = [(w.options[j][0], row[j] + self.beta * priors[j]) for j in range(len(row))]
            ranked.sort(key=lambda x: -x[1])
            self._set_options(w, ranked + w.options[len(row):])

    def refine(self, scorer) -> None:
        """Chạy đồng bộ tầng ViT5 (`scorer` = Corrector.score_pairs hoặc CachedModel.score_pairs)."""
        reqs = self.refine_requests()
        if not reqs:
            return
        flat = scorer([r[1] for r in reqs for _ in r[2]], [c for r in reqs for c in r[2]])
        scores, pos = [], 0
        for r in reqs:
            scores.append(flat[pos:pos + len(r[2])])
            pos += len(r[2])
        self.apply_refine(reqs, scores)

    # ------------------------------------------------------------------ kết quả
    def uncertain(self, w: Word) -> bool:
        """Cần gạch chân: gợi ý đầu khác chữ đang hiện, hoặc phương án hai sát nút (chỉ với từ chưa khóa).
        Khóa nghĩa là không xếp lại nữa; từ khóa mà gợi ý đầu vẫn khác chữ đang hiện thì người dùng vẫn phải sửa được."""
        if w.chosen or len(w.options) < 2:
            return False
        if w.options[0][0] != w.shown.lower():
            return True
        return not w.locked and w.options[0][1] - w.options[1][1] < self.min_margin and any(c.isalpha() for c in w.raw)

    def state(self) -> list[dict]:
        return [{"i": i, "start": w.start, "end": w.end, "raw": w.raw, "shown": w.shown, "locked": w.locked, "auto": w.auto,
                 "uncertain": self.uncertain(w), "options": [match_case(w.raw, c) for c, _ in w.options[:self.top]]}
                for i, w in enumerate(self.words)]

    def text(self, accept_best: bool = False) -> str:
        """Câu hiện tại; accept_best=True: như thể người dùng nhận mọi gợi ý đầu."""
        return " ".join(match_case(w.raw, w.best) if accept_best else w.shown for w in self.words)

    # ------------------------------------------------------------------ cả câu cho danh sách gợi ý
    def _is_end(self, w: Word) -> bool:
        t = self.text_now
        between_digits = t[w.start - 1:w.start].isdigit() and t[w.end:w.end + 1].isdigit()  # "3.5" không phải hết câu
        return w.raw in END and not between_digits

    def segments(self) -> list[tuple[int, int]]:
        """Các câu trong tin nhắn dạng khoảng chỉ số từ [đầu, cuối); dấu kết thúc thuộc câu trước nó.
        Luôn có một câu cuối (có thể rỗng: vừa gõ dấu chấm, chưa xong từ nào của câu mới)."""
        out, i0 = [], 0
        for i, w in enumerate(self.words):
            if self._is_end(w):
                out.append((i0, i + 1))
                i0 = i + 1
        out.append((i0, len(self.words)))
        return out

    def active(self, caret: int | None = None) -> tuple[int, int]:
        """Câu chứa con trỏ (mặc định câu cuối, nơi đang gõ)."""
        segs = self.segments()
        if caret is None:
            return segs[-1]
        found = segs[0]
        for i0, i1 in segs:
            start = self.words[i0].start if i0 < len(self.words) else (self.words[-1].end if self.words else 0)
            if start <= caret:
                found = (i0, i1)
        return found

    def sentences(self, text: str | None = None, n: int = 3, caret: int | None = None) -> list[dict]:
        """Tối đa n phương án cho CÂU chứa con trỏ, để người dùng bấm chọn: {"text", "picks", "start", "end", "first"}.
        "text" thay cho đoạn [start, end) của ô nhập; "first" là chỉ số từ đầu câu. Từ chưa chắc có tối đa `top` phương
        án, các từ khác giữ phương án đầu; xếp theo tổng độ lệch điểm so với phương án đầu của từng từ. Chữ giữa các từ và
        từ đang gõ dở giữ nguyên như trong ô nhập. Câu chưa có từ nào gõ xong thì không có phương án."""
        text = self.text_now if text is None else text
        i0, i1 = self.active(caret)
        if i0 == i1:
            return []
        seg = self.words[i0:i1]
        start = seg[0].start
        end = len(text) if i1 == len(self.words) else seg[-1].end  # câu cuối gồm cả từ đang gõ dở
        beams: list[tuple[float, list[str]]] = [(0.0, [])]
        for w in seg:
            if w.chosen:
                alts = [(w.chosen, 0.0)]
            elif self.uncertain(w):
                head = w.options[:self.top]
                alts = [(c, head[0][1] - s) for c, s in head]
            else:
                alts = [(w.shown.lower(), 0.0)]
            beams = sorted(((d + dd, picks + [c]) for d, picks in beams for c, dd in alts), key=lambda x: x[0])[:n * 2]
        out, seen = [], set()
        for _, picks in beams:
            sent = self.render(text, seg, picks, start, end)
            if sent not in seen:
                seen.add(sent)
                out.append({"text": sent, "picks": picks, "start": start, "end": end, "first": i0})
            if len(out) == n:
                break
        return out

    @staticmethod
    def render(text: str, words: list[Word], picks: list[str], start: int, end: int) -> str:
        pieces, last = [], start
        for w, c in zip(words, picks):
            pieces += [text[last:w.start], match_case(w.raw, c)]
            last = w.end
        return "".join(pieces) + text[last:end]

    def pick(self, picks: list[str], first: int = 0) -> list[int]:
        """Người dùng bấm một câu trong danh sách (các từ từ vị trí `first`): chọn phương án cho từ chưa chắc hoặc khác chữ
        đang hiện. Trả vị trí các từ đã chọn."""
        changed = [first + j for j, (w, p) in enumerate(zip(self.words[first:], picks))
                   if not w.chosen and (p != w.shown.lower() or self.uncertain(w))]
        for i in changed:
            self.choose(i, picks[i - first])
        return changed
