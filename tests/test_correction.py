import pandas as pd

from src.correction.dataset import filter_by_length, load_pairs
from src.correction.predict import restore_unknown


def test_restore_unknown_fills_in_order():
    assert restore_unknown("2<unk> được bữa rồi <unk>", ["$", "=))"]) == "2$ được bữa rồi =))"


def test_restore_unknown_drops_extra_and_keeps_plain_text():
    assert restore_unknown("a <unk> b <unk>", ["😂"]) == "a 😂 b"
    assert restore_unknown("tôi đi học", []) == "tôi đi học"


def test_filter_by_length_drops_long_pairs():
    df = pd.DataFrame({"source": ["a", "b", "c"], "target": ["a", "b", "c"]})
    src_lens, tgt_lens = [3, 10, 3], [3, 3, 9]
    kept = filter_by_length(df, src_lens, tgt_lens, max_source_len=5, max_target_len=5)
    assert kept.source.tolist() == ["a"]


def test_load_pairs_samples_reproducibly(tmp_path):
    p = tmp_path / "x.jsonl"
    pd.DataFrame({"source": list("abcdefgh"), "target": list("abcdefgh")}).to_json(p, orient="records", lines=True)
    a, b = load_pairs(p, max_samples=3, seed=1), load_pairs(p, max_samples=3, seed=1)
    assert len(a) == 3 and a.source.tolist() == b.source.tolist()
    assert len(load_pairs(p)) == 8


def test_stress_inputs_are_reproducible_and_noisy(tmp_path):
    from src.correction.stress_test import CATEGORIES, build_inputs, score

    p = tmp_path / "t.jsonl"
    sents = ["hôm nay mình đi học sớm nhé bạn", "tối nay cả nhóm cùng nhau làm bài", "mai trời mưa to lắm đó"]
    pd.DataFrame({"source": sents, "target": sents}).to_json(p, orient="records", lines=True, force_ascii=False)
    a, b = build_inputs(p, 3), build_inputs(p, 3)
    assert a.equals(b) and set(a.category) == set(CATEGORIES)
    noisy = a[a.category != "cau_dung"]
    assert (noisy.input != noisy.target).all()
    s = score(a.assign(pred=a.target))
    assert all(v["exact_match"] == 1.0 and v["wer"] == 0.0 for v in s.values())


def test_merge_nbest_normalizes_and_merges():
    import math

    from src.correction.predict import merge_nbest

    r = merge_nbest([("a", math.log(0.5)), ("b", math.log(0.25)), ("a", math.log(0.25))])
    assert [x["text"] for x in r] == ["a", "b"]
    assert abs(r[0]["prob"] - 0.75) < 1e-9 and abs(sum(x["prob"] for x in r) - 1) < 1e-9


def test_restore_symbols_from_source():
    from src.correction.predict import restore_symbols

    assert restore_symbols("10 điểm… nhưng… k có", "10 điểm... nhưng... không có") == "10 điểm… nhưng… không có"
    assert restore_symbols("high note =))))))", "high note =))))))))))))") == "high note =))))))"
    assert restore_symbols("đẹp quá...", "đẹp quá...") == "đẹp quá..."      # nguồn dùng "..." thì giữ
    assert restore_symbols("ok :))", "ok :)) nha") == "ok :)) nha"
