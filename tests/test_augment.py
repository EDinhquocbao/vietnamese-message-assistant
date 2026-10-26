import random
import unicodedata

from src.data.augment_errors import (
    ERROR_TYPES, change_tone, change_vowel_mark, confuse_consonant, delete_char, make_noisy, transpose,
)


def test_tone_and_vowel_changes_keep_base_letters():
    rng = random.Random(0)
    for _ in range(20):
        w = change_tone("sớm", rng)
        assert w != "sớm" and unicodedata.normalize("NFD", w)[0] == "s" and "m" in w
    assert change_vowel_mark("cô", random.Random(1)) in {"co", "cơ"}


def test_char_level_typos():
    assert delete_char("cùng", random.Random(3)) in {"ùng", "cng", "cùg", "cùn"}
    assert transpose("nhau", random.Random(0)) in {"hnau", "nahu", "nhua"}
    assert confuse_consonant("sớm", random.Random(0)) == "xớm"
    assert confuse_consonant("cùng", random.Random(0)) == "cùn"


def test_make_noisy_changes_only_some_words_and_is_reproducible():
    s = "tí nữa mình cùng nhau làm bài nhé"
    a, ta = make_noisy(s, random.Random(7), max_errors=2)
    b, tb = make_noisy(s, random.Random(7), max_errors=2)
    assert (a, ta) == (b, tb)
    assert a != s and 1 <= len(ta) <= 2 and set(ta) <= set(ERROR_TYPES)
    changed = sum(x != y for x, y in zip(a.split(), s.split()))
    assert len(a.split()) == len(s.split()) and 1 <= changed <= 2


def test_make_noisy_leaves_numbers_and_punctuation():
    s = "Giá 150.000 đồng, 7h30 nhé!"
    for seed in range(20):
        noisy, _ = make_noisy(s, random.Random(seed), max_errors=3)
        assert "150.000" in noisy and "7h30" in noisy


def test_new_word_level_errors():
    from src.data.augment_errors import double_char, strip_diacritics, telex_raw

    assert strip_diacritics("Đường đi học") == "Duong di hoc"
    assert telex_raw("đường") == "dduwowngf"
    assert telex_raw("Tiếng") == "Tieengs"
    assert double_char("đi", random.Random(0)) in {"đđi", "đii"}


def test_fast_typing_noise_profile():
    from src.data.augment_errors import make_fast_typing_noise, strip_diacritics

    cfg = {"p_strip": 1.0, "p_strip_full": 1.0, "typo_counts": {0: 0, 1: 1}, "p_merge": 0.0, "p_clean": 0.0}
    s = "tí nữa mình cùng nhau làm bài nhé"
    noisy, types = make_fast_typing_noise(s, random.Random(3), cfg)
    assert types[0] == "strip_full" and len(types) == 2
    assert noisy != strip_diacritics(s) and noisy == strip_diacritics(noisy)  # có thêm lỗi gõ, không còn dấu
    clean, t2 = make_fast_typing_noise(s, random.Random(3), {**cfg, "p_clean": 1.0})
    assert clean == s and t2 == []
    merged, t3 = make_fast_typing_noise(s, random.Random(1), {**cfg, "p_strip": 0.0, "typo_counts": {0: 1}, "p_merge": 1.0})
    assert t3 == ["merge"] and len(merged.split()) == len(s.split()) - 1
