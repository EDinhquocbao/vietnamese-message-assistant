"""Tạo lỗi nhân tạo trên câu chuẩn của tập train sửa lỗi -> data/processed/correction/train_aug.jsonl

Lý do: dữ liệu thật (ViLexNorm, VEC) chủ yếu là viết tắt/không dấu; lỗi gõ phím trong tin nhắn
(thiếu chữ "cùng"->"cùn", đảo chữ "nhau"->"nahu", sai dấu "quên"->"quyên") hầu như không có,
nên mô hình bỏ qua chúng. Quy tắc tạo lỗi (mỗi câu 1..max_errors từ, mỗi từ một lỗi):
- tone:       đổi/bỏ/thêm dấu thanh (sớm -> sơm, sờm)
- vowel_mark: đổi dấu chữ â/ă/a, ê/e, ô/ơ/o, ư/u (cô -> co, cơ)
- delete:     xóa một ký tự (cùng -> cùn)
- transpose:  đảo hai ký tự liền nhau (nhau -> nahu)
- keyboard:   gõ nhầm phím bên cạnh trên bàn phím QWERTY (bạn -> vạn)
- consonant:  nhầm phụ âm đầu/cuối hay gặp (s/x, ch/tr, d/gi/r, l/n, n/ng, c/t)
Chỉ thêm vào TRAIN; val/test giữ dữ liệu thật. Không đụng từ có chữ số (giờ, tiền, mã).

Chạy:  python -m src.data.augment_errors   (sau build_correction_mix)
"""
import argparse
import json
import random
import re
import unicodedata
from pathlib import Path

import pandas as pd

from src.utils.text_utils import load_config

TONES = ["̀", "́", "̃", "̉", "̣"]  # huyền, sắc, ngã, hỏi, nặng
SHAPES = {"a": ["", "̆", "̂"], "e": ["", "̂"], "o": ["", "̂", "̛"], "u": ["", "̛"]}
VOWELS = set("aeiouy")
NEIGHBORS = {
    "q": "wa", "w": "qes", "e": "wrd", "r": "etf", "t": "ryg", "y": "tuh", "u": "yij", "i": "uok", "o": "ipl",
    "p": "ol", "a": "qsz", "s": "adwx", "d": "sfe", "f": "dgr", "g": "fht", "h": "gjy", "j": "hku", "k": "jli",
    "l": "kop", "z": "asx", "x": "zcs", "c": "xvd", "v": "cbf", "b": "vng", "n": "bmh", "m": "nj",
}
INITIAL_RULES = [("ch", "tr"), ("tr", "ch"), ("gi", "d"), ("s", "x"), ("x", "s"), ("d", "gi"), ("d", "r"),
                 ("r", "d"), ("l", "n"), ("n", "l")]
FINAL_RULES = [("ng", "n"), ("n", "ng"), ("c", "t"), ("t", "c")]
_EDGE = re.compile(r"^(\W*)(.*?)(\W*)$", re.S)


def _clusters(word: str) -> list[list]:
    """Tách từ (NFD) thành [chữ cơ sở, [các dấu kết hợp]]."""
    out = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and out:
            out[-1][1].append(ch)
        else:
            out.append([ch, []])
    return out


def _join(clusters) -> str:
    return unicodedata.normalize("NFC", "".join(b + "".join(m) for b, m in clusters))


def change_tone(word: str, rng: random.Random) -> str:
    cl = _clusters(word)
    vowels = [i for i, (b, _) in enumerate(cl) if b.lower() in VOWELS]
    if not vowels:
        return word
    toned = [i for i in vowels if any(m in TONES for m in cl[i][1])]
    if toned:
        i = toned[0]
        cur = next(m for m in cl[i][1] if m in TONES)
        cl[i][1] = [m for m in cl[i][1] if m not in TONES]
        new = rng.choice([t for t in TONES if t != cur] + [""])
    else:
        # vị trí dấu gần đúng: nguyên âm có dấu chữ, hoặc nguyên âm áp chót nếu từ tận cùng bằng nguyên âm
        marked = [i for i in vowels if cl[i][1]]
        if marked:
            i = marked[-1]
        elif len(vowels) > 1 and vowels[-1] == len(cl) - 1:
            i = vowels[-2]
        else:
            i = vowels[-1]
        new = rng.choice(TONES)
    cl[i][1].append(new)
    return _join(cl)


def change_vowel_mark(word: str, rng: random.Random) -> str:
    cl = _clusters(word)
    cands = [i for i, (b, _) in enumerate(cl) if b.lower() in SHAPES]
    if not cands:
        return word
    i = rng.choice(cands)
    shapes = SHAPES[cl[i][0].lower()]
    cur = next((m for m in cl[i][1] if m in shapes[1:]), "")
    tones = [m for m in cl[i][1] if m not in shapes]
    cl[i][1] = [m for m in [rng.choice([s for s in shapes if s != cur])] if m] + tones
    return _join(cl)


def delete_char(word: str, rng: random.Random) -> str:
    if len(word) < 2:
        return word
    i = rng.randrange(len(word))
    return word[:i] + word[i + 1:]


def transpose(word: str, rng: random.Random) -> str:
    pos = [i for i in range(len(word) - 1) if word[i] != word[i + 1]]
    if not pos:
        return word
    i = rng.choice(pos)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def keyboard_typo(word: str, rng: random.Random) -> str:
    cl = _clusters(word)
    cands = [i for i, (b, m) in enumerate(cl) if b.lower() in NEIGHBORS and not m]
    if not cands:
        return word
    i = rng.choice(cands)
    new = rng.choice(NEIGHBORS[cl[i][0].lower()])
    cl[i][0] = new.upper() if cl[i][0].isupper() else new
    return _join(cl)


def confuse_consonant(word: str, rng: random.Random) -> str:
    low = word.lower()

    def is_vowel(ch):
        return bool(ch) and unicodedata.normalize("NFD", ch)[0] in VOWELS

    options = []
    for old, new in INITIAL_RULES:
        if low.startswith(old) and is_vowel(low[len(old):len(old) + 1]):
            options.append(new + word[len(old):] if word[0].islower() else new.capitalize() + word[len(old):])
    for old, new in FINAL_RULES:
        if low.endswith(old) and is_vowel(low[-len(old) - 1:-len(old)]):
            options.append(word[:-len(old)] + new)
    return rng.choice(options) if options else word


ERROR_TYPES = {
    "tone": (change_tone, 3.0),
    "vowel_mark": (change_vowel_mark, 2.0),
    "delete": (delete_char, 2.0),
    "transpose": (transpose, 1.5),
    "keyboard": (keyboard_typo, 1.5),
    "consonant": (confuse_consonant, 1.5),
}


def _corrupt_word(core: str, rng: random.Random) -> tuple[str, str | None]:
    names = list(ERROR_TYPES)
    weights = [ERROR_TYPES[n][1] for n in names]
    while names:
        name = rng.choices(names, weights)[0]
        new = ERROR_TYPES[name][0](core, rng)
        if new != core:
            return new, name
        k = names.index(name)
        names.pop(k), weights.pop(k)
    return core, None


def make_noisy(sentence: str, rng: random.Random, max_errors: int = 3) -> tuple[str, list[str]]:
    """Gây lỗi cho 1..max_errors từ (chỉ từ toàn chữ cái, giữ nguyên dấu câu dính kèm)."""
    words = sentence.split(" ")
    parts = [_EDGE.match(w).groups() for w in words]
    eligible = [i for i, (_, core, _) in enumerate(parts) if len(core) >= 2 and core.isalpha()]
    if not eligible:
        return sentence, []
    k = rng.randint(1, min(max_errors, len(eligible)))
    types = []
    for i in rng.sample(eligible, k):
        pre, core, post = parts[i]
        new, name = _corrupt_word(core, rng)
        if name:
            words[i] = pre + new + post
            types.append(name)
    return " ".join(words), types


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/data.yaml")
    args = ap.parse_args()
    cfg = load_config(args.config)
    aug = cfg["augment"]
    pdir = Path(cfg["processed_dir"])
    rng = random.Random(cfg["seed"])

    train = pd.read_json(pdir / "correction" / "train.jsonl", lines=True)
    pool = train[train.dataset.isin(aug["from_datasets"])].target.drop_duplicates()
    pool = pool[pool.str.split().str.len() >= aug["min_words"]]
    targets = pool.sample(min(aug["n_samples"], len(pool)), random_state=cfg["seed"]).tolist()

    # câu lỗi sinh ra không được trùng câu nào của val/test (giữ bất biến chống rò rỉ)
    held_out = set()
    for name in cfg["correction_mix"]["datasets"]:
        t = pd.read_json(pdir / name / "test.jsonl", lines=True)
        held_out |= set(t.source) | set(t.target)
    v = pd.read_json(pdir / "correction" / "val.jsonl", lines=True)
    held_out |= set(v.source) | set(v.target)

    rows, dropped = [], 0
    for t in targets:
        noisy, types = make_noisy(t, rng, aug["max_errors"])
        if not types or noisy in held_out:
            dropped += 1
            continue
        rows.append({"source": noisy, "target": t, "dataset": "synthetic", "error_types": types})
    syn = pd.DataFrame(rows)
    out = pd.concat([train, syn], ignore_index=True).sample(frac=1, random_state=cfg["seed"])
    path = pdir / "correction" / "train_aug.jsonl"
    out.to_json(path, orient="records", lines=True, force_ascii=False)

    report = {
        "real_rows": len(train), "synthetic_rows": len(syn), "dropped": dropped, "total": len(out),
        "from_datasets": aug["from_datasets"],
        "error_type_counts": pd.Series([x for ts in syn.error_types for x in ts]).value_counts().to_dict(),
        "errors_per_sentence": syn.error_types.str.len().value_counts().sort_index().to_dict(),
        "examples": syn.head(10)[["source", "target"]].to_dict("records"),
    }
    (pdir / "correction" / "augment_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                             encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"-> {path}")


if __name__ == "__main__":
    main()
