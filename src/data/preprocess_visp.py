"""Làm sạch ViSP -> data/processed/visp_clean.jsonl (source = câu gốc, target = câu diễn đạt lại).

ViSP gồm các cụm câu đồng nghĩa (original_id); mỗi dòng là một cặp có thứ tự trong cụm.
Script đọc dạng stream (không nạp 1.18M dòng vào RAM), gom câu theo cụm, rồi lấy tối đa
`max_pairs_per_group` cặp mỗi cụm. Các câu khác trong cụm được lưu ở cột `references`
để đánh giá diễn đạt lại với nhiều câu tham chiếu.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.data.common import save_clean
from src.utils.text_utils import load_config, normalize_text


def load_clusters(raw_dir: str, spec: dict, pp: dict) -> tuple[dict, dict]:
    """Trả về {group_id: {"texts": [...], "orig_split": str, "topic": str}} và thống kê."""
    s_col, t_col, g_col = spec["source_col"], spec["target_col"], spec["group_id_col"]
    clusters = defaultdict(lambda: {"texts": {}, "orig_split": None, "topic": None})
    stats = {"raw_rows": 0, "source_col": s_col, "target_col": t_col, "dropped_texts_bad_length": 0}
    bad = set()
    for path in sorted((Path(raw_dir) / "visp").glob("*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                stats["raw_rows"] += 1
                c = clusters[str(r[g_col])]
                c["orig_split"] = path.stem
                c["topic"] = r.get("topic")
                for t in (r[s_col], r[t_col]):
                    t = normalize_text(t)
                    if pp["min_chars"] <= len(t) <= pp["max_chars"]:
                        c["texts"][t] = None  # dict giữ thứ tự xuất hiện, bỏ trùng
                    else:
                        bad.add(t)
    stats["dropped_texts_bad_length"] = len(bad)
    for c in clusters.values():
        c["texts"] = list(c["texts"])
    return dict(clusters), stats


def sample_pairs(clusters: dict, max_pairs: int | None, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for gid in sorted(clusters):
        c = clusters[gid]
        texts = c["texts"]
        pairs = [(a, b) for a in texts for b in texts if a != b]
        if max_pairs and len(pairs) > max_pairs:
            # ưu tiên mỗi câu nguồn khác nhau để không lặp source trong cùng cụm
            rng.shuffle(pairs)
            seen, chosen = set(), []
            for a, b in pairs:
                if a not in seen:
                    chosen.append((a, b))
                    seen.add(a)
                if len(chosen) == max_pairs:
                    break
            pairs = chosen
        for a, b in pairs:
            rows.append({
                "source": a, "target": b,
                "references": [t for t in texts if t != a],
                "group_id": gid, "topic": c["topic"], "orig_split": c["orig_split"],
            })
    return pd.DataFrame(rows)


def main(config_path: str = "configs/data.yaml"):
    cfg = load_config(config_path)
    spec = cfg["datasets"]["visp"]
    clusters, stats = load_clusters(cfg["raw_dir"], spec, cfg["preprocess"])
    sizes = pd.Series([len(c["texts"]) for c in clusters.values()])
    stats["clusters"] = len(clusters)
    stats["clusters_with_<2_texts_dropped"] = int((sizes < 2).sum())
    stats["texts_per_cluster"] = sizes.describe().round(2).to_dict()

    df = sample_pairs(clusters, spec.get("max_pairs_per_group"), cfg["seed"])
    stats["max_pairs_per_group"] = spec.get("max_pairs_per_group")
    stats["final_rows"] = len(df)
    stats["unique_sources"] = int(df.source.nunique())
    stats["rows_per_orig_split"] = df.orig_split.value_counts().to_dict()
    save_clean(df, stats, cfg, "visp")


if __name__ == "__main__":
    main()
