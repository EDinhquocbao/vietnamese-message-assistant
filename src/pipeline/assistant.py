"""Pipeline hai bước: sửa lỗi rồi gợi ý 2-3 cách diễn đạt lại.

Diễn đạt lại chạy trên câu ĐÃ SỬA (mô hình ViSP học trên văn bản chuẩn, không quen viết tắt/không dấu),
và bộ xếp hạng so ứng viên với câu đã sửa.

Chạy:  python -m src.pipeline.assistant "mai di hoc ko" "Em xin phép nghỉ học hôm nay vì em bị ốm ạ"
"""
import argparse
import json

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


class Assistant:
    def __init__(self, corrector, paraphraser, ranker: Ranker):
        self.corrector, self.paraphraser, self.ranker = corrector, paraphraser, ranker

    def run_batch(self, texts: list[str]) -> list[dict]:
        corrected = self.corrector(texts)
        all_cands = self.paraphraser.candidates(corrected)
        out = []
        for src, cor, cands in zip(texts, corrected, all_cands):
            rows = self.ranker.score_all(cor, cands)
            out.append({
                "input": src,
                "corrected": cor,
                "edits": describe_edits(src, cor),
                "suggestions": self.ranker.select(rows),
                "candidates": rows,  # mọi ứng viên kèm lý do bị loại, để xem từng bước
            })
        return out

    def run(self, text: str) -> dict:
        return self.run_batch([text])[0]


def from_config(config: str = "configs/pipeline.yaml") -> Assistant:
    cfg = load_config(config)
    return Assistant(load_corrector(config=cfg["correction_config"]),
                     load_paraphraser(config=cfg["paraphrase_config"]),
                     Ranker(**cfg["ranker"]))


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
        for i, s in enumerate(r["suggestions"], 1):
            print(f"  Gợi ý {i}: {s['text']}  (giống nghĩa {s['similarity']:.2f})")
        print()


if __name__ == "__main__":
    main()
