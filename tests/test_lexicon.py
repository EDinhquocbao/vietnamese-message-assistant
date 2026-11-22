import pytest

from src.lexicon.build import extract_counts
from src.lexicon.candidates import Lexicon, match_case
from src.lexicon.hybrid import HybridCorrector
from src.lexicon.telex import decode


@pytest.mark.parametrize("typed,expected", [
    ("conf", "còn"), ("cofn", "còn"), ("nguowif", "người"), ("dduowngf", "đường"), ("toois", "tối"),
    ("tieengs", "tiếng"), ("quas", "quá"), ("gias", "giá"), ("to6i1", "tối"), ("d9i", "đi"),
])
def test_telex_vni_decode(typed, expected):
    assert expected in decode(typed)


def test_telex_keeps_both_tone_styles():
    assert set(decode("hoaf")) == {"hòa", "hoà"}


@pytest.mark.parametrize("word", ["con", "ok", "k9", "123", "không"])
def test_telex_ignores_plain_tokens(word):
    assert decode(word) == []


@pytest.fixture(scope="module")
def lex():
    pairs = [("mai di hoc ko", "mai đi học không"), ("m di dau the", "mình đi đâu thế"), ("m di dau the", "mày đi đâu thế"),
             ("con yêu quá", "con yêu quá"), ("còn yêu quá", "còn yêu quá"), ("Nhà em ở Hà Nội", "Nhà em ở Hà Nội"),
             ("ny em dep", "người yêu em đẹp"), ("ko ?", "không ?"), ("người người đi", "người người đi")] * 2
    uni, bi, mapping = extract_counts([p[0] for p in pairs], [p[1] for p in pairs])
    return Lexicon({"unigram": dict(uni), "bigram": {f"{a}\t{b}": c for (a, b), c in bi.items()},
                    "mapping": {w: dict(c) for w, c in mapping.items()}, "syllables": ["đẹp", "ruby", "có", "gì"],
                    "nsw": {"kcj": ["không có gì"]}})


@pytest.mark.parametrize("token", ["con", "ko", "nguowif", "zzzq", "m", "Hà", "2026", ","])
@pytest.mark.parametrize("k", [1, 2, 8, None])
def test_options_always_include_the_word_itself(lex, token, k):
    assert token.lower() in [c for c, _ in lex.options(token, k)]


def test_candidates_cover_sources(lex):
    assert "không" in lex.channel("ko")                # bảng từ train
    assert "không có gì" in lex.channel("kcj")         # từ điển viết tắt
    assert "người" in lex.channel("nguowif")           # Telex
    assert {"con", "còn"} <= set(lex.channel("còn"))   # đổi dấu
    assert "mình" in lex.channel("m") and "mày" in lex.channel("m")  # viết tắt nhiều nghĩa giữ cả hai


def test_noisy_targets_are_rejected(lex):
    assert not any("?" in c for c in lex.channel("ko"))


def test_restrict_does_not_turn_names_into_common_words(lex):
    assert "người" not in lex.channel("Ngườii", restrict=True)
    assert "người" in lex.channel("ngườii")


@pytest.mark.parametrize("raw,cand,expected", [
    ("Mai", "mai", "Mai"), ("iPhone", "iphone", "iPhone"), ("Ko", "không", "Không"), ("KO", "không", "KHÔNG"),
    ("HN", "hà nội", "Hà Nội"), ("ko", "không", "không"),
])
def test_match_case(raw, cand, expected):
    assert match_case(raw, cand) == expected


def test_best_paths_keep_case_and_punctuation(lex):
    assert lex.best_paths("Mai di hoc ko, nhé?", k=8, n=1)[0].text.startswith("Mai đi học không,")


def test_build_uses_only_given_pairs():
    uni, _, mapping = extract_counts(["ko di"], ["không đi"])
    assert "đi" in uni and "học" not in uni and mapping["ko"] == {"không": 1}


def test_guard_rejects_edit_outside_candidates(lex):
    g = HybridCorrector("guard", lex)
    assert g.guard("em thích ruby", "em thích rực rỡ") == "em thích ruby"
    assert g.guard("mai di hoc ko", "mai đi học không") == "mai đi học không"


def test_guard_restores_deleted_words(lex):
    g = HybridCorrector("guard", lex)
    assert g.guard("đi đâu đi đâu thế", "đi đâu thế") == "đi đâu đi đâu thế"


def test_prior_prefers_edits_in_dictionary(lex):
    g = HybridCorrector("rerank", lex, penalty=-8.0)
    assert g.prior("mai di hoc ko", "mai đi học không") > g.prior("mai di hoc ko", "mai xin nghỉ không")
