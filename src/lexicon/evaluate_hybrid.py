"""So sánh mô hình hiện tại với các cách kết hợp từ điển (xem src/lexicon/hybrid.py).

    python -m src.lexicon.evaluate_hybrid tune   # chọn tham số trên VAL -> outputs/metrics/hybrid_tuning.json
    python -m src.lexicon.evaluate_hybrid test   # 3 tập test + stress test -> outputs/metrics/hybrid_*.json/.md

Tham số dùng khi test nằm ở configs/lexicon.yaml; test không bao giờ dùng để chọn tham số.
"""
import argparse
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from src.correction.evaluate import evaluate
from src.correction.predict import from_config as load_corrector, top_options
from src.correction.stress_test import CATEGORIES, LABELS, build_inputs, score as stress_score
from src.lexicon.candidates import SPAN, Lexicon
from src.lexicon.hybrid import CachedModel, HybridCorrector
from src.utils.metrics import correction_report, tokenize
from src.utils.text_utils import load_config

MODES = ["model", "lexicon", "guard", "rerank"]
OUT = Path("outputs/metrics")


def log(*a):
    print(*a, flush=True, file=sys.stderr)


def tune_sample(seed: int = 42) -> pd.DataFrame:
    """Toàn bộ val ViLexNorm (đúng miền tin nhắn), thêm 400 câu VSEC và 400 câu VEC."""
    val = pd.read_json("data/processed/correction/val.jsonl", lines=True)
    parts = [val[val.dataset == "vilexnorm"]]
    for name in ("vsec", "vec"):
        part = val[val.dataset == name]
        parts.append(part.sample(min(400, len(part)), random_state=seed))
    return pd.concat(parts, ignore_index=True)


def single_replacements(src: list[str], tgt: list[str]) -> list[tuple[str, str]]:
    """Các cặp (từ gốc, đáp án) của một phép thay: 1 từ -> cụm, hoặc n từ -> n từ ghép từng cặp; khác thì rỗng."""
    if len(src) == 1:
        return [(src[0], " ".join(tgt))]
    return list(zip(src, tgt)) if len(src) == len(tgt) else []


def coverage(lex: Lexicon, df: pd.DataFrame) -> float:
    """Trong các phép thay một từ của dữ liệu, tỉ lệ đáp án đúng có trong ứng viên."""
    hit = total = 0
    for s, t in zip(df.source, df.target):
        st, tt = tokenize(s.lower()), tokenize(t.lower())
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=st, b=tt, autojunk=False).get_opcodes():
            if tag != "replace":
                continue
            for a, b in single_replacements(st[i1:i2], tt[j1:j2]):
                total += 1
                hit += b in lex.channel(a)
    return hit / max(total, 1)


def ceiling(lex: Lexicon, df: pd.DataFrame, k: int) -> float:
    """Tỉ lệ câu mà câu chuẩn nằm trong lưới ứng viên (trần của chế độ chỉ dùng từ điển)."""
    ok = 0
    for s, t in zip(df.source, df.target):
        st, tt = [m.group() for m in SPAN.finditer(s)], tokenize(t.lower())
        low = [x.lower() for x in st]
        good = True
        for tag, i1, i2, j1, j2 in SequenceMatcher(a=low, b=tt, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            pairs = single_replacements(st[i1:i2], tt[j1:j2]) if tag == "replace" else []
            if not pairs or not all(b in dict(lex.options(a, k)) for a, b in pairs):
                good = False
                break
        ok += good
    return ok / max(len(df), 1)


def f05(system, df) -> dict:
    preds = system(df.source.tolist())
    return correction_report(df.source.tolist(), preds, df.target.tolist())


def tune() -> None:
    cfg = load_config("configs/lexicon.yaml")
    df = tune_sample()
    log("val:", len(df), "câu")
    results: dict = {}
    lex = Lexicon.from_config(cfg)
    results["coverage"] = {
        "day_du": coverage(lex, df),
        "bo_viet74k": coverage(Lexicon.load(cfg["lexicon_path"], use_syllables=False), df),
        "bo_nsw": coverage(Lexicon.load(cfg["lexicon_path"], use_nsw=False), df),
    }
    log(results["coverage"])
    grid = []
    for k in (6, 10):
        for alpha in (0.25, 0.5, 1.0, 2.0):
            r = f05(HybridCorrector("lexicon", lex, k=k, n=1, alpha=alpha), df)
            grid.append({"k": k, "alpha": alpha, "f0.5": r["f0.5"], "wer": r["wer"]})
            log("lexicon", grid[-1])
    results["lexicon"] = grid
    best = max(grid, key=lambda x: x["f0.5"])

    model = CachedModel(load_corrector(config=cfg["correction_config"]))
    results["model"] = f05(HybridCorrector("model", model=model), df)
    log("model", results["model"]["f0.5"], results["model"]["wer"])
    grid = []
    for gk in (6, 10, 20, None):
        r = f05(HybridCorrector("guard", lex, model, guard_k=gk), df)
        grid.append({"guard_k": gk, "f0.5": r["f0.5"], "wer": r["wer"]})
        log("guard", grid[-1])
    results["guard"] = grid
    grid = []
    for beta in (0.0, 0.25, 0.5, 1.0, 2.0):
        for penalty in (-4.0, -8.0, -14.0):
            r = f05(HybridCorrector("rerank", lex, model, k=best["k"], alpha=best["alpha"], beta=beta, penalty=penalty), df)
            grid.append({"beta": beta, "penalty": penalty, "f0.5": r["f0.5"], "wer": r["wer"]})
            log("rerank", grid[-1])
    results["rerank"] = grid
    results["best"] = {m: max(results[m], key=lambda x: x["f0.5"]) for m in ("lexicon", "guard", "rerank")}
    (OUT / "hybrid_tuning.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results["best"], ensure_ascii=False, indent=2))


def system(mode: str, cfg: dict, lex: Lexicon, model) -> HybridCorrector:
    p = cfg["params"]
    return HybridCorrector(mode, lex, model, k=p["k"], n=p["n"], alpha=p["alpha"], beta=p["beta"], penalty=p["penalty"],
                           guard_k=p["guard_k"])


def table(real: dict, stress: dict, ceil: dict) -> str:
    lines = ["## Tập test thật (WER / câu đúng hết / đúng trong top-3 / sửa quá tay)", "",
             "| Tập | Trần từ điển | " + " | ".join(MODES) + " |", "|---|---|" + "---|" * len(MODES)]
    for d in real[MODES[0]]:
        cells = [f"{real[m][d]['wer']:.2%} / {real[m][d]['exact_match']:.1%} / {real[m][d]['exact_match_top3']:.1%} / "
                 f"{real[m][d]['overcorrection_rate']:.1%}" for m in MODES]
        lines.append(f"| {d} | {ceil[d]:.1%} | " + " | ".join(cells) + " |")
    lines += ["", "## Stress test (WER / câu đúng hết / đúng trong top-3)", "",
              "| Kiểu lỗi | " + " | ".join(MODES) + " |", "|---|" + "---|" * len(MODES)]
    for c in CATEGORIES:
        cells = [f"{stress[m][c]['wer']:.2%} / {stress[m][c]['exact_match']:.1%} / {stress[m][c]['exact_match_top3']:.1%}"
                 for m in MODES]
        lines.append(f"| {LABELS[c]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def test() -> None:
    cfg = load_config("configs/lexicon.yaml")
    lex = Lexicon.from_config(cfg)
    model = CachedModel(load_corrector(config=cfg["correction_config"]))
    data = {d: pd.read_json(f"data/processed/{d}/test.jsonl", lines=True) for d in ("vilexnorm", "vsec", "vec")}
    ceil = {d: ceiling(lex, df, cfg["params"]["k"]) for d, df in data.items()}
    log("trần từ điển", ceil)
    inputs = build_inputs("data/processed/vilexnorm/test.jsonl", 400)
    real, stress = {m: {} for m in MODES}, {}
    for m in MODES:
        sys_ = system(m, cfg, lex, model)
        for d, df in data.items():
            log("bắt đầu", m, d)
            real[m][d], preds = evaluate(df, sys_, return_preds=True)
            df.assign(pred=preds).to_json(f"outputs/predictions/hybrid_{m}_{d}.jsonl", orient="records", lines=True,
                                          force_ascii=False)
            log(m, d, {k: round(real[m][d][k], 4) for k in ("wer", "exact_match", "overcorrection_rate")})
        log("stress", m)
        options = top_options(sys_, inputs.input.tolist())
        part = inputs.assign(pred=[o[0] for o in options], options=options)
        stress[m] = stress_score(part)
        log("stress xong", m, round(stress[m]["go_nhanh"]["exact_match"], 4))
    (OUT / "hybrid_results.json").write_text(json.dumps({"real": real, "stress": stress, "ceiling": ceil, "params": cfg["params"]},
                                                        ensure_ascii=False, indent=2), encoding="utf-8")
    md = table(real, stress, ceil)
    (OUT / "hybrid_comparison.md").write_text(md + "\n", encoding="utf-8")
    print(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "test"])
    args = ap.parse_args()
    {"tune": tune, "test": test}[args.stage]()


if __name__ == "__main__":
    main()
