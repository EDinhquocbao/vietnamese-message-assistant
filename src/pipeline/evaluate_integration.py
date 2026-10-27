"""Đánh giá pipeline trên tập kiểm thử tích hợp data/test/integration_test.csv (nhóm A-D).

Tự động (-> outputs/metrics/integration_<model>.json), báo cáo riêng từng nhóm:
- exact_match: câu đã sửa == expected_correction (nhóm C, D: expected = chính đầu vào)
- changed_rate: tỉ lệ câu bị thay đổi (ở nhóm D = tỉ lệ sửa quá tay)
- keep_rate_corrected / keep_rate_suggestions: tỉ lệ giữ được các mục must_keep (số, tên, phủ định)
- avg_suggestions: số gợi ý trung bình còn lại sau khi lọc
Thủ công (-> outputs/error_analysis/integration_<model>_to_rate.csv): mỗi dòng có cột trống để
chấm câu sửa (1/0) và từng gợi ý (1 = chấp nhận được: đúng nghĩa, tự nhiên, không thêm/bỏ ý),
từ đó tính Top-1/Top-3 acceptance.

Chạy:  python -m src.pipeline.evaluate_integration [--include_draft]
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from src.pipeline.assistant import from_config
from src.pipeline.ranker import NEGATIONS, protected_spans
from src.utils.text_utils import load_config


def keeps(text: str, must_keep: str) -> bool:
    """Mọi mục trong must_keep (ngăn cách bởi ;) còn trong text. Mục là từ phủ định (vd 'ko')
    thì chỉ cần text còn phủ định, vì sửa lỗi sẽ đổi 'ko' -> 'không'."""
    for item in (x.strip() for x in str(must_keep or "").split(";")):
        if not item:
            continue
        if item.lower() in NEGATIONS:
            if not protected_spans(text)["negation"]:
                return False
        elif item not in text:
            return False
    return True


def group_metrics(df: pd.DataFrame) -> dict:
    sugg_keep = [keeps(s, mk) for sugg, mk in zip(df.suggestions, df.must_keep) for s in sugg]
    return {
        "n": len(df),
        "exact_match": float((df.corrected == df.expected_correction).mean()),
        "changed_rate": float((df.corrected != df.input).mean()),
        "keep_rate_corrected": float(pd.Series([keeps(c, mk) for c, mk in zip(df.corrected, df.must_keep)]).mean()),
        "keep_rate_suggestions": float(pd.Series(sugg_keep).mean()) if sugg_keep else None,
        "avg_suggestions": float(df.suggestions.map(len).mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/test/integration_test.csv")
    ap.add_argument("--config", default="configs/pipeline.yaml")
    ap.add_argument("--include_draft", action="store_true",
                    help="tính cả câu status=draft (chưa duyệt); kết quả chỉ để tham khảo")
    ap.add_argument("--tag", default="", help="hậu tố tên file kết quả, vd '_para-ep4' khi đổi mô hình diễn đạt lại")
    args = ap.parse_args()

    df = pd.read_csv(args.data, dtype=str, keep_default_na=False)
    if not args.include_draft:
        df = df[df.status != "draft"]
    if df.empty:
        raise SystemExit("Không còn câu nào đã duyệt. Duyệt tập kiểm thử hoặc chạy với --include_draft.")

    results = from_config(args.config).run_batch(df.input.tolist())
    df = df.assign(corrected=[r["corrected"] for r in results],
                   suggestions=[[s["text"] for s in r["suggestions"]] for r in results])

    pipe_cfg = load_config(args.config)
    corr_cfg = load_config(pipe_cfg["correction_config"])
    system = Path(corr_cfg["output_dir"]).name + args.tag
    report = {"system": system, "paraphrase_model": load_config(pipe_cfg["paraphrase_config"])["output_dir"],
              "data": args.data, "include_draft": args.include_draft,
              "all": group_metrics(df), "by_group": {g: group_metrics(part) for g, part in df.groupby("group")}}
    out = Path("outputs/metrics") / f"integration_{system}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    rate = df[["id", "group", "input", "expected_correction", "must_keep", "corrected"]].copy()
    rate["rate_correction"] = ""
    for i in range(3):
        rate[f"suggestion_{i + 1}"] = df.suggestions.map(lambda s, i=i: s[i] if i < len(s) else "")
        rate[f"rate_suggestion_{i + 1}"] = ""
    rate_path = Path("outputs/error_analysis") / f"integration_{system}_to_rate.csv"
    rate_path.parent.mkdir(parents=True, exist_ok=True)
    rate.to_csv(rate_path, index=False, encoding="utf-8-sig")  # utf-8-sig để Excel đọc đúng tiếng Việt
    print(f"-> {out}\n-> {rate_path} (điền cột rate_* để tính Top-1/Top-3)")


if __name__ == "__main__":
    main()
