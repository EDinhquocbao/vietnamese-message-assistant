"""Làm sạch các dataset sửa lỗi -> data/processed/<tên>_clean.jsonl (source = câu lỗi, target = câu chuẩn).

Dùng chung cho VSEC, ViLexNorm, VEC. Giữ lại các cặp source == target (câu đúng sẵn,
có trong VEC) vì chúng dạy mô hình không sửa quá tay.

Chạy:  python -m src.data.preprocess_vsec                  (chỉ VSEC, như trước)
       python -m src.data.preprocess_vsec --only vilexnorm
       python -m src.data.preprocess_vsec --all            (mọi dataset sửa lỗi)
"""
import argparse
from pathlib import Path

import pandas as pd

from src.data.common import build_pairs, save_clean
from src.utils.text_utils import VSEC_SOURCE_CANDS, VSEC_TARGET_CANDS, load_config

CORRECTION_DATASETS = ["vsec", "vilexnorm", "vec"]


def preprocess(name: str, cfg: dict) -> None:
    df, stats = build_pairs(name, cfg, VSEC_SOURCE_CANDS, VSEC_TARGET_CANDS,
                            drop_identical=cfg["preprocess"]["drop_identical_pairs"])
    for other in cfg["datasets"][name].get("drop_overlap_with") or []:
        # So sánh không phân biệt hoa thường, vì một bản sao có thể đã bị hạ chữ thường
        o = pd.read_json(Path(cfg["processed_dir"]) / f"{other}_clean.jsonl", lines=True)
        texts = set(o.source.str.lower()) | set(o.target.str.lower())
        dup = df.source.str.lower().isin(texts) | df.target.str.lower().isin(texts)
        stats[f"dropped_overlap_with_{other}"] = int(dup.sum())
        df = df[~dup].reset_index(drop=True)
    stats["final_rows"] = len(df)
    stats["identical_pairs_kept"] = int((df.source == df.target).sum())
    save_clean(df, stats, cfg, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/data.yaml")
    ap.add_argument("--only", choices=CORRECTION_DATASETS, default="vsec")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    for name in (CORRECTION_DATASETS if args.all else [args.only]):
        preprocess(name, cfg)


if __name__ == "__main__":
    main()
