"""Pipeline hai bước: sửa lỗi rồi gợi ý 2-3 cách diễn đạt lại.

Diễn đạt lại chạy trên câu ĐÃ SỬA (mô hình ViSP học trên văn bản chuẩn, không quen viết tắt/không dấu),
và bộ xếp hạng so ứng viên với câu đã sửa. Nếu câu đã sửa vẫn còn từ lạ (không có trong từ điển lấy từ
câu chuẩn của tập train, vd "nahu"), các gợi ý sinh ra gần như luôn vô nghĩa nên không hiển thị.

Chạy:  python -m src.pipeline.assistant "mai di hoc ko" "Em xin phép nghỉ học hôm nay vì em bị ốm ạ"
"""
import argparse
import json
from collections import Counter

import pandas as pd

from src.correction.predict import from_config as load_corrector
from src.paraphrase.generate import from_config as load_paraphraser
from src.pipeline.ranker import Ranker
from src.utils.metrics import tokenize, word_edits
from src.utils.text_utils import load_config


def describe_edits(source: str, corrected: str) -> list[dict]:
    """Các chỗ đã sửa mức từ, để demo tô sáng: [{"from": "hok", "to": "học"}]."""
    s = tokenize(source)
    return [{"from": " ".join(s[i1:i2]), "to": " ".join(rep)}
            for i1, i2, rep in sorted(word_edits(source, corrected))]


def load_vocab(sources: dict[str, list[str]], min_count: int = 2) -> set[str]:
    """Từ điển âm tiết (chữ thường) từ các cột câu chuẩn {file: [cột]}; bỏ từ xuất hiện < min_count lần."""
    counts = Counter()
    for path, columns in sources.items():
        df = pd.read_json(path, lines=True)
        for col in columns:
            for text in df[col]:
                counts.update(t.lower() for t in tokenize(text) if t.isalpha())
    return {w for w, c in counts.items() if c >= min_count}


def unknown_words(text: str, vocab: set[str]) -> list[str]:
    """Từ viết thường không có trong từ điển. Bỏ qua từ viết hoa (tên riêng), số và dấu câu."""
    return [t for t in tokenize(text) if t.isalpha() and t.islower() and t not in vocab]


def uncertain_words(alternatives: list[dict], min_prob: float = 0.1) -> list[dict]:
    """Từ của phương án tốt nhất mà một phương án khác (xác suất >= min_prob) sửa khác đi.
    Vd ["ngày mai...", "người yêu mai..."] -> [{"span": "ngày", "options": ["người yêu"]}]."""
    best = alternatives[0]["text"]
    tokens = tokenize(best)
    found: dict[str, list[str]] = {}
    for alt in alternatives[1:]:
        if alt["prob"] < min_prob:
            continue
        for i1, i2, rep in sorted(word_edits(best, alt["text"])):
            if i1 == i2:  # phương án khác chỉ chèn thêm từ, không có từ nào của câu tốt nhất để gạch chân
                continue
            span, o = " ".join(tokens[i1:i2]), " ".join(rep)
            if o.lower() == span.lower():  # chỉ khác chữ hoa: không đáng hỏi người dùng
                continue
            opts = found.setdefault(span, [])
            if o not in opts:
                opts.append(o)
    return [{"span": s, "options": o} for s, o in found.items()]


class Assistant:
    def __init__(self, corrector, paraphraser, ranker: Ranker, vocab: set[str] | None = None):
        self.corrector, self.paraphraser, self.ranker = corrector, paraphraser, ranker
        self.vocab = vocab

    def run_batch(self, texts: list[str]) -> list[dict]:
        if hasattr(self.corrector, "nbest"):
            alternatives = self.corrector.nbest(texts)
        else:  # bộ sửa lỗi chỉ trả một câu (baseline, mô hình giả trong test)
            alternatives = [[{"text": c, "prob": 1.0}] for c in self.corrector(texts)]
        corrected = [a[0]["text"] for a in alternatives]
        all_cands = self.paraphraser.candidates(corrected)
        out = []
        for src, cor, cands, alts in zip(texts, corrected, all_cands, alternatives):
            rows = self.ranker.score_all(cor, cands)
            unknown = unknown_words(cor, self.vocab) if self.vocab else []
            out.append({
                "input": src,
                "corrected": cor,
                "edits": describe_edits(src, cor),
                "unknown_words": unknown,  # từ nghi còn lỗi sau khi sửa
                "alternatives": alts,      # các phương án sửa (N-best) kèm xác suất
                "uncertain": uncertain_words(alts),
                "suggestions": [] if unknown else self.ranker.select(rows),
                "candidates": rows,  # mọi ứng viên kèm lý do bị loại, để xem từng bước
            })
        return out

    def run(self, text: str) -> dict:
        return self.run_batch([text])[0]


def from_config(config: str = "configs/pipeline.yaml") -> Assistant:
    cfg = load_config(config)
    vocab = load_vocab(cfg["vocab"]["sources"], cfg["vocab"]["min_count"]) if cfg.get("vocab") else None
    return Assistant(load_corrector(config=cfg["correction_config"]),
                     load_paraphraser(config=cfg["paraphrase_config"]),
                     Ranker(**cfg["ranker"]), vocab=vocab)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("texts", nargs="+")
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--json", action="store_true", help="in toàn bộ kết quả dạng JSON")
    args = ap.parse_args()
    for r in from_config(args.config).run_batch(args.texts):
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
            continue
        print(f"Đầu vào : {r['input']}\nĐã sửa  : {r['corrected']}")
        if r["unknown_words"]:
            print(f"  Nghi còn lỗi: {', '.join(r['unknown_words'])} (không đưa gợi ý)")
        for i, s in enumerate(r["suggestions"], 1):
            print(f"  Gợi ý {i}: {s['text']}  (giống nghĩa {s['similarity']:.2f})")
        print()


if __name__ == "__main__":
    main()
