"""P02 tests — canonical hash + normalize (spec mục 4, 9.6, INV-09/22b)."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import canonical as C  # noqa: E402


# ---- canonical_hash -----------------------------------------------------
def test_hash_stable_across_runs():
    data = {"b": 1, "a": [{"x": "đúng", "y": "kernel"}]}
    h1 = C.canonical_hash(data)
    h2 = C.canonical_hash(data)
    assert h1 == h2 and h1.startswith("sha256:")


def test_hash_key_order_independent():
    assert C.canonical_hash({"a": 1, "b": 2}) == C.canonical_hash({"b": 2, "a": 1})


def test_hash_vietnamese_not_escaped():
    # ensure_ascii=False → 'đ' nguyên trạng trong chuỗi canonical
    js = C.canonical_json({"k": "đdđ"})
    assert "đ" in js and "\\u0111" not in js


def test_hash_date_obj_equals_string():
    assert C.canonical_hash({"d": date(2026, 7, 12)}) == C.canonical_hash({"d": "2026-07-12"})


def test_hash_rejects_raw_float():
    with pytest.raises(C.ECanonicalFloat):
        C.canonical_hash({"s": 12.34})


def test_review_schedule_domain_hash():
    # miền băm review_schedule (v2.6/F-B): 4 field, KHÔNG due_at_utc
    data = [
        {"lesson_id": "t/lesson-001", "item_id": "rv-001",
         "due_date": "2026-07-12", "mastery_state": "in_review"},
    ]
    h = C.canonical_hash(data)
    # đổi field ngoài miền (thêm due_at_utc) KHÔNG được tính vào (caller không đưa vào)
    assert h == C.canonical_hash([dict(data[0])])


# ---- normalize_yaml_object ----------------------------------------------
def test_normalize_keeps_date_type():
    out = C.normalize_yaml_object({"created": date(2026, 6, 30), "score": 2})
    assert out["created"] == date(2026, 6, 30)  # giữ type
    assert out["score"] == 2


def test_normalize_stringifies_declared_str_field():
    # due_at_utc schema muốn str; YAML có thể ép; ép hình thức về str
    out = C.normalize_yaml_object({"due_at_utc": date(2026, 7, 12)}, str_fields={"due_at_utc"})
    assert out["due_at_utc"] == "2026-07-12"


# ---- normalize_for_match (INV-22b) --------------------------------------
def test_match_strips_bold():
    q = C.normalize_for_match("chia sẻ **kernel**")
    t = C.normalize_for_match("Container chia sẻ kernel với host")
    assert q in t


def test_match_curly_quotes_and_spaces():
    assert C.normalize_for_match("“abc”\n\n  def") == C.normalize_for_match('"abc" def')


def test_match_keeps_vietnamese_diacritics():
    assert C.normalize_for_match("má") != C.normalize_for_match("ma")


def test_match_keeps_underscores_in_identifiers():
    out = C.normalize_for_match("gọi `__init__` và a_b")
    assert "__init__" in out and "a_b" in out
