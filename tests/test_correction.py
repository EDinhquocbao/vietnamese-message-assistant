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
