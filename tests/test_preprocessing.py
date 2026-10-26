import pandas as pd
import pytest

from src.data.split_data import check_leakage, group_split
from src.utils.text_utils import normalize_text, pick_column


def test_normalize_keeps_diacritics_and_case():
    assert normalize_text("  Tôi   yêu\u00a0Việt Nam \u200b") == "Tôi yêu Việt Nam"


def test_normalize_nfc():
    decomposed = "e\u0302\u0301"  # ê + dấu sắc dạng tổ hợp
    assert normalize_text(decomposed) == "\u1ebf"  # ế dựng sẵn


def test_normalize_none():
    assert normalize_text(None) == ""


def test_pick_column_auto_and_error():
    assert pick_column(["Noisy", "clean"], None, ["noisy"], "x") == "Noisy"
    with pytest.raises(KeyError):
        pick_column(["a", "b"], None, ["noisy"], "x")
    with pytest.raises(KeyError):
        pick_column(["a", "b"], "zzz", ["noisy"], "x")


def test_group_split_has_no_leakage():
    rows = []
    for i in range(200):  # 200 câu gốc, mỗi câu 3 biến thể
        for j in range(3):
            rows.append({"source": f"s{i}", "target": f"t{i}_{j}"})
    df = pd.DataFrame(rows)
    tr, va, te = group_split(df, "source", {"train": 0.8, "val": 0.1, "test": 0.1}, seed=42)
    assert len(tr) + len(va) + len(te) == len(df)
    leak = check_leakage(tr, va, te, "source")
    assert all(v["shared_groups"] == 0 for v in leak.values())
    assert len(te) > 0 and len(va) > 0


def test_group_split_by_group_id_keeps_paraphrases_together():
    rows = [{"source": f"s{i}", "target": f"t{i}_{j}", "group_id": str(i)} for i in range(150) for j in range(4)]
    df = pd.DataFrame(rows)
    tr, va, te = group_split(df, "group_id", {"train": 0.8, "val": 0.1, "test": 0.1}, seed=1)
    assert not (set(tr.group_id) & set(te.group_id))
    assert not (set(tr.group_id) & set(va.group_id))
