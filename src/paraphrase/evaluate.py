"""Đánh giá diễn đạt lại trên tập test ViSP với nhiều câu tham chiếu (cột `references`).

Chạy baseline:
    python -m src.paraphrase.evaluate --baseline copy        # chép câu gốc: bleu_ref cao nhưng ibleu thấp
    python -m src.paraphrase.evaluate --baseline target      # trả về đúng một câu tham chiếu: mốc trần
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from src.utils.metrics import paraphrase_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed/visp/test.jsonl")
    ap.add_argument("--baseline", choices=["copy", "target"], default="copy")
    ap.add_argument("--out_dir", default="outputs/metrics")
    args = ap.parse_args()

    df = pd.read_json(args.data, lines=True)
    sources = df.source.tolist()
    if args.baseline == "copy":
        preds, refs = sources, df.references.tolist()
    else:
        # dự đoán = target; tham chiếu = các câu còn lại trong cụm (bỏ chính target để không tự so với mình)
        preds = df.target.tolist()
        refs = [[r for r in rs if r != t] or [t] for rs, t in zip(df.references, preds)]

    report = paraphrase_report(sources, preds, refs)
    report.update({"system": f"baseline_{args.baseline}", "data": args.data})
    out = Path(args.out_dir) / f"paraphrase_{Path(args.data).parent.name}_{Path(args.data).stem}_baseline_{args.baseline}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
