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
