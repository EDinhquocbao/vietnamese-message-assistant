"""Khảo sát dữ liệu thô: cột, số mẫu, độ dài, trùng lặp, mẫu ngẫu nhiên.

Chạy:  python -m src.data.inspect_data            (cả hai)
Kết quả in ra màn hình và lưu vào reports/inspect_<tên>.md
"""
import argparse
from pathlib import Path

import pandas as pd

from src.utils.text_utils import (
    VISP_SOURCE_CANDS, VISP_TARGET_CANDS, VSEC_SOURCE_CANDS, VSEC_TARGET_CANDS,
    load_config, normalize_text, pick_column,
)

CANDS = {
    "vsec": (VSEC_SOURCE_CANDS, VSEC_TARGET_CANDS),
    "visp": (VISP_SOURCE_CANDS, VISP_TARGET_CANDS),
}


def load_raw(raw_dir: str, name: str) -> pd.DataFrame:
    parts = []
    for p in sorted((Path(raw_dir) / name).glob("*.jsonl")):
        df = pd.read_json(p, lines=True)
        df["_orig_split"] = p.stem
        parts.append(df)
    if not parts:
        raise FileNotFoundError(f"Chưa có dữ liệu trong {raw_dir}/{name}. Chạy download_data trước.")
    return pd.concat(parts, ignore_index=True)


def inspect(name: str, cfg: dict) -> str:
    spec = cfg["datasets"][name]
    df = load_raw(cfg["raw_dir"], name)
    origin = spec.get("hf_name") or next(iter(spec["files"].values())).rsplit("/", 1)[0]
    lines = [f"# Khảo sát {name.upper()} ({origin})", ""]

    lines += ["## Cấu trúc", f"- Tổng số dòng: {len(df):,}"]
    lines += [f"- Các split gốc: {df['_orig_split'].value_counts().to_dict()}"]
    lines += [f"- Cột: {[c for c in df.columns if c != '_orig_split']}", ""]
    lines += ["## Kiểu dữ liệu và giá trị rỗng", "```", str(df.dtypes), "---", str(df.isna().sum()), "```", ""]

    s_cands, t_cands = CANDS.get(name, CANDS["vsec"])
    try:
        s_col = pick_column(df.columns, spec.get("source_col"), s_cands, "nguồn")
        t_col = pick_column(df.columns, spec.get("target_col"), t_cands, "đích")
    except KeyError as e:
        lines += ["## Lỗi dò cột", str(e), ""]
        return "\n".join(lines)

    lines += [f"## Cột được dùng", f"- source = `{s_col}`, target = `{t_col}` (kiểm tra xem có đúng chiều không!)", ""]

    src = df[s_col].map(normalize_text)
    tgt = df[t_col].map(normalize_text)
    stats = pd.DataFrame({
        "source_chars": src.str.len(), "target_chars": tgt.str.len(),
        "source_words": src.str.split().str.len(), "target_words": tgt.str.split().str.len(),
    })
    lines += ["## Độ dài", "```", str(stats.describe(percentiles=[.5, .9, .99]).round(1)), "```", ""]

    identical = (src == tgt).mean()
    lines += ["## Chất lượng",
              f"- Cặp source == target: {identical:.2%}",
              f"- Source rỗng: {(src == '').sum():,}; target rỗng: {(tgt == '').sum():,}",
              f"- Cặp (source, target) trùng hoàn toàn: {pd.DataFrame({'s': src, 't': tgt}).duplicated().sum():,}",
              f"- Số source duy nhất: {src.nunique():,}; số target duy nhất: {tgt.nunique():,}",
              f"- Số target xuất hiện >1 lần: {(tgt.value_counts() > 1).sum():,}", ""]

    if name == "vsec":
        if "has_errors" in df.columns:
            lines += ["## Thông tin lỗi (VSEC)", f"- has_errors: {df['has_errors'].value_counts().to_dict()}"]
        if "error_count" in df.columns:
            lines += ["- error_count:", "```", str(df["error_count"].describe().round(2)), "```", ""]
    if name == "visp":
        gid = spec.get("group_id_col")
        if gid and gid in df.columns:
            per = df.groupby(gid).size()
            lines += ["## Cấu trúc nhóm (ViSP)", f"- Số câu gốc duy nhất ({gid}): {per.shape[0]:,}",
                      "- Số paraphrase mỗi câu gốc:", "```", str(per.describe().round(2)), "```"]
            sp = df.groupby(gid)["_orig_split"].nunique()
            lines += [f"- Câu gốc xuất hiện ở >1 split gốc: {(sp > 1).sum():,}", ""]
        for c in ("topic", "source"):
            if c in df.columns:
                lines += [f"- {c}: {df[c].value_counts().head(12).to_dict()}"]
        lines += [""]

    lines += ["## 15 mẫu ngẫu nhiên (seed=42)", ""]
    sample = df.assign(source=src, target=tgt).sample(min(15, len(df)), random_state=cfg["seed"])
    for _, r in sample.iterrows():
        lines += [f"- **S:** {r['source']}", f"  **T:** {r['target']}"]
    lines += [""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/data.yaml")
    ap.add_argument("--only", default=None, help="tên một dataset trong config")
    args = ap.parse_args()
    cfg = load_config(args.config)

    Path(cfg["reports_dir"]).mkdir(parents=True, exist_ok=True)
    for name in ([args.only] if args.only else list(cfg["datasets"])):
        report = inspect(name, cfg)
        print(report)
        (Path(cfg["reports_dir"]) / f"inspect_{name}.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
