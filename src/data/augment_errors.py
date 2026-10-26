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

Hai hồ sơ (tỉ lệ ở configs/data.yaml > augment.profiles):
- single:      1..max_errors lỗi như trên trên câu còn dấu.
- fast_typing: mô phỏng gõ nhanh trên điện thoại: bỏ dấu cả câu/một phần, chồng thêm 0..3 lỗi gõ
               (đảo chữ, bấm hụt, phím bên cạnh, phím đúp "đii", nhầm phụ âm; nếu còn dấu thì cả sai dấu
               và Telex không chuyển "dduwowngf"), đôi khi thiếu dấu cách ("cùngnhau"); một phần nhỏ giữ
               nguyên câu để mô hình không sửa quá tay.

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

TONES = ["\u0300", "\u0301", "\u0303", "\u0309", "\u0323"]  # huyền, sắc, ngã, hỏi, nặng
SHAPES = {"a": ["", "\u0306", "\u0302"], "e": ["", "\u0302"], "o": ["", "\u0302", "\u031b"], "u": ["", "\u031b"]}
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


def _corrupt_word(core: str, rng: random.Random, types: dict = ERROR_TYPES) -> tuple[str, str | None]:
    names = list(types)
    weights = [types[n][1] for n in names]
    while names:
        name = rng.choices(names, weights)[0]
        new = types[name][0](core, rng)
        if new != core:
            return new, name
        k = names.index(name)
        names.pop(k), weights.pop(k)
    return core, None


def corrupt_words(sentence: str, rng: random.Random, k: int, types: dict = ERROR_TYPES) -> tuple[str, list[str]]:
    """Gây lỗi cho k từ ngẫu nhiên (chỉ từ toàn chữ cái, giữ nguyên dấu câu dính kèm), loại lỗi lấy từ `types`."""
    words = sentence.split(" ")
    parts = [_EDGE.match(w).groups() for w in words]
    eligible = [i for i, (_, core, _) in enumerate(parts) if len(core) >= 2 and core.isalpha()]
    applied = []
    for i in rng.sample(eligible, min(k, len(eligible))):
        pre, core, post = parts[i]
        new, name = _corrupt_word(core, rng, types)
        if name:
            words[i] = pre + new + post
            applied.append(name)
    return " ".join(words), applied


def make_noisy(sentence: str, rng: random.Random, max_errors: int = 3) -> tuple[str, list[str]]:
    """Gây lỗi cho 1..max_errors từ bằng mọi loại lỗi trong ERROR_TYPES."""
    n_eligible = sum(len(c) >= 2 and c.isalpha() for _, c, _ in (_EDGE.match(w).groups() for w in sentence.split(" ")))
    if not n_eligible:
        return sentence, []
    return corrupt_words(sentence, rng, rng.randint(1, min(max_errors, n_eligible)))


# ---------------------------------------------------------------- hồ sơ "gõ nhanh"

def strip_diacritics(text: str) -> str:
    """Bỏ mọi dấu (gõ không dấu): "Đường đi học" -> "Duong di hoc"."""
    text = "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", text.replace("đ", "d").replace("Đ", "D"))


def double_char(word: str, rng: random.Random) -> str:
    """Phím bị nhấn đúp: "đi" -> "đii"."""
    i = rng.randrange(len(word))
    return word[:i + 1] + word[i] + word[i + 1:]


_TELEX_SHAPE = {"̂": None, "̆": "w", "̛": "w"}  # None = gõ đúp nguyên âm (â -> aa)
_TELEX_TONE = {"́": "s", "̀": "f", "̉": "r", "̃": "x", "̣": "j"}


def telex_raw(word: str) -> str:
    """Chuỗi phím Telex khi bộ gõ không chuyển (dấu thanh gõ cuối từ): "đường" -> "dduwowngf"."""
    out, tone = [], ""
    for base, marks in _clusters(word):
        key = {"đ": "dd", "Đ": "Dd"}.get(base, base)
        for m in marks:
            if m in _TELEX_TONE:
                tone = _TELEX_TONE[m]
            elif m in _TELEX_SHAPE:
                key += _TELEX_SHAPE[m] or base.lower()
        out.append(key)
    return "".join(out) + tone


def _telex_word(word: str, rng: random.Random) -> str:
    return telex_raw(word) if strip_diacritics(word) != word else word


# Lỗi gõ áp được cho cả từ đã bỏ dấu; các lỗi về dấu chỉ dùng khi câu còn dấu.
TYPING_ERRORS = {
    "transpose": (transpose, 3.0),
    "delete": (delete_char, 3.0),
    "keyboard": (keyboard_typo, 2.5),
    "double": (double_char, 1.0),
    "consonant": (confuse_consonant, 1.0),
}
DIACRITIC_ERRORS = {
    "tone": (change_tone, 2.0),
    "vowel_mark": (change_vowel_mark, 1.5),
    "telex": (_telex_word, 0.5),
}


def make_fast_typing_noise(sentence: str, rng: random.Random, cfg: dict) -> tuple[str, list[str]]:
    """Mô phỏng gõ nhanh trên điện thoại: có thể bỏ dấu (cả câu/một phần), rồi chồng thêm 0..n lỗi gõ
    (đảo chữ, bấm hụt, phím bên cạnh, phím đúp, nhầm phụ âm; nếu còn dấu thì cả sai dấu/Telex dở),
    và đôi khi thiếu dấu cách giữa hai từ. Trả về (câu lỗi, danh sách loại lỗi); [] = giữ nguyên câu."""
    if rng.random() < cfg["p_clean"]:
        return sentence, []
    words, types = sentence.split(" "), []
    stripped = rng.random() < cfg["p_strip"]
    if stripped:
        if rng.random() < cfg["p_strip_full"]:
            words = [strip_diacritics(w) for w in words]
            types.append("strip_full")
        else:
            words = [strip_diacritics(w) if rng.random() < 0.5 else w for w in words]
            types.append("strip_partial")

    counts = {int(k): v for k, v in cfg["typo_counts"].items()}
    k = rng.choices(list(counts), list(counts.values()))[0]
    allowed = TYPING_ERRORS if stripped else {**TYPING_ERRORS, **DIACRITIC_ERRORS}
    text, applied = corrupt_words(" ".join(words), rng, k, allowed)
    words = text.split(" ")
    types += applied

    if len(words) >= 2 and rng.random() < cfg["p_merge"]:
        i = rng.randrange(len(words) - 1)
        words[i:i + 2] = [words[i] + words[i + 1]]
        types.append("merge")
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
    # pool nhỏ hơn n_samples thì một câu chuẩn được dùng nhiều lần với các kiểu lỗi khác nhau
    targets = pool.sample(aug["n_samples"], replace=aug["n_samples"] > len(pool), random_state=cfg["seed"]).tolist()

    # câu lỗi sinh ra không được trùng câu nào của val/test (giữ bất biến chống rò rỉ)
    held_out = set()
    for name in cfg["correction_mix"]["datasets"]:
        t = pd.read_json(pdir / name / "test.jsonl", lines=True)
        held_out |= set(t.source) | set(t.target)
    v = pd.read_json(pdir / "correction" / "val.jsonl", lines=True)
    held_out |= set(v.source) | set(v.target)

    profiles = aug["profiles"]
    rows, dropped, seen = [], 0, set()
    for t in targets:
        profile = rng.choices(list(profiles), list(profiles.values()))[0]
        if profile == "single":
            noisy, types = make_noisy(t, rng, aug["max_errors"])
        else:
            noisy, types = make_fast_typing_noise(t, rng, aug["fast_typing"])
        if noisy in held_out or (noisy, t) in seen:
            dropped += 1
            continue
        seen.add((noisy, t))
        rows.append({"source": noisy, "target": t, "dataset": "synthetic", "profile": profile, "error_types": types})
    syn = pd.DataFrame(rows)
    out = pd.concat([train, syn], ignore_index=True).sample(frac=1, random_state=cfg["seed"])
    path = pdir / "correction" / "train_aug.jsonl"
    out.to_json(path, orient="records", lines=True, force_ascii=False)

    report = {
        "real_rows": len(train), "synthetic_rows": len(syn), "dropped_held_out_or_duplicate": dropped,
        "total": len(out), "unique_targets_used": int(syn.target.nunique()),
        "from_datasets": aug["from_datasets"], "profiles": syn.profile.value_counts().to_dict(),
        "unchanged_copies": int((syn.source == syn.target).sum()),
        "error_type_counts": pd.Series([x for ts in syn.error_types for x in ts]).value_counts().to_dict(),
        "errors_per_sentence": syn.error_types.str.len().value_counts().sort_index().to_dict(),
        "examples": syn.sample(15, random_state=1)[["source", "target"]].to_dict("records"),
    }
    (pdir / "correction" / "augment_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                                             encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"-> {path}")


if __name__ == "__main__":
    main()
