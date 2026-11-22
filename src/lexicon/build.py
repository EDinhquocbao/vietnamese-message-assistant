"""Dựng từ điển cho bước sinh ứng viên -> data/processed/lexicon/lexicon.json

Nguồn (data/raw/lexicon/, không đưa lên repo):
- Viet74K.txt (github.com/duyet/vietnamese-wordlist, GPL-2.0): âm tiết hợp lệ.
- vi-nsw-dict.json (github.com/AnhHoang0529/vn-nsw-dictionary, không ghi giấy phép): viết tắt/từ không chuẩn.
- data/processed/correction/train.jsonl: bảng "từ gốc -> từ đúng" kèm số lần và thống kê unigram/bigram.

CHỈ dùng tập train (dữ liệu thật, không có lỗi nhân tạo): val để chọn tham số, test để đánh giá.

Chạy:  python -m src.lexicon.build
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from src.utils.metrics import tokenize, word_edits

RAW = Path("data/raw/lexicon")
START = "<s>"
EXTRA_NSW = {"kcj": ["không có gì"]}  # viết tắt phổ biến mà cả hai nguồn trên đều thiếu


def extract_counts(sources: list[str], targets: list[str]) -> tuple[Counter, Counter, dict]:
    """(unigram, bigram câu chuẩn, bảng từ gốc -> {từ đúng: số lần}). Mọi thứ ở chữ thường."""
    uni, bi = Counter(), Counter()
    mapping: dict[str, Counter] = defaultdict(Counter)
    for src, tgt in zip(sources, targets):
        src, tgt = src.lower(), tgt.lower()
        toks = [START] + tokenize(tgt)
        uni.update(toks)
        bi.update(zip(toks, toks[1:]))
        src_toks, touched = tokenize(src), set()
        for i1, i2, rep in word_edits(src, tgt):
            touched.update(range(i1, i2))
            if i2 - i1 == 1 and rep:
                mapping[src_toks[i1]][" ".join(rep)] += 1
            elif i2 - i1 == len(rep):  # nhiều từ sai liền nhau, cùng số từ: ghép từng cặp ("ko di" -> "không đi")
                for off, word in enumerate(rep):
                    mapping[src_toks[i1 + off]][word] += 1
        for i, w in enumerate(src_toks):
            if i not in touched:
                mapping[w][w] += 1
    return uni, bi, mapping


def load_syllables(path: Path = RAW / "Viet74K.txt") -> set[str]:
    out = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if "-" in line:  # phiên âm tiếng nước ngoài kiểu "a-ba-giua"
            continue
        out.update(t for t in line.lower().split() if t.isalpha())
    return out


def load_nsw(path: Path = RAW / "vi-nsw-dict.json") -> dict[str, list[str]]:
    """Chỉ giữ khóa một từ có chữ cái; giá trị viết thường."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    out = {k.lower(): [v.lower() for v in vals if v.strip()] for k, vals in raw.items()
           if len(k.split()) == 1 and any(c.isalpha() for c in k)}
    return out | EXTRA_NSW


def build(train: str = "data/processed/correction/train.jsonl") -> dict:
    df = pd.read_json(train, lines=True)
    uni, bi, mapping = extract_counts(df["source"].tolist(), df["target"].tolist())
    return {
        "unigram": dict(uni),
        "bigram": {f"{a}\t{b}": c for (a, b), c in bi.items()},
        "mapping": {w: dict(c) for w, c in mapping.items() if set(c) != {w}},  # từ chỉ luôn giữ nguyên thì không cần lưu
        "syllables": sorted(load_syllables()),
        "nsw": load_nsw(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/processed/lexicon/lexicon.json")
    args = ap.parse_args()
    lex = build()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(lex, ensure_ascii=False), encoding="utf-8")
    print({k: len(v) for k, v in lex.items()}, f"-> {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
