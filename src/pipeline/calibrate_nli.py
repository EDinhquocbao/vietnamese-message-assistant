"""Chọn ngưỡng NLI cho bộ lọc gợi ý trên ViSP VAL (không dùng test).

Đo min(P(a ⇒ b), P(b ⇒ a)) trên các cặp diễn đạt do NGƯỜI viết; ngưỡng = phân vị `--keep` sao cho
khoảng (1 - keep) câu người viết vẫn qua được. Kết quả -> outputs/metrics/nli_calibration.json;
chép giá trị `threshold` vào configs/pipeline.yaml > ranker.min_entailment.

Chạy:  python -m src.pipeline.calibrate_nli [--n 1000 --keep 10]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.pipeline.ranker import Ranker
from src.utils.text_utils import load_config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed/visp/val.jsonl")
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--keep", type=float, default=10, help="phân vị dùng làm ngưỡng (%%)")
    args = ap.parse_args()

    nli_model = load_config(args.config)["ranker"]["nli_model"]
    r = Ranker(nli_model=nli_model)
    df = pd.read_json(args.data, lines=True).sample(args.n, random_state=42)
    a, b = df.source.tolist(), df.target.tolist()
    scores = np.minimum(r.entail(a, b), r.entail(b, a))
    pct = {q: float(np.percentile(scores, q)) for q in (5, 10, 15, 20, 25, 50)}
    report = {
        "nli_model": nli_model, "data": args.data, "n": args.n, "percentiles": pct,
        "pass_rate": {th: float((scores >= th).mean()) for th in (0.3, 0.5, 0.6, 0.7, 0.8)},
        "threshold": round(pct[int(args.keep)] if int(args.keep) in pct else float(np.percentile(scores, args.keep)), 3),
        "lowest_pairs": [{"a": x, "b": y, "score": float(s)}
                         for x, y, s in sorted(zip(a, b, scores), key=lambda t: t[2])[:5]],
    }
    out = Path("outputs/metrics/nli_calibration.json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
