"""Đánh giá sửa lỗi trên tập test, kèm đo sửa quá tay.

VSEC không có câu nào đúng sẵn, nên tỉ lệ sửa quá tay được đo bằng cách đưa chính các câu
chuẩn (target) vào hệ thống: một hệ thống tốt phải giữ nguyên chúng.

Chạy baseline "chép nguyên đầu vào" (mốc tối thiểu mọi mô hình phải vượt):
    python -m src.correction.evaluate --baseline copy
Chạy mô hình đã fine-tune (lưu thêm dự đoán vào outputs/predictions/ để phân tích lỗi):
    python -m src.correction.evaluate --model models/correction/vit5-base --data data/processed/vilexnorm/test.jsonl
"""
import argparse
import json
from pathlib import Path
from typing import Callable

import pandas as pd

from src.utils.metrics import correction_report, overcorrection_rate

BASELINES: dict[str, Callable[[list[str]], list[str]]] = {
    "copy": lambda texts: list(texts),
}


def evaluate(df: pd.DataFrame, predict: Callable[[list[str]], list[str]], return_preds: bool = False):
    sources, refs = df.source.tolist(), df.target.tolist()
    preds = predict(sources)
    report = correction_report(sources, preds, refs)
    clean = sorted(set(refs))
    report["overcorrection_rate"] = overcorrection_rate(clean, predict(clean))
    report["n_clean"] = len(clean)
    return (report, preds) if return_preds else report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed/vsec/test.jsonl")
    ap.add_argument("--baseline", choices=sorted(BASELINES), default="copy")
    ap.add_argument("--model", default=None, help="thư mục mô hình đã fine-tune hoặc tên mô hình trên Hub (thay cho --baseline)")
    ap.add_argument("--out_dir", default="outputs/metrics")
    args = ap.parse_args()

    df = pd.read_json(args.data, lines=True)
    tag = f"{Path(args.data).parent.name}_{Path(args.data).stem}"
    if args.model:
        from src.correction.predict import load_any

        system = Path(args.model).name
        report, preds = evaluate(df, load_any(args.model), return_preds=True)
        pred_path = Path("outputs/predictions") / f"correction_{tag}_{system}.jsonl"
        pred_path.parent.mkdir(parents=True, exist_ok=True)
        df.assign(pred=preds).to_json(pred_path, orient="records", lines=True, force_ascii=False)
    else:
        system = f"baseline_{args.baseline}"
        report = evaluate(df, BASELINES[args.baseline])
    report.update({"system": system, "data": args.data})

    out = Path(args.out_dir) / f"correction_{tag}_{system}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
