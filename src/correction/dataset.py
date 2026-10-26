"""Nạp tokenizer và chuẩn bị dữ liệu seq2seq cho mô hình sửa lỗi.

Tokenizer ViT5 được nạp thẳng từ tokenizer.json (PreTrainedTokenizerFast): ở transformers 5,
AutoTokenizer chuyển spiece.model của T5 bị lỗi `'dict' object is not an instance of 'Sequence'`.
"""
from pathlib import Path

import pandas as pd
from datasets import Dataset
from transformers import PreTrainedTokenizerFast


def load_tokenizer(name_or_dir: str) -> PreTrainedTokenizerFast:
    return PreTrainedTokenizerFast.from_pretrained(name_or_dir)


def load_pairs(path: str | Path, max_samples: int | None = None, seed: int = 42) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)[["source", "target"]]
    if max_samples and len(df) > max_samples:
        df = df.sample(max_samples, random_state=seed)
    return df.reset_index(drop=True)


def filter_by_length(df, src_lens, tgt_lens, max_source_len: int, max_target_len: int) -> pd.DataFrame:
    """Bỏ cặp quá dài thay vì cắt cụt: cắt câu đích sẽ dạy mô hình làm mất nội dung."""
    keep = (pd.Series(src_lens, index=df.index) <= max_source_len) & (pd.Series(tgt_lens, index=df.index) <= max_target_len)
    return df[keep]


def build_dataset(df: pd.DataFrame, tok, max_source_len: int, max_target_len: int) -> tuple[Dataset, int]:
    """Trả về (Dataset đã token hóa, số cặp bị bỏ vì quá dài)."""
    src = tok(df.source.tolist()).input_ids
    tgt = tok(df.target.tolist()).input_ids
    kept = filter_by_length(df, [len(x) for x in src], [len(x) for x in tgt], max_source_len, max_target_len)
    idx = kept.index.tolist()
    ds = Dataset.from_dict({
        "input_ids": [src[i] for i in idx],
        "attention_mask": [[1] * len(src[i]) for i in idx],
        "labels": [tgt[i] for i in idx],
    })
    return ds, len(df) - len(kept)
