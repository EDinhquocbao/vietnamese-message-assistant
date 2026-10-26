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
