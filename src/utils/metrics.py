"""Chỉ số đánh giá cho sửa lỗi và diễn đạt lại.

Mọi chỉ số mức từ dùng cùng một cách tách từ `tokenize` (tách dấu câu khỏi chữ),
để "nhau." và "nhau" không bị tính là hai từ khác nhau.
"""
import math
import re
from collections import Counter
from difflib import SequenceMatcher

import jiwer

_TOKEN = re.compile(r"\w+|[^\w\s]")


def tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text)


def _joined(texts):
    return [" ".join(tokenize(t)) or "<empty>" for t in texts]


# ---------------------------------------------------------------- sửa lỗi

def cer(preds, refs) -> float:
    return jiwer.cer(list(refs), list(preds))


def wer(preds, refs) -> float:
    return jiwer.wer(_joined(refs), _joined(preds))


def exact_match(preds, refs) -> float:
    pairs = list(zip(preds, refs))
    return sum(p == r for p, r in pairs) / max(len(pairs), 1)


def word_edits(source: str, target: str) -> set[tuple]:
    """Tập các phép sửa mức từ biến source thành target: (vị trí đầu, vị trí cuối, từ thay thế)."""
    s, t = tokenize(source), tokenize(target)
    ops = SequenceMatcher(a=s, b=t, autojunk=False).get_opcodes()
    return {(i1, i2, tuple(t[j1:j2])) for tag, i1, i2, j1, j2 in ops if tag != "equal"}


def correction_prf(sources, preds, refs, beta: float = 0.5) -> dict:
    """Precision/Recall/F_beta trên các phép sửa (kiểu M2/ERRANT, đơn giản hóa).

    - TP: phép sửa mô hình làm trùng với phép sửa chuẩn.
    - P thấp = mô hình sửa sai/sửa thừa; R thấp = bỏ sót lỗi.
    F0.5 ưu tiên precision, vì sửa sai câu của người dùng tệ hơn bỏ sót một lỗi.
    """
    tp = fp = fn = 0
    for s, p, r in zip(sources, preds, refs):
        gold, hyp = word_edits(s, r), word_edits(s, p)
        tp += len(gold & hyp)
        fp += len(hyp - gold)
        fn += len(gold - hyp)
    prec = tp / (tp + fp) if tp + fp else 1.0  # không sửa gì -> không sửa sai
    rec = tp / (tp + fn) if tp + fn else 1.0
    b2 = beta * beta
    f = (1 + b2) * prec * rec / (b2 * prec + rec) if prec + rec else 0.0
    return {"precision": prec, "recall": rec, f"f{beta}": f, "tp": tp, "fp": fp, "fn": fn}


def overcorrection_rate(clean_inputs, preds) -> float:
    """Tỉ lệ câu vốn đã đúng nhưng bị mô hình thay đổi."""
    pairs = list(zip(clean_inputs, preds))
    return sum(c != p for c, p in pairs) / max(len(pairs), 1)


def correction_report(sources, preds, refs) -> dict:
    return {
        "n": len(refs),
        "cer": cer(preds, refs),
        "wer": wer(preds, refs),
        "exact_match": exact_match(preds, refs),
        **correction_prf(sources, preds, refs),
    }


# ---------------------------------------------------------------- diễn đạt lại

def _ngrams(tokens, n):
    return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))


def corpus_bleu(hyps, refs_list, max_n: int = 4) -> float:
    """BLEU mức corpus (0-100), hỗ trợ nhiều tham chiếu mỗi câu. refs_list[i] là list các câu tham chiếu."""
    match, total = [0] * max_n, [0] * max_n
    hyp_len = ref_len = 0
    for hyp, refs in zip(hyps, refs_list):
        h = tokenize(hyp)
        rs = [tokenize(r) for r in refs]
        hyp_len += len(h)
        ref_len += min((abs(len(r) - len(h)), len(r)) for r in rs)[1]  # độ dài tham chiếu gần nhất
        for n in range(1, max_n + 1):
            hc = _ngrams(h, n)
            max_ref = Counter()
            for r in rs:
                max_ref |= _ngrams(r, n)
            match[n - 1] += sum(min(c, max_ref[g]) for g, c in hc.items())
            total[n - 1] += max(len(h) - n + 1, 0)
    if hyp_len == 0 or min(match) == 0:
        return 0.0
    log_p = sum(math.log(m / t) for m, t in zip(match, total)) / max_n
    bp = 1.0 if hyp_len > ref_len else math.exp(1 - ref_len / hyp_len)
    return 100 * bp * math.exp(log_p)


def distinct_n(texts, n: int = 2) -> float:
    """Tỉ lệ n-gram khác nhau trên tổng n-gram: đo độ đa dạng giữa các gợi ý."""
    grams = Counter()
    for t in texts:
        grams.update(_ngrams(tokenize(t), n))
    return len(grams) / max(sum(grams.values()), 1)


def paraphrase_report(sources, preds, refs_list, alpha: float = 0.8) -> dict:
    """Chỉ số tự động cho diễn đạt lại (chưa gồm độ tương đồng ngữ nghĩa, cần mô hình embedding).

    - bleu_ref: giống câu tham chiếu (cao = tốt)
    - self_bleu: giống câu gốc (thấp = diễn đạt khác đi nhiều)
    - ibleu = alpha*bleu_ref - (1-alpha)*self_bleu: phạt việc chép lại câu gốc
    """
    bleu_ref = corpus_bleu(preds, refs_list)
    self_bleu = corpus_bleu(preds, [[s] for s in sources])
    pairs = list(zip(sources, preds))
    return {
        "n": len(pairs),
        "bleu_ref": bleu_ref,
        "self_bleu": self_bleu,
        "ibleu": alpha * bleu_ref - (1 - alpha) * self_bleu,
        "copy_rate": sum(s == p for s, p in pairs) / max(len(pairs), 1),
        "distinct_2": distinct_n(preds, 2),
    }
