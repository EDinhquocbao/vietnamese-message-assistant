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
import math
import re
import sys
from pathlib import Path

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


_SYMBOL_RUN = re.compile(r"([^\w\s])\1{2,}")  # một ký hiệu lặp >= 3 lần: "))))", "!!!"


def restore_symbols(source: str, pred: str) -> str:
    """Trả lại ký hiệu mà tokenizer chuẩn hóa mất: "…" bị đổi thành "...", và độ dài chuỗi ký hiệu
    lặp ("=))))") mà mô hình hay sinh dài/ngắn hơn câu gốc. Chuỗi lặp được thay theo thứ tự xuất hiện."""
    if "…" in source and "..." not in source:
        pred = pred.replace("...", "…")
    runs = iter(m.group() for m in _SYMBOL_RUN.finditer(source))

    def fix(m):
        r = next(runs, None)
        return r if r is not None and r[0] == m.group()[0] else m.group()

    return _SYMBOL_RUN.sub(fix, pred)


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
    def generate_many(self, texts: list[str], n: int = 1, with_scores: bool = False, **gen_kwargs) -> list[list]:
        """Sinh `n` câu cho mỗi câu đầu vào (gen_kwargs truyền thẳng cho model.generate).
        with_scores=True (chỉ với beam search): mỗi phần tử là (câu, log-prob của CẢ câu). Beam search trả
        log-prob chia cho độ dài; nhân lại với số token sinh ra, vì xác suất tính trên trung bình theo token
        gần như bằng nhau giữa các phương án (27/25/25/24%) nên không giúp người dùng chọn."""
        texts = [normalize_text(t) for t in texts]
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))  # gom câu cùng độ dài, ít padding
        out = [[] for _ in texts]
        for k in range(0, len(order), self.batch_size):
            idx = order[k:k + self.batch_size]
            batch = [texts[i] for i in idx]
            enc = self.tok(batch, return_offsets_mapping=True, padding=True, return_tensors="pt")
            offsets = enc.pop("offset_mapping").tolist()
            gen = self.model.generate(**enc.to(self.device), num_return_sequences=n,
                                      max_new_tokens=self.max_new_tokens, return_dict_in_generate=True,
                                      output_scores=with_scores, **gen_kwargs)
            decoded = self.tok.batch_decode(gen.sequences, skip_special_tokens=False)
            if with_scores:  # token đầu là decoder_start (= pad với T5) nên đếm token khác pad là số token sinh ra
                lengths = (gen.sequences != self.tok.pad_token_id).sum(-1)
                scores = (gen.sequences_scores * lengths).tolist()
            else:
                scores = [None] * len(decoded)
            for j, i in enumerate(idx):
                spans = self._unk_spans(batch[j], enc["input_ids"][j].tolist(), offsets[j])
                for d, sc in zip(decoded[j * n:(j + 1) * n], scores[j * n:(j + 1) * n]):
                    d = d.replace(self.tok.pad_token, "").replace(self.tok.eos_token, "")
                    text = restore_symbols(batch[j], restore_unknown(d, spans, self.tok.unk_token))
                    out[i].append((text, sc) if with_scores else text)
        return out

    def nbest(self, texts: list[str], n: int = 4) -> list[list[dict]]:
        """n phương án sửa tốt nhất mỗi câu, kèm xác suất tương đối (chuẩn hóa trong n phương án)."""
        rows = self.generate_many(texts, n, with_scores=True, num_beams=max(self.num_beams, n))
        return [merge_nbest(r) for r in rows]

    def __call__(self, texts: list[str]) -> list[str]:
        return [c[0] for c in self.generate_many(texts, num_beams=self.num_beams)]


def merge_nbest(cands: list[tuple[str, float]]) -> list[dict]:
    """Softmax trên log-prob của các phương án, gộp phương án trùng chữ. GIỮ thứ tự beam search (chuẩn hóa
    theo độ dài) để phương án đầu luôn trùng với kết quả `__call__` đã được đánh giá; xác suất chỉ để hiển thị."""
    m = max(s for _, s in cands)
    probs = {}
    for text, s in cands:
        probs[text] = probs.get(text, 0.0) + math.exp(s - m)
    z = sum(probs.values())
    return [{"text": t, "prob": p / z} for t, p in probs.items()]


def choices(alternatives: list[dict], k: int = 3, min_prob: float = 0.02) -> list[dict]:
    """Tối đa k phương án sửa để người dùng chọn, giữ thứ tự beam search: gộp các phương án chỉ khác chữ
    hoa/dấu câu cuối (cộng xác suất, giữ cách viết của phương án đứng trước) và bỏ phương án dưới min_prob."""
    merged: dict[str, dict] = {}
    for a in alternatives:
        key = a["text"].lower().rstrip(" .!?…")
        if key in merged:
            merged[key]["prob"] += a["prob"]
        else:
            merged[key] = {"text": a["text"], "prob": a["prob"]}
    return [c for i, c in enumerate(merged.values()) if i == 0 or c["prob"] >= min_prob][:k]


def top_options(model, texts: list[str], k: int = 3) -> list[list[str]]:
    """Các phương án sửa hiển thị cho người dùng (như demo); phần tử đầu = kết quả mặc định.
    Mô hình không có N-best (baseline, mô hình trên Hub) chỉ có một phương án."""
    if hasattr(model, "nbest"):
        return [[c["text"] for c in choices(alts, k)] for alts in model.nbest(texts)]
    return [[p] for p in model(texts)]


class HubCorrector:
    """Mô hình sửa lỗi bất kỳ trên Hugging Face Hub (vd bmd1905/vietnamese-correction-v2, BARTpho) để so sánh.
    Tokenizer chậm (không có offset) nên không khôi phục <unk>."""

    def __init__(self, name: str, num_beams: int = 4, batch_size: int = 16, max_new_tokens: int = 160,
                 device: str | None = None):
        from transformers import AutoTokenizer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(name)
        dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForSeq2SeqLM.from_pretrained(name, dtype=dtype).to(self.device).eval()
        self.num_beams, self.batch_size, self.max_new_tokens = num_beams, batch_size, max_new_tokens

    @torch.no_grad()
    def __call__(self, texts: list[str]) -> list[str]:
        texts = [normalize_text(t) for t in texts]
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        out = [""] * len(texts)
        for k in range(0, len(order), self.batch_size):
            idx = order[k:k + self.batch_size]
            enc = self.tok([texts[i] for i in idx], return_tensors="pt", padding=True).to(self.device)
            gen = self.model.generate(**enc, num_beams=self.num_beams, max_new_tokens=self.max_new_tokens)
            for i, d in zip(idx, self.tok.batch_decode(gen, skip_special_tokens=True)):
                out[i] = normalize_text(d)
        return out


def load_any(name: str, config: str = "configs/correction.yaml"):
    """'copy' -> baseline chép đầu vào; thư mục mô hình đã fine-tune -> Corrector; còn lại -> HubCorrector."""
    if name == "copy":
        return lambda texts: list(texts)
    if Path(name).is_dir():
        return from_config(name, config)
    g = load_config(config)["generate"]
    return HubCorrector(name, num_beams=g["num_beams"], max_new_tokens=g["max_new_tokens"])


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
