"""Sửa lỗi bằng mô hình đã fine-tune.

Ký tự ngoài từ điển của ViT5 ($, “ ”, –, emoji, "=))"...) bị mã hóa thành <unk>, nên mô hình
không thể sinh lại chúng. Ta ghi lại đoạn gốc ứng với từng <unk> trong câu nguồn (qua offset)
rồi điền lại theo thứ tự vào câu sinh ra.

Dùng như hàm cho src.correction.evaluate:
    corrector = Corrector("models/correction/vit5-base")
    corrector(["ko bít dc ko"])  -> ["không biết được không"]
Chạy:  python -m src.correction.predict --model models/correction/vit5-base "Mai mình đi hộp lúc 8h nhé"
"""
import argparse
import sys

import torch
from transformers import AutoModelForSeq2SeqLM

from src.correction.dataset import load_tokenizer
from src.utils.text_utils import load_config, normalize_text


def restore_unknown(text: str, spans: list[str], unk: str = "<unk>") -> str:
    """Thay lần lượt từng `unk` trong `text` bằng đoạn gốc; thừa <unk> thì bỏ."""
    parts = text.split(unk)
    out = parts[0]
    for i, part in enumerate(parts[1:]):
        out += (spans[i] if i < len(spans) else "") + part
    return normalize_text(out)


class Corrector:
    def __init__(self, model_dir: str, num_beams: int = 4, batch_size: int = 32,
                 max_new_tokens: int = 160, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = load_tokenizer(model_dir)
        dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_dir, dtype=dtype).to(self.device).eval()
        self.num_beams, self.batch_size, self.max_new_tokens = num_beams, batch_size, max_new_tokens

    def _unk_spans(self, text: str, ids: list[int], offsets: list[tuple[int, int]]) -> list[str]:
        return [text[a:b].strip() for i, (a, b) in zip(ids, offsets) if i == self.tok.unk_token_id]

    @torch.no_grad()
    def generate_many(self, texts: list[str], n: int = 1, **gen_kwargs) -> list[list[str]]:
        """Sinh `n` câu cho mỗi câu đầu vào (gen_kwargs truyền thẳng cho model.generate)."""
        texts = [normalize_text(t) for t in texts]
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))  # gom câu cùng độ dài, ít padding
        out = [[] for _ in texts]
        for k in range(0, len(order), self.batch_size):
            idx = order[k:k + self.batch_size]
            batch = [texts[i] for i in idx]
            enc = self.tok(batch, return_offsets_mapping=True, padding=True, return_tensors="pt")
            offsets = enc.pop("offset_mapping").tolist()
            gen = self.model.generate(**enc.to(self.device), num_return_sequences=n,
                                      max_new_tokens=self.max_new_tokens, **gen_kwargs)
            decoded = self.tok.batch_decode(gen, skip_special_tokens=False)
            for j, i in enumerate(idx):
                spans = self._unk_spans(batch[j], enc["input_ids"][j].tolist(), offsets[j])
                for d in decoded[j * n:(j + 1) * n]:
                    d = d.replace(self.tok.pad_token, "").replace(self.tok.eos_token, "")
                    out[i].append(restore_unknown(d, spans, self.tok.unk_token))
        return out

    def __call__(self, texts: list[str]) -> list[str]:
        return [c[0] for c in self.generate_many(texts, num_beams=self.num_beams)]


def from_config(model_dir: str | None = None, config: str = "configs/correction.yaml") -> Corrector:
    cfg = load_config(config)
    g = cfg["generate"]
    return Corrector(model_dir or cfg["output_dir"], num_beams=g["num_beams"],
                     batch_size=g["batch_size"], max_new_tokens=g["max_new_tokens"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("texts", nargs="*", help="câu cần sửa; bỏ trống thì đọc từng dòng từ stdin")
    ap.add_argument("--model", default=None, help="thư mục mô hình (mặc định output_dir trong config)")
    ap.add_argument("--config", default="configs/correction.yaml")
    args = ap.parse_args()
    corrector = from_config(args.model, args.config)
    texts = args.texts or [line for line in sys.stdin.read().splitlines() if line.strip()]
    for src, pred in zip(texts, corrector(texts)):
        print(f"{src}\n-> {pred}\n")


if __name__ == "__main__":
    main()
