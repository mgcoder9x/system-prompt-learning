"""P07b-2a tests — claims: cấu trúc (INV-15) + tiền đề C (INV-14).

Test thuần trên _check_claims (list claim + file) — cách ly từng mã lỗi
E-CLAIM-UNCLASSED / E-CLAIM-DRAFTREASON / E-CLAIM-WEAKBASE. + end-to-end demo PASS.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"


def _codes(claims):
    rep = V.Report()
    V._check_claims([(c, "topic.md") for c in claims], rep)
    return [e["error_code"] for e in rep.errors]


def _B(id, status="confirmed", **kw):
    d = {"id": id, "class": "B", "status": status, "text": "t", "source_refs": ["src-1#a1"],
         "premise_refs": [], "draft_reason": None}
    d.update(kw)
    return d


# ---- 1. claims hợp lệ (B confirmed, C confirmed đủ tiền đề, draft có reason) → sạch
def test_valid_claims_pass():
    claims = [
        _B("clm-a", **{"class": "A"}),
        _B("clm-b"),
        {"id": "clm-c", "class": "C", "status": "confirmed", "text": "suy luận",
         "source_refs": [], "premise_refs": ["clm-a", "clm-b"], "draft_reason": None},
        {"id": "clm-d", "class": "D", "status": "draft", "text": "phán đoán",
         "source_refs": [], "premise_refs": [], "draft_reason": "chưa nguồn hoá"},
    ]
    assert _codes(claims) == []


# ---- 2. thiếu class → E-CLAIM-UNCLASSED -------------------------------
def test_missing_class():
    claims = [{"id": "clm-x", "status": "confirmed", "text": "t"}]
    assert "E-CLAIM-UNCLASSED" in _codes(claims)


# ---- 3. draft thiếu draft_reason → E-CLAIM-DRAFTREASON ----------------
def test_draft_missing_reason():
    claims = [{"id": "clm-x", "class": "D", "status": "draft", "text": "t",
               "draft_reason": None}]
    codes = _codes(claims)
    assert "E-CLAIM-DRAFTREASON" in codes
    assert "E-CLAIM-UNCLASSED" not in codes  # đủ id/class/status/text


# ---- 4. C confirmed không có tiền đề → E-CLAIM-WEAKBASE ---------------
def test_C_no_premises():
    claims = [{"id": "clm-c", "class": "C", "status": "confirmed", "text": "t",
               "premise_refs": []}]
    assert "E-CLAIM-WEAKBASE" in _codes(claims)


# ---- 5. C confirmed với tiền đề là draft → E-CLAIM-WEAKBASE -----------
def test_C_premise_is_draft():
    claims = [
        {"id": "clm-d", "class": "B", "status": "draft", "text": "t", "draft_reason": "r"},
        {"id": "clm-c", "class": "C", "status": "confirmed", "text": "t",
         "premise_refs": ["clm-d"]},
    ]
    assert "E-CLAIM-WEAKBASE" in _codes(claims)


# ---- 6. C confirmed với tiền đề lớp D → E-CLAIM-WEAKBASE --------------
def test_C_premise_is_classD():
    claims = [
        {"id": "clm-dd", "class": "D", "status": "confirmed", "text": "t"},
        {"id": "clm-c", "class": "C", "status": "confirmed", "text": "t",
         "premise_refs": ["clm-dd"]},
    ]
    assert "E-CLAIM-WEAKBASE" in _codes(claims)


# ---- 7. C confirmed với tiền đề A/B confirmed → KHÔNG weakbase --------
def test_C_premise_valid():
    claims = [
        {"id": "clm-a", "class": "A", "status": "confirmed", "text": "t"},
        {"id": "clm-b", "class": "B", "status": "confirmed", "text": "t",
         "source_refs": ["src-1#a1"]},
        {"id": "clm-c", "class": "C", "status": "confirmed", "text": "t",
         "premise_refs": ["clm-a", "clm-b"]},
    ]
    assert "E-CLAIM-WEAKBASE" not in _codes(claims)


# ---- 7b. C confirmed với tiền đề trỏ claim KHÔNG TỒN TẠI (dangling) → E-CLAIM-WEAKBASE
#      (khoá hồi quy: by_id.get(pid) is None → phải bắt, không im lặng bỏ qua ref treo)
def test_C_premise_nonexistent_is_weakbase():
    claims = [{"id": "clm-c", "class": "C", "status": "confirmed", "text": "t",
               "premise_refs": ["clm-ghost"]}]
    assert "E-CLAIM-WEAKBASE" in _codes(claims)


# ---- 8. thiếu id/text → E-CLAIM-UNCLASSED -----------------------------
def test_missing_id_and_text():
    claims = [{"class": "B", "status": "confirmed"}]  # thiếu id + text
    assert _codes(claims).count("E-CLAIM-UNCLASSED") >= 2


# ---- 9. end-to-end: demo vault (không claim file) → full semantic PASS -
def test_demo_vault_still_passes():
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, VAULT_SRC, rep, now=datetime(2026, 7, 1, tzinfo=timezone.utc))
    assert rep.ok(), rep.errors
