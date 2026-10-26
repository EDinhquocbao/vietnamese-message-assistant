"""Đánh giá diễn đạt lại trên tập test ViSP với nhiều câu tham chiếu (cột `references`).

Chạy baseline:
    python -m src.paraphrase.evaluate --baseline copy        # chép câu gốc: bleu_ref cao nhưng ibleu thấp
    python -m src.paraphrase.evaluate --baseline target      # trả về đúng một câu tham chiếu: mốc trần
Chạy mô hình (lưu dự đoán vào outputs/predictions/), thêm --semantic để đo độ giữ nghĩa bằng embedding:
    python -m src.paraphrase.evaluate --model models/paraphrase/vit5-base --semantic
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from src.utils.metrics import paraphrase_report

EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def semantic_similarity(sources: list[str], preds: list[str]) -> float:
    """Cosine trung bình giữa embedding câu gốc và câu sinh ra (cao = giữ nghĩa)."""
    from src.pipeline.ranker import Ranker

    r = Ranker(model_name=EMBED_MODEL)
    a, b = r.encode(sources), r.encode(preds)
    return float((a * b).sum(axis=1).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed/visp/test.jsonl")
    ap.add_argument("--baseline", choices=["copy", "target"], default="copy")
    ap.add_argument("--model", default=None, help="thư mục mô hình đã fine-tune (thay cho --baseline)")
    ap.add_argument("--max_samples", type=int, default=None, help="đánh giá trên tập con ngẫu nhiên (seed 42)")
    ap.add_argument("--semantic", action="store_true", help="thêm độ tương đồng embedding với câu gốc")
    ap.add_argument("--out_dir", default="outputs/metrics")
    args = ap.parse_args()

    df = pd.read_json(args.data, lines=True)
    if args.max_samples and len(df) > args.max_samples:
        df = df.sample(args.max_samples, random_state=42).reset_index(drop=True)
    sources = df.source.tolist()
    system = Path(args.model).name if args.model else f"baseline_{args.baseline}"
    if args.model:
        from src.paraphrase.generate import from_config

        # cùng tham chiếu như baseline copy: mọi câu khác trong cụm (gồm cả target)
        preds, refs = from_config(args.model)(sources), df.references.tolist()
        tag = f"{Path(args.data).parent.name}_{Path(args.data).stem}"
        pred_path = Path("outputs/predictions") / f"paraphrase_{tag}_{system}.jsonl"
        pred_path.parent.mkdir(parents=True, exist_ok=True)
        df.assign(pred=preds).to_json(pred_path, orient="records", lines=True, force_ascii=False)
    elif args.baseline == "copy":
        preds, refs = sources, df.references.tolist()
    else:
        # dự đoán = target; tham chiếu = các câu còn lại trong cụm (bỏ chính target để không tự so với mình)
        preds = df.target.tolist()
        refs = [[r for r in rs if r != t] or [t] for rs, t in zip(df.references, preds)]

    report = paraphrase_report(sources, preds, refs)
    if args.semantic:
        report["semantic_sim_to_source"] = semantic_similarity(sources, preds)
    report.update({"system": system, "data": args.data, "max_samples": args.max_samples})
    suffix = f"_n{args.max_samples}" if args.max_samples else ""
    out = Path(args.out_dir) / f"paraphrase_{Path(args.data).parent.name}_{Path(args.data).stem}_{system}{suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
