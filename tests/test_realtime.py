import pytest

from src.lexicon.build import extract_counts
from src.lexicon.candidates import Lexicon
from src.realtime.session import Session


@pytest.fixture(scope="module")
def lex():
    pairs = [("mai di hoc ko", "mai đi học không"), ("m di dau the", "mình đi đâu thế"), ("con yêu quá", "con yêu quá"),
             ("còn yêu quá", "còn yêu quá"), ("người ta đi học", "người ta đi học")] * 3
    uni, bi, mapping = extract_counts([p[0] for p in pairs], [p[1] for p in pairs])
    return Lexicon({"unigram": dict(uni), "bigram": {f"{a}\t{b}": c for (a, b), c in bi.items()},
                    "mapping": {w: dict(c) for w, c in mapping.items()}, "syllables": [], "nsw": {"kcj": ["không có gì"]}})


def test_word_being_typed_is_left_alone(lex):
    s = Session(lex)
    s.sync("mai di ho")
    assert [w.raw for w in s.words] == ["mai", "di"]
    s.sync("mai di hoc ")
    assert [w.raw for w in s.words] == ["mai", "di", "hoc"]


def test_telex_is_auto_applied_only_when_sure(lex):
    s = Session(lex)
    s.sync("nguowif con ")
    assert s.words[0].shown == "người" and s.words[0].auto
    assert s.words[1].shown == "con" and not s.words[1].auto


def test_ambiguous_word_keeps_raw_text_and_is_flagged(lex):
    s = Session(lex)
    s.sync("con yeu qua ")
    assert s.text() == "con yeu qua"
    state = s.state()
    assert state[2]["uncertain"] and "quá" in state[2]["options"]


def test_chosen_word_is_locked_and_never_changes(lex):
    s = Session(lex)
    s.sync("con yeu ")
    s.choose(0, "còn")
    s.sync("con yeu qua di hoc ")
    assert s.words[0].shown == "còn" and s.words[0].locked and s.words[0].best == "còn"


def test_old_words_lock_automatically(lex):
    s = Session(lex, lock_after=2)
    s.sync("mai di hoc ko ")
    assert [w.locked for w in s.words] == [True, True, False, False]


def test_locked_word_with_better_suggestion_can_still_be_fixed(lex):
    s = Session(lex, lock_after=2)
    s.sync("mai di hoc ko ")
    assert s.words[1].locked and s.words[1].shown == "di"
    assert s.state()[1]["uncertain"] and "đi" in s.state()[1]["options"]
    before = s.words[1].options[:]
    s.sync("mai di hoc ko nua ")
    assert s.words[1].options == before  # khóa: thứ tự gợi ý không đổi
    s.choose(1, "đi")
    assert s.words[1].shown == "đi" and not s.state()[1]["uncertain"]


def test_editing_earlier_text_recomputes_from_first_change(lex):
    s = Session(lex)
    s.sync("mai di hoc ")
    s.sync("mai ve hoc ")
    assert [w.raw for w in s.words] == ["mai", "ve", "hoc"]


def test_sync_accepts_text_after_autoreplace(lex):
    s = Session(lex)
    s.sync("nguowif ta ")
    first = s.words[0]
    s.sync("người ta di ")
    assert s.words[0] is first and s.words[0].raw == "nguowif"


def test_multi_word_choice_survives_sync(lex):
    s = Session(lex)
    s.sync("kcj nha ")
    s.choose(0, "không có gì")
    s.sync("không có gì nha mai ")
    assert s.words[0].locked and s.words[0].shown == "không có gì"
    assert [w.raw for w in s.words[1:]] == ["nha", "mai"]


def test_refine_reorders_only_unlocked_words(lex):
    s = Session(lex, beta=0.0, lock_after=1)
    s.sync("con yeu qua ")
    locked_before = s.words[0].options[:]

    def scorer(sources, cands):  # mô hình giả: thích câu giữ nguyên chữ "qua"
        return [10.0 if c.endswith(" qua") else 0.0 for c in cands]

    s.refine(scorer)
    assert s.words[0].options == locked_before
    assert s.words[-1].best == "qua"


def test_sentences_are_whole_sentences_keeping_the_word_being_typed(lex):
    s = Session(lex)
    text = "Con yeu qua, di ho"
    s.sync(text)
    rows = s.sentences(text)
    assert 1 <= len(rows) <= 3 and len({r["text"] for r in rows}) == len(rows)
    assert all(r["text"].endswith(", đi ho") or r["text"].endswith(", di ho") for r in rows)
    assert rows[0]["text"].startswith("Con yêu") and all(r["text"][:1] == "C" for r in rows)  # giữ chữ hoa
    assert rows[0]["picks"] == [w.best for w in s.words]  # dòng đầu = mọi gợi ý đầu


def test_only_uncertain_words_vary_between_sentences(lex):
    s = Session(lex)
    text = "nguowif ta di hoc "
    s.sync(text)
    rows = s.sentences(text)
    assert all(r["text"].startswith("người ta ") for r in rows)  # Telex chắc chắn: không có phương án khác


def test_picking_a_sentence_locks_its_words(lex):
    s = Session(lex)
    text = "con yeu qua "
    s.sync(text)
    row = s.sentences(text)[-1]
    s.pick(row["picks"])
    s.sync(row["text"])
    assert s.text() + " " == row["text"]
    assert all(w.locked for w in s.words if w.chosen) and not any(st["uncertain"] for st in s.state())
