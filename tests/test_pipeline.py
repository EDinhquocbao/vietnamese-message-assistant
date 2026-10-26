import numpy as np

from src.paraphrase.generate import dedupe_candidates
from src.pipeline.ranker import Ranker, protected_spans, violates_protected


def test_dedupe_drops_copies_and_duplicates():
    out = dedupe_candidates("Bạn rảnh không?", ["bạn rảnh không", "Bạn có rảnh không?", "Bạn có rảnh không?", ""])
    assert out == ["Bạn có rảnh không?"]


def test_protected_spans_finds_numbers_names_negation():
    p = protected_spans("Tuần sau Lan về Đà Nẵng lúc 7h30, đơn #A1023 giá 150.000 không?")
    assert {"7h30", "#A1023", "150.000"} <= p["numbers"]
    assert {"Lan", "Đà Nẵng"} <= p["names"]
    assert p["negation"] is True


def test_violates_protected():
    src = "Mình chưa nhận được 200k của Minh"
    assert not violates_protected(src, "Minh vẫn chưa chuyển cho mình 200k")
    assert violates_protected(src, "Mình đã nhận được 200k của Minh")       # mất phủ định
    assert violates_protected(src, "Mình chưa nhận được 300k của Minh")     # đổi số
    assert violates_protected(src, "Mình chưa nhận được 200k của anh ấy")   # mất tên
    assert violates_protected("Mình nhận được rồi", "Mình không nhận được")  # thêm phủ định


def _fake_encode(texts):
    """Embedding giả: câu chứa 'xa' thì khác nghĩa, còn lại gần như trùng câu gốc."""
    vecs = [[0.0, 1.0] if "xa" in t else [1.0, 0.05 * (i % 3)] for i, t in enumerate(texts)]
    v = np.array(vecs)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def test_ranker_filters_and_limits():
    r = Ranker(encode=_fake_encode, top_k=2, min_similarity=0.8, max_overlap=0.9)
    src = "Bạn gửi file cho mình chưa?"
    cands = ["Bạn đã gửi tệp cho mình chưa?", "Bạn gửi file cho mình chưa ạ?", "Bạn ở xa lắm",
             "Bạn gửi file cho mình rồi", "File đó bạn gửi mình chưa vậy?"]
    out = r.rank(src, cands)
    texts = [s["text"] for s in out]
    assert len(texts) == 2
    assert "Bạn ở xa lắm" not in texts                  # khác nghĩa
    assert "Bạn gửi file cho mình rồi" not in texts     # mất phủ định "chưa"
    assert all(0.8 <= s["similarity"] <= 1.0 for s in out)


def test_describe_edits():
    from src.pipeline.assistant import describe_edits

    assert describe_edits("mai di hoc ko", "mai đi học không") == [{"from": "di hoc ko", "to": "đi học không"}]
    assert describe_edits("đã đúng", "đã đúng") == []


def test_assistant_runs_with_fake_models():
    from src.pipeline.assistant import Assistant

    class FakePara:
        def candidates(self, texts):
            return [["Bạn có rảnh vào chiều mai không?", "Chiều mai bạn rảnh chứ?"] for _ in texts]

    a = Assistant(lambda xs: ["Chiều mai bạn có rảnh không?" for _ in xs], FakePara(),
                  Ranker(encode=_fake_encode, top_k=3))
    r = a.run("chieu mai ban co ranh ko")
    assert r["corrected"] == "Chiều mai bạn có rảnh không?" and r["edits"]
    assert [s["text"] for s in r["suggestions"]] == ["Bạn có rảnh vào chiều mai không?"]
    assert any(c["rejected"] == "đổi phủ định" for c in r["candidates"])


def test_integration_keeps_must_keep_items():
    from src.pipeline.evaluate_integration import keeps

    assert keeps("Sáng mai 7h30 họp ở phòng 302 nhé", "7h30;302")
    assert not keeps("Sáng mai họp ở phòng 302 nhé", "7h30;302")
    assert keeps("mai đi học không", "ko")       # 'ko' được sửa thành 'không' vẫn tính là giữ phủ định
    assert not keeps("mai đi học nhé", "ko")
    assert keeps("bất kỳ", "")


def test_clean_candidate_fixes_artifacts():
    from src.paraphrase.generate import clean_candidate

    assert clean_candidate("Mình đã gửi rồi", 'Mình đã gửi đi rồi."') == "Mình đã gửi đi rồi."
    assert clean_candidate("Em bị ốm ạ", "Em bị bệnh ạ ạ.") == "Em bị bệnh ạ."
    assert clean_candidate("nói sớm sớm nhé", "nói sớm sớm nha") == "nói sớm sớm nha"  # lặp có sẵn ở câu gốc
    assert clean_candidate("a", 'Anh nói "được" rồi') == 'Anh nói "được" rồi'          # ngoặc cân bằng


def test_unknown_words_flags_lowercase_oov_only():
    from src.pipeline.assistant import unknown_words

    vocab = {"tí", "nữa", "mình", "cùn", "làm", "bài", "nhé", "về"}
    assert unknown_words("tí nữa mình cùn nahu làm bài nhé", vocab) == ["nahu"]
    assert unknown_words("Lan về 7h30 nhé!", vocab) == []  # tên riêng, số, dấu câu không tính


def test_assistant_hides_suggestions_when_correction_has_oov():
    from src.pipeline.assistant import Assistant

    class FakePara:
        def candidates(self, texts):
            return [["Sự nahu nhé"] for _ in texts]

    a = Assistant(lambda xs: list(xs), FakePara(), Ranker(encode=_fake_encode), vocab={"tí", "nữa", "nhé"})
    r = a.run("tí nữa nahu nhé")
    assert r["unknown_words"] == ["nahu"] and r["suggestions"] == []


def test_uncertain_words_lists_alternatives():
    from src.pipeline.assistant import uncertain_words

    alts = [{"text": "ngày mai khi nào học anh", "prob": 0.6},
            {"text": "người yêu mai khi nào học anh", "prob": 0.3},
            {"text": "ngày mai khi nào học à", "prob": 0.05}]  # dưới ngưỡng -> bỏ
    assert uncertain_words(alts, min_prob=0.1) == [{"span": "ngày", "options": ["người yêu"]}]
    assert uncertain_words(alts[:1]) == []


def test_assistant_uses_nbest_when_available():
    from src.pipeline.assistant import Assistant

    class NBestCorrector:
        def nbest(self, texts):
            return [[{"text": "ngày mai đi học", "prob": 0.7}, {"text": "người yêu mai đi học", "prob": 0.3}]
                    for _ in texts]

    class FakePara:
        def candidates(self, texts):
            return [[] for _ in texts]

    r = Assistant(NBestCorrector(), FakePara(), Ranker(encode=_fake_encode)).run("ngy mai di hoc")
    assert r["corrected"] == "ngày mai đi học"
    assert r["uncertain"] == [{"span": "ngày", "options": ["người yêu"]}]


def test_ranker_nli_rejects_non_entailing_candidates():
    def fake_entail(premises, hypotheses):  # "không nên" mâu thuẫn với "đừng quên"
        return [0.05 if ("Không nên" in p or "Không nên" in h) else 0.95 for p, h in zip(premises, hypotheses)]

    r = Ranker(encode=_fake_encode, entail=fake_entail, min_entailment=0.5, top_k=3)
    rows = r.score_all("Đừng quên mua sữa cho bé nhé", ["Đừng quên mua sữa cho con nha", "Không nên mua sữa cho bé nhé"])
    by_text = {x["text"]: x for x in rows}
    assert by_text["Đừng quên mua sữa cho con nha"]["rejected"] is None
    assert by_text["Không nên mua sữa cho bé nhé"]["rejected"].startswith("không suy ra nhau")
    assert by_text["Đừng quên mua sữa cho con nha"]["entailment"] == 0.95
