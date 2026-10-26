"""Gộp train/val của các dataset sửa lỗi -> data/processed/correction/{train,val}.jsonl

Tập test KHÔNG gộp: mỗi dataset giữ test riêng để báo cáo riêng (văn bản trang trọng vs tin nhắn).
Bỏ mọi dòng train/val có câu (source hoặc target) xuất hiện trong test của BẤT KỲ dataset nào,
vì các dataset có thể chồng lấn nguồn (VEC và ViLexNorm đều lấy từ bình luận mạng xã hội).

Chạy:  python -m src.data.build_correction_mix   (sau preprocess_vsec --all và split_data)
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from src.utils.text_utils import load_config

COLS = ["source", "target", "dataset"]


def load_split(processed_dir: Path, name: str, split: str) -> pd.DataFrame:
    df = pd.read_json(processed_dir / name / f"{split}.jsonl", lines=True)
    return df.assign(dataset=name)[COLS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/data.yaml")
    args = ap.parse_args()
    cfg = load_config(args.config)
    pdir = Path(cfg["processed_dir"])
    names = cfg["correction_mix"]["datasets"]

    tests = {n: load_split(pdir, n, "test") for n in names}
    test_texts = set().union(*(set(t.source) | set(t.target) for t in tests.values()))

    report = {"datasets": names, "splits": {}, "cross_dataset_test_overlap": {}}
    for a in names:  # rò rỉ chéo: test của a có câu nằm trong train của dataset khác?
        train_a = load_split(pdir, a, "train")
        a_texts = set(train_a.source) | set(train_a.target)
        for b in names:
            if a != b:
                n = int((tests[b].source.isin(a_texts) | tests[b].target.isin(a_texts)).sum())
                report["cross_dataset_test_overlap"][f"train_{a}->test_{b}"] = n

    out = pdir / "correction"
    out.mkdir(parents=True, exist_ok=True)
    seen = set(test_texts)
    for split in ("train", "val"):
        parts = []
        for n in names:
            df = load_split(pdir, n, split)
            leak = df.source.isin(seen) | df.target.isin(seen)
            report["splits"].setdefault(split, {})[n] = {"rows": int((~leak).sum()), "dropped_overlap": int(leak.sum())}
            parts.append(df[~leak])
        mix = pd.concat(parts, ignore_index=True).drop_duplicates(["source", "target"])
        mix = mix.sample(frac=1, random_state=cfg["seed"]).reset_index(drop=True)
        mix.to_json(out / f"{split}.jsonl", orient="records", lines=True, force_ascii=False)
        report["splits"][split]["total"] = len(mix)
        report["splits"][split]["identical_pairs"] = int((mix.source == mix.target).sum())
        if split == "train":
            seen |= set(mix.source) | set(mix.target)  # val không được chứa câu của train

    (out / "mix_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
