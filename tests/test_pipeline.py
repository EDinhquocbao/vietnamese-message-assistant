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
    case_only = [{"text": "Đừng quên nhé", "prob": 0.6}, {"text": "đừng quên nhé", "prob": 0.4}]
    assert uncertain_words(case_only) == []


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


def test_choices_merge_trivial_variants_and_limit():
    from src.pipeline.assistant import choices

    alts = [{"text": "người mai ăn gì không", "prob": 0.42}, {"text": "Người mai ăn gì không?", "prob": 0.10},
            {"text": "ngày mai ăn gì không", "prob": 0.21}, {"text": "người yêu mai ăn gì không", "prob": 0.16},
            {"text": "người mãi ăn gì không", "prob": 0.1}, {"text": "ngừi mai ăn gì không", "prob": 0.01}]
    out = choices(alts, k=3, min_prob=0.02)
    assert [c["text"] for c in out] == ["người mai ăn gì không", "ngày mai ăn gì không", "người yêu mai ăn gì không"]
    assert abs(out[0]["prob"] - 0.52) < 1e-9          # gộp biến thể chỉ khác hoa/dấu câu cuối
    assert choices([{"text": "a", "prob": 1.0}]) == [{"text": "a", "prob": 1.0}]


def test_assistant_suggest_for_chosen_option():
    from src.pipeline.assistant import Assistant

    class FakePara:
        def candidates(self, texts):
            return [[f"Gợi ý cho: {t}"] for t in texts]

    a = Assistant(lambda xs: list(xs), FakePara(), Ranker(encode=_fake_encode, max_overlap=1.0, min_similarity=0.0))
    corr = a.correct("ngy mai di hoc")
    assert corr["choices"][0]["text"] == "ngy mai di hoc"
    s = a.suggest("ngy mai di hoc", "ngày mai đi học")
    assert s["corrected"] == "ngày mai đi học" and s["edits"]
    assert [x["text"] for x in s["suggestions"]] == ["Gợi ý cho: ngày mai đi học"]


def test_rq3_judge_and_summarize():
    import pandas as pd

    from src.pipeline.rq3 import judge, summarize

    r = Ranker(encode=_fake_encode, entail=lambda ps, hs: [0.9] * len(ps), min_similarity=0.8, min_entailment=0.17)
    vocab = {"mai", "đi", "học", "nhé"}
    judged = judge(r, vocab, ["mai đi học", "mai đi học"], [["mai đi học nhé", "mai di hoc"], []])
    assert [j["ok"] for j in judged[0]] == [True, False]  # "di hoc" còn từ lạ -> không sạch
    assert judged[1] == []
    s = summarize(pd.DataFrame({"judged": judged, "target": ["mai đi học"] * 2}))
    assert s["top1_ok"] == 0.5 and s["any_ok"] == 0.5 and s["has_suggestion"] == 0.5 and s["clean"] == 0.5


def test_manual_eval_scoring_and_review():
    import pandas as pd

    from src.pipeline.manual_eval import apply_review, score_ratings

    ratings = pd.DataFrame({"Mã câu": ["M01", "M01", "M02", "M02", "M03"], "Gợi ý số": [1, 2, 1, 2, 1],
                            "Chấp nhận": [0, 1, 1, 0, None], "Lý do (nếu 0)": ["Đảo vai (ai làm gì cho ai)", None, None, None, None]})
    s = score_ratings(ratings)
    assert s["n_messages"] == 2 and s["n_incomplete"] == 1        # M03 chưa chấm
    assert s["top1_acceptance"] == 0.5 and s["top3_acceptance"] == 1.0
    assert s["reasons"] == {"Đảo vai (ai làm gì cho ai)": 1, "(không ghi)": 1}

    cases = pd.DataFrame({"id": ["A01", "A02", "A03", "A04"], "expected_correction": ["a", "b", "c", "d"],
                          "must_keep": ["", "8h", "", ""], "status": ["draft"] * 4})
    review = pd.DataFrame({"id": ["A01", "A02", "A03", "A04"], "decision": ["giữ ", "Sửa", "Bỏ", None],
                           "new_correction": [None, "bb", None, None], "new_must_keep": [None, "9h", None, None]})
    out, counts = apply_review(cases, review)
    assert list(out.id) == ["A01", "A02", "A04"]
    assert list(out.status) == ["approved", "approved", "draft"]
    assert out.set_index("id").loc["A02", "expected_correction"] == "bb"
    assert out.set_index("id").loc["A02", "must_keep"] == "9h"
    assert counts == {"Giữ": 1, "Sửa": 1, "Bỏ": 1, "chưa duyệt": 1}
