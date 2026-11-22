"""Giả lập gõ từng từ trên câu test, không cần người thật gõ.

Với mỗi câu, phát lại từng từ qua `Session` và đo:
- giu_nguyen: không chọn gì, chỉ áp Telex tự động.
- nhan_dau: nhận mọi gợi ý đầu.
- chon_dung: người dùng chọn đáp án nếu nó có trong tối đa 3 gợi ý (CẬN TRÊN, người thật có thể không chọn đúng).
Kèm top-1/top-3 mỗi từ sai, số lần chạm mỗi câu, số lần gợi ý đầu bị đổi, độ trễ từng tầng.

Chạy:  python -m src.realtime.simulate --n 300
"""
import argparse
import json
import random
import statistics
import time
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from src.correction.predict import from_config as load_corrector
from src.correction.stress_test import CATEGORIES
from src.lexicon.candidates import SPAN, Lexicon
from src.realtime.session import Session
from src.utils.metrics import exact_match, tokenize, wer
from src.utils.text_utils import load_config

SEED = 2026


def gold_words(source_tokens: list[str], target: str) -> list[str | None]:
    """Đáp án chữ thường cho từng từ nguồn; None nếu không ghép được (thêm/bớt/gộp từ)."""
    low, tgt = [t.lower() for t in source_tokens], tokenize(target.lower())
    gold: list[str | None] = [None] * len(low)
    for tag, i1, i2, j1, j2 in SequenceMatcher(a=low, b=tgt, autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for off in range(i2 - i1):
                gold[i1 + off] = tgt[j1 + off]
        elif tag == "replace" and i2 - i1 == 1:
            gold[i1] = " ".join(tgt[j1:j2])
    return gold


def percentile(values: list[float], q: float) -> float:
    return sorted(values)[min(int(len(values) * q), len(values) - 1)] if values else 0.0


def replay(source: str, target: str, make_session, scorer=None, pick_gold: bool = False):
    """Phát lại một câu. Trả (session, số lần chạm, độ trễ tầng nhanh, độ trễ tầng ViT5)."""
    tokens = SPAN.findall(source)
    gold = gold_words(tokens, target)
    s = make_session()
    taps, fast, slow = 0, [], []

    def maybe_pick(i: int):
        nonlocal taps
        w, g = s.words[i], gold[i]
        if w.locked or g is None or g == w.shown.lower():
            return
        if g in [c for c, _ in w.options[:s.top]]:
            s.choose(i, g)
            taps += 1

    typed: list[str] = []
    for i, tok in enumerate(tokens):
        typed.append(tok)  # luôn đưa chữ gốc: từ đã đổi hoặc đã chọn vẫn được sync nhận ra qua w.raw
        t0 = time.perf_counter()
        s.sync(" ".join(typed) + " ")
        fast.append((time.perf_counter() - t0) * 1000)
        if scorer:
            t0 = time.perf_counter()
            s.refine(scorer)
            slow.append((time.perf_counter() - t0) * 1000)
        if pick_gold and i > 0:
            maybe_pick(i - 1)
    if pick_gold and tokens:
        maybe_pick(len(tokens) - 1)
    return s, taps, gold, fast, slow


def evaluate_set(df: pd.DataFrame, make_session, scorer=None) -> dict:
    keep, best, oracle, refs = [], [], [], df.target.tolist()
    taps, fast, slow, changes = [], [], [], []
    top1 = top3 = errors = 0
    for src, tgt in zip(df.source, df.target):
        s, _, gold, f, sl = replay(src, tgt, make_session, scorer)
        keep.append(s.text())
        best.append(s.text(accept_best=True))
        fast += f
        slow += sl
        changes.append(s.best_changes)
        for w, g in zip(s.words, gold):
            if g is not None and g != w.raw.lower():
                errors += 1
                opts = [c for c, _ in w.options[:s.top]]
                top1 += opts[:1] == [g]
                top3 += g in opts
        o, t, *_ = replay(src, tgt, make_session, scorer, pick_gold=True)
        oracle.append(o.text())
        taps.append(t)
    norm = [" ".join(tokenize(r)) for r in refs]

    def report(preds):
        return {"wer": wer(preds, refs), "exact_match": exact_match([" ".join(tokenize(p)) for p in preds], norm)}

    return {
        "n": len(df), "giu_nguyen": report(keep), "nhan_dau": report(best), "chon_dung": report(oracle),
        "tu_sai": errors, "top1_tu_sai": top1 / max(errors, 1), "top3_tu_sai": top3 / max(errors, 1),
        "cham_moi_cau": statistics.mean(taps), "doi_goi_y_moi_cau": statistics.mean(changes),
        "tre_nhanh_ms": {"p50": percentile(fast, 0.5), "p95": percentile(fast, 0.95)},
        "tre_vit5_ms": {"p50": percentile(slow, 0.5), "p95": percentile(slow, 0.95)} if slow else None,
    }


def corrupted(df: pd.DataFrame, category: str) -> pd.DataFrame:
    rng = random.Random(SEED)
    return pd.DataFrame({"source": [CATEGORIES[category](t, rng) for t in df.target], "target": df.target.tolist()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--config", default="configs/lexicon.yaml")
    args = ap.parse_args()
    cfg = load_config(args.config)
    p = cfg["params"]
    lex = Lexicon.from_config(cfg)
    make = lambda: Session(lex, k=p["k"], alpha=p["alpha"], beta=p["beta"])  # noqa: E731
    corrector = load_corrector(config=cfg["correction_config"])
    test = pd.read_json("data/processed/vilexnorm/test.jsonl", lines=True)
    test = test[test.target.str.split().str.len().between(4, 25)].sample(min(args.n, len(test)), random_state=SEED)
    sets = {"vilexnorm": test[["source", "target"]], "khong_dau": corrupted(test, "khong_dau"), "go_nhanh": corrupted(test, "go_nhanh")}
    results = {}
    for name, df in sets.items():
        results[name] = {"tu_dien": evaluate_set(df, make), "tu_dien_vit5": evaluate_set(df, make, corrector.score_pairs)}
        print(name, json.dumps(results[name], ensure_ascii=False), flush=True)
    out = Path("outputs/metrics/realtime_simulation.json")
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("->", out)


if __name__ == "__main__":
    main()
