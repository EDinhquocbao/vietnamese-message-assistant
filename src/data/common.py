import json
from pathlib import Path

import pandas as pd

from src.data.inspect_data import load_raw
from src.utils.text_utils import normalize_text, pick_column


def build_pairs(name, cfg, s_cands, t_cands, drop_identical: bool):
    """Đọc raw -> bảng (source, target, orig_split) đã chuẩn hóa và lọc. Trả về (df, stats)."""
    spec = cfg["datasets"][name]
    pp = cfg["preprocess"]
    raw = load_raw(cfg["raw_dir"], name)
    s_col = pick_column(raw.columns, spec.get("source_col"), s_cands, "nguồn")
    t_col = pick_column(raw.columns, spec.get("target_col"), t_cands, "đích")

    df = pd.DataFrame({
        "source": raw[s_col].map(normalize_text),
        "target": raw[t_col].map(normalize_text),
        "orig_split": raw["_orig_split"],
    })
    gid_col = spec.get("group_id_col")
    if gid_col:
        if gid_col not in raw.columns:
            raise KeyError(f"group_id_col '{gid_col}' không có trong dữ liệu: {list(raw.columns)}")
        df["group_id"] = raw[gid_col].astype(str)
    for extra in ("topic", "error_count", "has_errors"):  # giữ lại để phân tích lỗi sau này
        if extra in raw.columns:
            df[extra] = raw[extra]
    stats = {"raw_rows": len(df), "source_col": s_col, "target_col": t_col}

    n = len(df)
    df = df[(df.source.str.len() >= pp["min_chars"]) & (df.target.str.len() >= pp["min_chars"])]
    stats["dropped_empty_or_short"] = n - len(df)

    n = len(df)
    df = df[(df.source.str.len() <= pp["max_chars"]) & (df.target.str.len() <= pp["max_chars"])]
    stats["dropped_too_long"] = n - len(df)

    if drop_identical:
        n = len(df)
        df = df[df.source != df.target]
        stats["dropped_identical_pairs"] = n - len(df)

    n = len(df)
    df = df.drop_duplicates(subset=["source", "target"] + (["group_id"] if "group_id" in df.columns else [])).reset_index(drop=True)
    stats["dropped_duplicate_pairs"] = n - len(df)
    stats["final_rows"] = len(df)
    stats["identical_pairs_kept"] = int((df.source == df.target).sum())
    return df, stats


def save_clean(df: pd.DataFrame, stats: dict, cfg: dict, name: str) -> Path:
    out_dir = Path(cfg["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}_clean.jsonl"
    df.to_json(path, orient="records", lines=True, force_ascii=False)
    (out_dir / f"{name}_clean_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"-> {path}")
    return path
