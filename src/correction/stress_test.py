"""Đo mô hình sửa lỗi theo TỪNG KIỂU LỖI gõ phím, trên câu chuẩn held-out (ViLexNorm test).

Mỗi kiểu lỗi được sinh tự động bằng đúng các hàm trong src/data/augment_errors.py, với seed riêng
(khác seed tạo dữ liệu train) và chỉ trên câu test, nên không rò rỉ vào train. Kiểu "cau_dung" đưa
nguyên câu chuẩn vào để đo sửa quá tay.

Chạy:  python -m src.correction.stress_test --models copy models/correction/vit5-base \
           models/correction/vit5-base-aug bmd1905/vietnamese-correction-v2
Kết quả: outputs/metrics/stress_<hệ thống>.json, bảng so sánh outputs/metrics/stress_comparison.md,
và dự đoán từng câu ở outputs/predictions/stress_<hệ thống>.jsonl (để phân tích lỗi).
"""
import argparse
import json
import random
from pathlib import Path

import pandas as pd

from src.correction.predict import load_any
from src.data.augment_errors import (
    DIACRITIC_ERRORS, ERROR_TYPES, TYPING_ERRORS, corrupt_words, strip_diacritics,
)
from src.utils.metrics import wer

SEED = 2026  # khác seed 42 dùng khi tạo dữ liệu train


def _only(*names):
    return {n: ERROR_TYPES.get(n) or TYPING_ERRORS.get(n) or DIACRITIC_ERRORS[n] for n in names}


def _typos(types):
    return lambda s, rng: corrupt_words(s, rng, rng.randint(1, 2), types)[0]


CATEGORIES = {
    "cau_dung": lambda s, rng: s,
    "khong_dau": lambda s, rng: strip_diacritics(s),
    "dao_chu": _typos(_only("transpose")),
    "bam_hut": _typos(_only("delete")),
    "phim_ben_canh": _typos(_only("keyboard")),
    "phim_dup": _typos(_only("double")),
    "sai_dau": _typos(_only("tone", "vowel_mark")),
    "go_nhanh": lambda s, rng: corrupt_words(strip_diacritics(s), rng, rng.randint(1, 2), TYPING_ERRORS)[0],
}
LABELS = {
    "cau_dung": "Câu đã đúng (sửa quá tay)", "khong_dau": "Không dấu cả câu", "dao_chu": "Đảo chữ",
    "bam_hut": "Bấm hụt/thiếu chữ", "phim_ben_canh": "Phím bên cạnh", "phim_dup": "Phím đúp",
    "sai_dau": "Sai dấu thanh/dấu chữ", "go_nhanh": "Gõ nhanh: không dấu + 1–2 lỗi gõ",
}


def build_inputs(data: str, n: int) -> pd.DataFrame:
    df = pd.read_json(data, lines=True)
    pool = df.target[df.target.str.split().str.len().between(4, 25)].drop_duplicates()
    targets = pool.sample(min(n, len(pool)), random_state=SEED).tolist()
    rng = random.Random(SEED)
    rows = [{"category": c, "input": fn(t, rng), "target": t} for c, fn in CATEGORIES.items() for t in targets]
    return pd.DataFrame(rows)


def score(df: pd.DataFrame) -> dict:
    out = {}
    for c, part in df.groupby("category", sort=False):
        out[c] = {
            "n": len(part),
            "wer_input": wer(part.input.tolist(), part.target.tolist()),
            "wer": wer(part.pred.tolist(), part.target.tolist()),
            "exact_match": float((part.pred == part.target).mean()),
        }
    return out


def to_markdown(results: dict[str, dict]) -> str:
    systems = list(results)
    lines = ["| Kiểu lỗi | WER đầu vào | " + " | ".join(f"{s} WER / đúng hết" for s in systems) + " |",
             "|---|---|" + "---|" * len(systems)]
    for c in CATEGORIES:
        first = results[systems[0]][c]
        cells = [f"{results[s][c]['wer']:.1%} / {results[s][c]['exact_match']:.1%}" for s in systems]
        lines.append(f"| {LABELS[c]} | {first['wer_input']:.1%} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True,
                    help="'copy', thư mục mô hình đã fine-tune, hoặc tên mô hình trên Hub")
    ap.add_argument("--data", default="data/processed/vilexnorm/test.jsonl")
    ap.add_argument("--n", type=int, default=400, help="số câu chuẩn; mỗi câu được gây lỗi theo mọi kiểu")
    args = ap.parse_args()

    inputs = build_inputs(args.data, args.n)
    results = {}
    for name in args.models:
        system = "copy" if name == "copy" else Path(name).name
        df = inputs.assign(pred=load_any(name)(inputs.input.tolist()))
        results[system] = score(df)
        df.to_json(Path("outputs/predictions") / f"stress_{system}.jsonl", orient="records", lines=True,
                   force_ascii=False)
        out = Path("outputs/metrics") / f"stress_{system}.json"
        out.write_text(json.dumps({"system": system, "data": args.data, "n_sentences": args.n, "seed": SEED,
                                   "categories": results[system]}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{system}] xong -> {out}")

    table = to_markdown(results)
    Path("outputs/metrics/stress_comparison.md").write_text(
        f"Stress test trên {args.n} câu chuẩn của {args.data} (seed {SEED}). Ô: WER sau sửa / tỉ lệ câu đúng hết.\n\n"
        + table + "\n", encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
