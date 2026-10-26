"""Chia train/val/test THEO NHÓM để tránh rò rỉ dữ liệu.

- VSEC: nhóm = câu chuẩn (target). Một câu chuẩn có nhiều biến thể lỗi sẽ nằm cùng một tập.
- ViSP: nhóm = câu gốc (source). Các paraphrase của cùng một câu gốc nằm cùng một tập.

Chạy:  python -m src.data.split_data
Kết quả: data/processed/<tên>/{train,val,test}.jsonl + split_report.json
"""
import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from src.utils.text_utils import load_config


def group_split(df: pd.DataFrame, group_col: str, ratios: dict, seed: int):
    """Trả về (train, val, test) với các nhóm tách biệt hoàn toàn."""
    assert abs(sum(ratios.values()) - 1.0) < 1e-6, "Tỷ lệ chia phải cộng lại bằng 1"
    groups = df[group_col]

    gss = GroupShuffleSplit(n_splits=1, test_size=ratios["test"], random_state=seed)
    trainval_idx, test_idx = next(gss.split(df, groups=groups))
    trainval, test = df.iloc[trainval_idx], df.iloc[test_idx]

    val_frac = ratios["val"] / (ratios["train"] + ratios["val"])
    gss2 = GroupShuffleSplit(n_splits=1, test_size=val_frac, random_state=seed)
    tr_idx, val_idx = next(gss2.split(trainval, groups=trainval[group_col]))
    return trainval.iloc[tr_idx], trainval.iloc[val_idx], test


def check_leakage(train, val, test, group_col: str) -> dict:
    sets = {"train": train, "val": val, "test": test}
    result = {}
    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        g = set(sets[a][group_col]) & set(sets[b][group_col])
        s = set(sets[a]["source"]) & set(sets[b]["source"])
        t = set(sets[a]["target"]) & set(sets[b]["target"])
        result[f"{a}&{b}"] = {"shared_groups": len(g), "shared_sources": len(s), "shared_targets": len(t)}
    return result


def drop_text_overlap(train, val, test):
    """Bỏ khỏi val/test các dòng có câu (source hoặc target) đã xuất hiện ở tập trước đó.

    Cần cho ViSP: cùng một câu có thể nằm trong hai cụm khác nhau, nên tách theo cụm vẫn rò rỉ.
    """
    def texts(df):
        return set(df["source"]) | set(df["target"])

    def keep(df, seen):
        return df[~df["source"].isin(seen) & ~df["target"].isin(seen)]

    seen = texts(train)
    val2 = keep(val, seen)
    test2 = keep(test, seen | texts(val2))
    return val2, test2, {"val": len(val) - len(val2), "test": len(test) - len(test2)}


def split_one(name: str, cfg: dict) -> None:
    path = Path(cfg["processed_dir"]) / f"{name}_clean.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Chưa có {path}. Chạy preprocess_{name} trước.")
    df = pd.read_json(path, lines=True)
    spec = cfg["datasets"][name]
    group_col = spec["group_by"]

    if spec.get("use_original_split"):
        # Dùng split gốc của dataset (đã kiểm tra là tách theo nhóm) để so sánh được với bài báo
        train, val, test = (df[df.orig_split == s] for s in ("train", "validation", "test"))
    else:
        train, val, test = group_split(df, group_col, cfg["split"], cfg["seed"])
    val, test, dropped = drop_text_overlap(train, val, test)
    leak = check_leakage(train, val, test, group_col)
    bad = {k: v for k, v in leak.items() if any(v.values())}
    if bad:
        raise RuntimeError(f"Rò rỉ dữ liệu giữa các tập: {bad}")

    out = Path(cfg["processed_dir"]) / name
    out.mkdir(parents=True, exist_ok=True)
    report = {"group_by": group_col, "seed": cfg["seed"],
              "original_split": bool(spec.get("use_original_split")),
              "dropped_text_overlap": dropped, "leakage_check": leak, "sizes": {}}
    for split_name, part in [("train", train), ("val", val), ("test", test)]:
        part.to_json(out / f"{split_name}.jsonl", orient="records", lines=True, force_ascii=False)
        report["sizes"][split_name] = {"rows": len(part), "groups": int(part[group_col].nunique())}
    (out / "split_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{name}] {json.dumps(report['sizes'])}  (không rò rỉ nhóm)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/data.yaml")
    ap.add_argument("--only", default=None, help="tên một dataset trong config")
    args = ap.parse_args()
    cfg = load_config(args.config)
    for name in ([args.only] if args.only else list(cfg["datasets"])):
        split_one(name, cfg)


if __name__ == "__main__":
    main()
