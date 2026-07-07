"""P03 tests — pydantic strict models (spec 5.x, INV-01/05, v2.6/F-A).

Lưu ý kiến trúc: INV-04 (id trùng) và INV-10 (prompt_ref trùng) là bất biến CẤP-TẬP-HỢP,
KHÔNG kiểm trong model (nếu kiểm ở đây mọi lỗi biến thành E-SCHEMA, sai taxonomy 10.6).
Chúng được validator kiểm với mã riêng E-ID-DUP / E-REVIEW-DUP (test ở phase06/phase07a).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import models as M  # noqa: E402


def reviewed_card():
    return {
        "state": "Review", "step": 0, "stability": 12.34, "difficulty": 5.41,
        "due_at_utc": "2026-07-12T13:00:00Z", "due_date": date(2026, 7, 12),
        "last_reviewed_at_utc": "2026-06-30T13:00:00Z",
    }


def new_card():
    return {
        "state": "Learning", "step": 0, "stability": None, "difficulty": None,
        "due_at_utc": "2026-06-30T03:00:00Z", "due_date": date(2026, 6, 30),
        "last_reviewed_at_utc": None,
    }


def mastery(score=0):
    ax = {"score": score, "evidence": []}
    return {k: dict(ax) for k in ("concept", "explain", "apply", "critique", "teachback")}


def lesson(**over):
    base = {
        "schema": "lesson_state", "schema_version": 1,
        "lesson_id": "docker/lesson-001", "title": "Container", "status": "in_progress",
        "created": date(2026, 6, 30), "updated": date(2026, 6, 30),
        "objective": "Hiểu container", "prerequisites": [],
        "sections_done": [], "sections_pending": [], "mastery": mastery(),
        "open_gaps": [], "review_items": [], "next_action": "", "last_session": None,
    }
    base.update(over)
    return base


# ---- valid --------------------------------------------------------------
def test_valid_new_item():
    it = {"id": "rv-001", "prompt_ref": "lesson.md#q1", "fsrs_config_version": 1,
          "created": date(2026, 6, 30), "card": new_card(), "log": [], "mastery_state": "new"}
    m = M.LessonState(**lesson(review_items=[it]))
    assert m.review_items[0].mastery_state == "new"


def test_valid_reviewed_item():
    it = {"id": "rv-002", "prompt_ref": "lesson.md#q2", "fsrs_config_version": 1,
          "created": date(2026, 6, 30), "card": reviewed_card(),
          "log": [{"reviewed_at": "2026-06-30T20:00:00+07:00", "rating": 3}],
          "mastery_state": "in_review"}
    M.LessonState(**lesson(review_items=[it]))


def test_valid_vault_state():
    M.VaultState(**{"schema": "vault_state", "schema_version": 1, "utc_offset": "+07:00",
                    "current_topic": "docker", "current_lesson": "docker/lesson-001"})


# ---- invalid (strict + INV) --------------------------------------------
def test_strict_rejects_string_score():
    with pytest.raises(ValidationError):
        M.LessonState(**lesson(mastery={**mastery(), "concept": {"score": "2", "evidence": []}}))


def test_newitem_with_stability_rejected():
    c = new_card(); c["stability"] = 1.2
    it = {"id": "rv-1", "prompt_ref": "lesson.md#q1", "fsrs_config_version": 1,
          "created": date(2026, 6, 30), "card": c, "log": [], "mastery_state": "new"}
    with pytest.raises(ValidationError):
        M.LessonState(**lesson(review_items=[it]))


def test_revieweditem_without_stability_rejected():
    c = reviewed_card(); c["stability"] = None
    it = {"id": "rv-1", "prompt_ref": "lesson.md#q1", "fsrs_config_version": 1,
          "created": date(2026, 6, 30), "card": c,
          "log": [{"reviewed_at": "2026-06-30T20:00:00+07:00", "rating": 3}],
          "mastery_state": "in_review"}
    with pytest.raises(ValidationError):
        M.LessonState(**lesson(review_items=[it]))


def test_updated_before_created_rejected():
    with pytest.raises(ValidationError):
        M.LessonState(**lesson(created=date(2026, 6, 30), updated=date(2026, 6, 29)))


def test_bad_status_enum_rejected():
    with pytest.raises(ValidationError):
        M.LessonState(**lesson(status="done"))


def test_dup_prompt_ref_not_model_concern():
    """INV-10 là bất biến cấp-tập-hợp → model KHÔNG raise (validator phát E-REVIEW-DUP).
    Đây là ranh giới tầng cố ý: model chỉ kiểm cấu trúc từng item."""
    mk = lambda i: {"id": f"rv-{i}", "prompt_ref": "lesson.md#q1", "fsrs_config_version": 1,
                    "created": date(2026, 6, 30), "card": new_card(), "log": [], "mastery_state": "new"}
    m = M.LessonState(**lesson(review_items=[mk(1), mk(2)]))  # không raise
    assert len(m.review_items) == 2


def test_bad_utc_offset_rejected():
    with pytest.raises(ValidationError):
        M.VaultState(**{"schema": "vault_state", "schema_version": 1, "utc_offset": "+7h"})


def test_bad_date_policy_rejected():
    # date_policy chỉ có 1 giá trị spec định nghĩa (§5.4: local_date). Giá trị khác = cấu hình
    # 'nói dối hành vi' (code luôn dùng local_date theo utc_offset) → strict phải TỪ CHỐI, không âm thầm bỏ qua.
    with pytest.raises(ValidationError):
        M.VaultState(**{"schema": "vault_state", "schema_version": 1, "utc_offset": "+07:00",
                        "date_policy": "utc"})


def test_default_and_explicit_local_date_ok():
    # default (thiếu field) và giá trị hợp lệ 'local_date' đều PASS.
    assert M.VaultState(**{"schema": "vault_state", "schema_version": 1,
                           "utc_offset": "+07:00"}).date_policy == "local_date"
    M.VaultState(**{"schema": "vault_state", "schema_version": 1, "utc_offset": "+07:00",
                    "date_policy": "local_date"})


def test_bad_due_at_utc_format_rejected():
    c = reviewed_card(); c["due_at_utc"] = "2026-07-12 13:00"
    it = {"id": "rv-1", "prompt_ref": "lesson.md#q1", "fsrs_config_version": 1,
          "created": date(2026, 6, 30), "card": c,
          "log": [{"reviewed_at": "2026-06-30T20:00:00+07:00", "rating": 3}],
          "mastery_state": "in_review"}
    with pytest.raises(ValidationError):
        M.LessonState(**lesson(review_items=[it]))
