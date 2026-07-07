"""P08 — INV-11 (E-REVIEW-LOST) ĐÃ được cắm vào Transaction.validate_staged (spec 10.3a).

Trước fix: check_review_not_lost chỉ là hàm mồ côi (chỉ test unit lẻ), KHÔNG chạy ở luồng
/review /done /forget → mất review item in_review/need_redo mà không bị chặn.

Cách ly: stub validate_full_semantic → chỉ còn _check_review_preservation chạy → chứng minh wiring.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import transaction as TX  # noqa: E402
import validate as V      # noqa: E402
import vault_io as VIO    # noqa: E402

REL = "topics/docker/lessons/lesson-001/lesson_state.md"

_HEAD = """---
schema: lesson_state
schema_version: 1
lesson_id: docker/lesson-001
title: t
status: in_progress
created: 2026-06-30
updated: 2026-06-30
objective: o
mastery:
  concept: {score: 0, evidence: []}
  explain: {score: 0, evidence: []}
  apply: {score: 0, evidence: []}
  critique: {score: 0, evidence: []}
  teachback: {score: 0, evidence: []}
"""


def _ls(items_block: str) -> str:
    return _HEAD + items_block + "---\n"


LS_INREVIEW = _ls("review_items:\n  - id: rv-001\n    mastery_state: in_review\n")
LS_NEW = _ls("review_items:\n  - id: rv-001\n    mastery_state: new\n")
LS_EMPTY = _ls("review_items: []\n")


def _setup(tmp_path, original: str):
    p = tmp_path / REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(original, encoding="utf-8")
    return VIO.content_hash(p)


def _staged_codes(tmp_path, monkeypatch, original, staged, tombstones=None):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    monkeypatch.setattr(V, "validate_full_semantic", lambda *a, **k: None)  # cách ly INV-11
    h = _setup(tmp_path, original)
    tx = TX.Transaction(tmp_path, level="full")
    tx.begin([TX.Write(REL, staged.encode("utf-8"), expected_read_hash=h)], tombstones=tombstones)
    tx.stage()
    rep = tx.validate_staged(ROOT, "full")
    tx.abort()
    return {e["error_code"] for e in rep.errors}


# ---- 1. drop item in_review, KHÔNG tombstone → E-REVIEW-LOST ----------
def test_inreview_dropped_without_tombstone(tmp_path, monkeypatch):
    codes = _staged_codes(tmp_path, monkeypatch, LS_INREVIEW, LS_EMPTY)
    assert "E-REVIEW-LOST" in codes


# ---- 2. drop item in_review CÓ tombstone khớp → KHÔNG lỗi ------------
def test_inreview_dropped_with_tombstone(tmp_path, monkeypatch):
    tomb = TX.Tombstone(op="delete", scope="item", lesson_id="docker/lesson-001",
                        item_ids=["rv-001"], reason="học lại", confirmed_by_user=True)
    codes = _staged_codes(tmp_path, monkeypatch, LS_INREVIEW, LS_EMPTY, tombstones=[tomb])
    assert "E-REVIEW-LOST" not in codes


# ---- 3. drop item 'new' (không được bảo vệ) → KHÔNG lỗi --------------
def test_new_item_dropped_allowed(tmp_path, monkeypatch):
    codes = _staged_codes(tmp_path, monkeypatch, LS_NEW, LS_EMPTY)
    assert "E-REVIEW-LOST" not in codes


# ---- 4. XOÁ hẳn file lesson_state (op=delete) in_review, không tombstone → LOST
def test_delete_file_without_tombstone(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    monkeypatch.setattr(V, "validate_full_semantic", lambda *a, **k: None)
    h = _setup(tmp_path, LS_INREVIEW)
    tx = TX.Transaction(tmp_path, level="full")
    tx.begin([TX.Write(REL, None, expected_read_hash=h, op="delete")])
    tx.stage()
    rep = tx.validate_staged(ROOT, "full")
    tx.abort()
    assert "E-REVIEW-LOST" in {e["error_code"] for e in rep.errors}
