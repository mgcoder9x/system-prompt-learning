"""P09 tests — build_review_schedule / build_assessment (spec 4 + 7).

Dùng SimpleNamespace để cô lập P09 (views chỉ đọc lesson_id/review_items/status/mastery).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import views as VW  # noqa: E402

AXES = VW.AXES


def rv(rid, due, ms, **extra):
    return NS(id=rid, card=NS(due_date=date.fromisoformat(due), **extra), mastery_state=ms)


def lesson(lid, items=(), status="in_progress", scores=None):
    scores = scores or {ax: 0 for ax in AXES}
    mastery = NS(**{ax: NS(score=scores[ax]) for ax in AXES})
    return NS(lesson_id=lid, review_items=list(items), status=status, mastery=mastery)


# ---- review_schedule ----------------------------------------------------
def test_schedule_sorted_by_due_then_ids():
    lessons = [
        lesson("t/l2", [rv("rv-002", "2026-07-10", "in_review")]),
        lesson("t/l1", [rv("rv-001", "2026-07-12", "new"), rv("rv-003", "2026-07-08", "need_redo")]),
    ]
    out = VW.build_review_schedule(lessons)
    order = [(it["item_id"], it["due_date"].isoformat()) for it in out["items"]]
    assert order == [("rv-003", "2026-07-08"), ("rv-002", "2026-07-10"), ("rv-001", "2026-07-12")]


def test_schedule_deterministic():
    lessons = [lesson("t/l1", [rv("rv-001", "2026-07-12", "new")])]
    a = VW.build_review_schedule(lessons)
    b = VW.build_review_schedule(lessons)
    assert a == b
    assert a["generated_from_hash"].startswith("sha256:")


def test_schedule_hash_ignores_out_of_domain_field():
    """Đổi field NGOÀI miền băm (difficulty/due_at_utc) → hash KHÔNG đổi (v2.6/F-B)."""
    base = [lesson("t/l1", [rv("rv-001", "2026-07-12", "new", difficulty=5.0, due_at_utc="X")])]
    other = [lesson("t/l1", [rv("rv-001", "2026-07-12", "new", difficulty=9.9, due_at_utc="Y")])]
    assert VW.build_review_schedule(base)["generated_from_hash"] == \
           VW.build_review_schedule(other)["generated_from_hash"]


def test_schedule_hash_changes_on_due_date():
    a = VW.build_review_schedule([lesson("t/l1", [rv("rv-001", "2026-07-12", "new")])])
    b = VW.build_review_schedule([lesson("t/l1", [rv("rv-001", "2026-07-13", "new")])])
    assert a["generated_from_hash"] != b["generated_from_hash"]  # stale phát hiện được


def test_schedule_hash_changes_on_mastery_state():
    a = VW.build_review_schedule([lesson("t/l1", [rv("rv-001", "2026-07-12", "in_review")])])
    b = VW.build_review_schedule([lesson("t/l1", [rv("rv-001", "2026-07-12", "need_redo")])])
    assert a["generated_from_hash"] != b["generated_from_hash"]


# ---- assessment ---------------------------------------------------------
def test_assessment_only_counts_learned_and_needs_review():
    lessons = [
        lesson("t/l1", status="learned",
               scores={"concept": 2, "explain": 2, "apply": 1, "critique": 0, "teachback": 0}),
        lesson("t/l2", status="needs_review",
               scores={"concept": 3, "explain": 2, "apply": 3, "critique": 2, "teachback": 2}),
        lesson("t/l3", status="in_progress",
               scores={"concept": 3, "explain": 3, "apply": 3, "critique": 3, "teachback": 3}),
    ]
    out = VW.build_assessment(lessons)
    assert out["concept_avg"] == 2.5     # (2+3)/2, l3 bị loại
    assert out["apply_avg"] == 2.0       # (1+3)/2
    assert out["teachback_avg"] == 1.0   # (0+2)/2


def test_assessment_empty_when_no_eligible_lesson():
    out = VW.build_assessment([lesson("t/l1", status="in_progress",
                                       scores={ax: 3 for ax in AXES})])
    assert all(out[f"{ax}_avg"] == 0.0 for ax in AXES)
    assert out["generated_from_hash"].startswith("sha256:")


def test_assessment_rounds_one_decimal():
    lessons = [
        lesson("t/l1", status="learned", scores={ax: 1 for ax in AXES}),
        lesson("t/l2", status="learned", scores={ax: 2 for ax in AXES}),
        lesson("t/l3", status="learned", scores={ax: 2 for ax in AXES}),
    ]
    out = VW.build_assessment(lessons)
    assert out["concept_avg"] == 1.7  # 5/3 = 1.666..→1.7


def test_assessment_deterministic():
    lessons = [lesson("t/l1", status="learned", scores={ax: 2 for ax in AXES})]
    assert VW.build_assessment(lessons) == VW.build_assessment(lessons)
