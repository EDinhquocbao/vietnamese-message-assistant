import pytest

from src.utils.metrics import (
    corpus_bleu, correction_prf, exact_match, overcorrection_rate, paraphrase_report, tokenize, wer, word_edits,
)


def test_tokenize_splits_punctuation():
    assert tokenize("Đi ăn ko?") == ["Đi", "ăn", "ko", "?"]


def test_word_edits_finds_replacement():
    assert word_edits("tôi đi hok", "tôi đi học") == {(2, 3, ("học",))}


def test_prf_perfect_and_copy():
    src, ref = ["tôi đi hok", "an com chua"], ["tôi đi học", "ăn cơm chưa"]
    perfect = correction_prf(src, ref, ref)
    assert perfect["precision"] == perfect["recall"] == 1.0
    copy = correction_prf(src, src, ref)
    assert copy["recall"] == 0.0 and copy["fp"] == 0


def test_prf_penalizes_wrong_fix():
    r = correction_prf(["tôi đi hok"], ["tôi đi hóc"], ["tôi đi học"])
    assert r["tp"] == 0 and r["fp"] == 1 and r["fn"] == 1


def test_wer_ignores_punctuation_attachment():
    assert wer(["ăn cơm chưa ?"], ["ăn cơm chưa?"]) == 0.0


def test_exact_match_and_overcorrection():
    assert exact_match(["a", "b"], ["a", "c"]) == 0.5
    assert overcorrection_rate(["câu đúng", "câu khác"], ["câu đúng", "câu sửa"]) == 0.5


def test_bleu_identity_and_multi_ref():
    s = "hôm nay trời rất đẹp và mát"
    assert corpus_bleu([s], [[s]]) == pytest.approx(100.0)
    # thêm một tham chiếu khớp hoàn toàn thì điểm phải tăng
    assert corpus_bleu([s], [["trời hôm nay đẹp quá", s]]) > corpus_bleu([s], [["trời hôm nay đẹp quá"]])


def test_paraphrase_report_penalizes_copy():
    src = ["hôm nay trời rất đẹp và mát mẻ"]
    refs = [["thời tiết hôm nay rất đẹp và mát mẻ"]]
    copy = paraphrase_report(src, src, refs)
    good = paraphrase_report(src, refs[0], refs)
    assert copy["copy_rate"] == 1.0 and copy["self_bleu"] == pytest.approx(100.0)
    assert good["ibleu"] > copy["ibleu"]
