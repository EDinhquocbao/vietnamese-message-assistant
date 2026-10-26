"""Sinh câu diễn đạt lại bằng mô hình đã fine-tune trên ViSP.

`candidates` sinh nhiều ứng viên (nửa từ beam search: sát nghĩa; nửa từ lấy mẫu nucleus: đa dạng),
bỏ câu trùng và câu chép nguyên đầu vào. Việc chọn 2-3 gợi ý cuối do src/pipeline/ranker.py làm.

Chạy:  python -m src.paraphrase.generate --model models/paraphrase/vit5-base "Bạn gửi file cho mình chưa?"
"""
import argparse
import sys

import torch

from src.correction.predict import Corrector
from src.utils.text_utils import load_config, normalize_text


def _key(text: str) -> str:
    """Khóa so trùng: bỏ khác biệt chữ hoa và dấu câu cuối câu."""
    return normalize_text(text).lower().rstrip(" .!?…")


def clean_candidate(source: str, text: str) -> str:
    """Sửa lỗi bề mặt hay gặp: ngoặc kép lẻ (học từ câu trích dẫn trong ViSP) và từ lặp liền nhau
    ("ạ ạ", "ơi ơi") mà câu gốc không có (giữ từ láy có sẵn như "sớm sớm")."""
    text = normalize_text(text)
    if text.count('"') % 2:
        text = text.replace('"', "")
    words, src = text.split(" "), f" {source.lower()} "
    core = [w.lower().rstrip(".,!?…") for w in words]
    # bỏ từ đứng trước trong cặp lặp, giữ từ sau để không mất dấu câu dính kèm ("ạ ạ." -> "ạ.")
    kept = [w for i, w in enumerate(words)
            if i + 1 == len(words) or core[i] != core[i + 1]
            or w.lower() != core[i]  # từ trước có dấu câu dính kèm ("ơi, ơi") -> giữ
            or f" {core[i]} {core[i]} " in src]
    return normalize_text(" ".join(kept))


def dedupe_candidates(source: str, candidates: list[str]) -> list[str]:
    """Giữ thứ tự, bỏ câu rỗng, câu trùng nhau và câu chỉ chép lại `source`."""
    seen, out = {_key(source)}, []
    for c in candidates:
        c = clean_candidate(source, c)
        k = _key(c)
        if k and k not in seen:
            seen.add(k)
            out.append(c)
    return out


class Paraphraser(Corrector):
    def __init__(self, model_dir: str, num_candidates: int = 8, num_beams: int = 8, top_p: float = 0.9,
                 temperature: float = 1.0, batch_size: int = 16, max_new_tokens: int = 160,
                 seed: int = 42, device: str | None = None):
        super().__init__(model_dir, num_beams=num_beams, batch_size=batch_size,
                         max_new_tokens=max_new_tokens, device=device)
        self.num_candidates, self.top_p, self.temperature, self.seed = num_candidates, top_p, temperature, seed

    def candidates(self, texts: list[str]) -> list[list[str]]:
        n_beam = self.num_candidates // 2
        beams = self.generate_many(texts, n_beam, num_beams=max(self.num_beams, n_beam))
        torch.manual_seed(self.seed)  # lấy mẫu tái lập được
        samples = self.generate_many(texts, self.num_candidates - n_beam, do_sample=True,
                                     top_p=self.top_p, temperature=self.temperature)
        return [dedupe_candidates(t, b + s) for t, b, s in zip(texts, beams, samples)]

    def __call__(self, texts: list[str]) -> list[str]:
        """Một câu mỗi đầu vào: ứng viên beam tốt nhất mà không chép lại câu gốc (dùng để đánh giá)."""
        beams = self.generate_many(texts, 4, num_beams=self.num_beams)
        out = []
        for t, cs in zip(texts, beams):
            kept = dedupe_candidates(t, cs)
            out.append(kept[0] if kept else cs[0])
        return out


def from_config(model_dir: str | None = None, config: str = "configs/paraphrase.yaml") -> Paraphraser:
    cfg = load_config(config)
    g = cfg["generate"]
    return Paraphraser(model_dir or cfg["output_dir"], num_candidates=g["num_candidates"],
                       num_beams=g["num_beams"], top_p=g["top_p"], temperature=g["temperature"],
                       batch_size=g["batch_size"], max_new_tokens=g["max_new_tokens"], seed=cfg["seed"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("texts", nargs="*", help="câu cần diễn đạt lại; bỏ trống thì đọc từ stdin")
    ap.add_argument("--model", default=None)
    ap.add_argument("--config", default="configs/paraphrase.yaml")
    args = ap.parse_args()
    para = from_config(args.model, args.config)
    texts = args.texts or [line for line in sys.stdin.read().splitlines() if line.strip()]
    for src, cands in zip(texts, para.candidates(texts)):
        print(src)
        for c in cands:
            print(f"  - {c}")
        print()


if __name__ == "__main__":
    main()
