"""RQ3: nên diễn đạt lại thẳng câu lỗi, hay sửa lỗi trước rồi mới diễn đạt lại?

Đầu vào lấy từ stress test (src.correction.stress_test.build_inputs: câu chuẩn ViLexNorm test bị gây
lỗi tự động, seed 2026), nên biết câu chuẩn (`target`) mà người viết muốn nói. Ba hệ thống:
- truc_tiep: diễn đạt lại ngay câu lỗi, xếp hạng so với chính câu lỗi (hệ thống không biết câu chuẩn);
- hai_buoc: sửa lỗi (phương án đầu) rồi diễn đạt lại câu đã sửa (pipeline đang dùng);
- can_tren: diễn đạt lại câu chuẩn (giới hạn trên, như thể bước sửa lỗi hoàn hảo).
Không áp dụng chặn "từ lạ" của demo để so được cả hai hệ thống; độ "sạch" được đo riêng.

Mỗi gợi ý được so với câu CHUẨN:
- giữ nghĩa: cosine MiniLM >= 0,8 và NLI hai chiều >= 0,17 (cùng ngưỡng với ranker);
- sạch: không có từ lạ (ngoài từ điển câu chuẩn train và ngoài chính câu chuẩn) -> không mang lỗi
  chính tả sang gợi ý;
- đạt = giữ nghĩa và sạch. Chỉ số chính: tỉ lệ câu có gợi ý đầu đạt / có ít nhất 1 gợi ý đạt.
- self-BLEU so với câu chuẩn: thấp = diễn đạt khác đi nhiều.

Chạy:  python -m src.pipeline.rq3 [--n 150]
Kết quả: outputs/metrics/rq3.json, bảng outputs/metrics/rq3.md, từng câu outputs/predictions/rq3.jsonl.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from src.correction.predict import from_config as load_corrector
from src.correction.stress_test import LABELS, build_inputs
from src.paraphrase.generate import from_config as load_paraphraser
from src.pipeline.assistant import load_vocab, unknown_words
from src.pipeline.ranker import Ranker
from src.utils.metrics import corpus_bleu, tokenize
from src.utils.text_utils import load_config

CATEGORIES = ["cau_dung", "khong_dau", "bam_hut", "sai_dau", "go_nhanh"]
SYSTEMS = {"truc_tiep": "Diễn đạt thẳng câu lỗi", "hai_buoc": "Sửa lỗi rồi diễn đạt",
           "can_tren": "Diễn đạt câu chuẩn (cận trên)"}


def judge(ranker: Ranker, vocab: set[str], targets: list[str], suggestions: list[list[str]]) -> list[list[dict]]:
    """Chấm từng gợi ý so với câu chuẩn tương ứng."""
    pairs = [(t, s) for t, sugg in zip(targets, suggestions) for s in sugg]
    if not pairs:
        return [[] for _ in targets]
    ts, ss = [p[0] for p in pairs], [p[1] for p in pairs]
    emb_t, emb_s = ranker.encode(ts), ranker.encode(ss)
    sims = (emb_t * emb_s).sum(axis=1)
    nli = [min(f, b) for f, b in zip(ranker.entail(ts, ss), ranker.entail(ss, ts))]
    # từ lạ có sẵn trong câu chuẩn (tên, từ lóng hiếm) không tính là lỗi
    rows = iter({"text": s, "sim": float(x), "nli": float(n),
                 "clean": not set(unknown_words(s, vocab)) - {w.lower() for w in tokenize(t)}}
                for t, s, x, n in zip(ts, ss, sims, nli))
    out = []
    for sugg in suggestions:
        judged = [next(rows) for _ in sugg]
        for j in judged:
            j["keeps_meaning"] = j["sim"] >= ranker.min_similarity and j["nli"] >= ranker.min_entailment
            j["ok"] = j["keeps_meaning"] and j["clean"]
        out.append(judged)
    return out


def summarize(df: pd.DataFrame) -> dict:
    """df: mỗi dòng một (hệ thống, kiểu lỗi, câu) với cột `judged` (list gợi ý đã chấm) và `target`."""
    flat = [j for js in df.judged for j in js]
    tops = [js[0] for js in df.judged if js]
    with_sugg = df[df.judged.map(len) > 0]
    return {
        "n": len(df),
        "has_suggestion": float((df.judged.map(len) > 0).mean()),
        "avg_suggestions": float(df.judged.map(len).mean()),
        "top1_ok": sum(j["ok"] for j in tops) / len(df),  # câu không có gợi ý tính là không đạt
        "any_ok": float(df.judged.map(lambda js: any(j["ok"] for j in js)).mean()),
        "keeps_meaning": sum(j["keeps_meaning"] for j in flat) / max(len(flat), 1),
        "clean": sum(j["clean"] for j in flat) / max(len(flat), 1),
        "sim_to_target": sum(j["sim"] for j in flat) / max(len(flat), 1),
        "self_bleu_target": corpus_bleu([js[0]["text"] for js in with_sugg.judged],
                                        [[t] for t in with_sugg.target]) if len(with_sugg) else None,
    }


def to_markdown(results: dict) -> str:
    lines = ["| Kiểu lỗi | " + " | ".join(SYSTEMS[s] for s in SYSTEMS) + " |", "|---|" + "---|" * len(SYSTEMS)]
    for c in CATEGORIES:
        cells = [f"{results[s][c]['top1_ok']:.1%} / {results[s][c]['any_ok']:.1%}" for s in SYSTEMS]
        lines.append(f"| {LABELS[c]} | " + " | ".join(cells) + " |")
    lines += ["", "Chi tiết (mọi gợi ý): giữ nghĩa / sạch lỗi / cosine với câu chuẩn / self-BLEU gợi ý đầu.", "",
              "| Kiểu lỗi | " + " | ".join(SYSTEMS[s] for s in SYSTEMS) + " |", "|---|" + "---|" * len(SYSTEMS)]
    for c in CATEGORIES:
        cells = []
        for s in SYSTEMS:
            r = results[s][c]
            sb = "–" if r["self_bleu_target"] is None else f"{r['self_bleu_target']:.0f}"
            cells.append(f"{r['keeps_meaning']:.0%} / {r['clean']:.0%} / {r['sim_to_target']:.2f} / {sb}")
        lines.append(f"| {LABELS[c]} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/processed/vilexnorm/test.jsonl")
    ap.add_argument("--n", type=int, default=150, help="số câu chuẩn; mỗi câu được gây lỗi theo mọi kiểu")
    ap.add_argument("--config", default="configs/pipeline.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    inputs = build_inputs(args.data, args.n)
    inputs = inputs[inputs.category.isin(CATEGORIES)].reset_index(drop=True)
    corrector = load_corrector(config=cfg["correction_config"])
    inputs["corrected"] = corrector(inputs.input.tolist())
    del corrector

    paraphraser = load_paraphraser(config=cfg["paraphrase_config"])
    ranker = Ranker(**cfg["ranker"])
    vocab = load_vocab(cfg["vocab"]["sources"], cfg["vocab"]["min_count"])
    sources = {"truc_tiep": inputs.input, "hai_buoc": inputs.corrected, "can_tren": inputs.target}

    frames = []
    for system, src in sources.items():
        texts = src.tolist()
        uniq = list(dict.fromkeys(texts))  # câu chuẩn lặp lại ở mọi kiểu lỗi -> chỉ sinh một lần
        cands = dict(zip(uniq, paraphraser.candidates(uniq)))
        sugg = {t: [r["text"] for r in ranker.rank(t, cands[t])] for t in uniq}
        df = inputs.assign(system=system, source=texts, suggestions=[sugg[t] for t in texts])
        df["judged"] = judge(ranker, vocab, df.target.tolist(), df.suggestions.tolist())
        frames.append(df)
        print(f"[{system}] xong")
    all_df = pd.concat(frames, ignore_index=True)

    results = {s: {c: summarize(part) for c, part in g.groupby("category", sort=False)}
               for s, g in all_df.groupby("system", sort=False)}
    Path("outputs/metrics/rq3.json").write_text(
        json.dumps({"data": args.data, "n_sentences": args.n, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    all_df.drop(columns=["suggestions"]).to_json("outputs/predictions/rq3.jsonl", orient="records", lines=True,
                                                 force_ascii=False)
    table = to_markdown(results)
    Path("outputs/metrics/rq3.md").write_text(
        f"RQ3 trên {args.n} câu chuẩn của {args.data} (đầu vào stress test, seed 2026). "
        "Ô: gợi ý đầu đạt / có ít nhất 1 gợi ý đạt (đạt = giữ nghĩa câu chuẩn và không còn từ lỗi).\n\n"
        + table + "\n", encoding="utf-8")
    print(table)


if __name__ == "__main__":
    main()
