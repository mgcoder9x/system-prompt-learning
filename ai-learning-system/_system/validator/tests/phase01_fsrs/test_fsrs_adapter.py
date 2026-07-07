"""P01 golden/unit tests cho fsrs_adapter (spec mục 8, INV-08/21)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# cho phép import fsrs_adapter từ _system/validator/
ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import fsrs_adapter as fa  # noqa: E402

CFG = fa.load_config(ROOT / "fsrs_config.yaml")
OFF = "+07:00"
CREATED = datetime(2026, 6, 30, 3, 0, 0, tzinfo=timezone.utc)  # 10:00 +07


def ev(day, hour_local, rating):
    base = datetime(2026, 6, 30, 0, 0, 0, tzinfo=fa._parse_offset(OFF))
    dt = base + timedelta(days=day - 30, hours=hour_local)
    return {"reviewed_at": dt.isoformat(), "rating": rating}


def test_grade_mapping():
    assert [fa.MAP_GRADE_TO_RATING[g].value for g in (0, 1, 2, 3)] == [1, 2, 3, 4]
    with pytest.raises(fa.EReviewBadGrade):
        fa.review(CREATED, [], 5, CREATED, CFG, OFF)


def test_new_card_nulls():
    c = fa.new_item_card(CREATED, OFF)
    assert c["state"] == "Learning"
    assert c["stability"] is None and c["difficulty"] is None
    assert c["last_reviewed_at_utc"] is None
    assert c["due_at_utc"] == "2026-06-30T03:00:00Z"
    assert c["due_date"] == "2026-06-30"  # 10:00 +07 cùng ngày


def test_derive_mastery_new():
    c = fa.new_item_card(CREATED, OFF)
    assert fa.derive_mastery(c, [], CFG) == "new"


def test_replay_deterministic():
    log = [ev(30, 10, 3), ev(30, 10, 2), ev(31, 9, 3)]
    a = fa.replay(CREATED, log, CFG, OFF)
    b = fa.replay(CREATED, log, CFG, OFF)
    assert a == b, "replay phải tất định byte-for-byte trên cùng máy"
    assert fa.cards_equal(a, b)


def test_review_appends_and_replays():
    log = []
    new_ev, card = fa.review(CREATED, log, 3, datetime(2026, 6, 30, 10, tzinfo=fa._parse_offset(OFF)), CFG, OFF)
    assert new_ev["rating"] == 4  # grade 3 -> Easy
    # card sau 1 lần Good/Easy: đã rời trạng thái "new"
    assert card["stability"] is not None
    assert fa.derive_mastery(card, [new_ev], CFG) in ("in_review", "mastered", "need_redo")


def test_replay_matches_incremental():
    """Replay toàn log == áp từng lượt (nền tảng INV-08)."""
    events = [ev(30, 10, 3), ev(31, 9, 1), ev(31, 9, 3)]
    full = fa.replay(CREATED, events, CFG, OFF)
    # incremental
    log = []
    card = None
    for e in events:
        grade = {1: 0, 2: 1, 3: 2, 4: 3}[e["rating"]]
        reviewed = datetime.fromisoformat(e["reviewed_at"])
        new_ev, card = fa.review(CREATED, log, grade, reviewed, CFG, OFF)
        log.append(new_ev)
    assert fa.cards_equal(full, card)


def test_again_gives_need_redo():
    log = [ev(30, 10, 3), ev(31, 9, 1)]  # lượt cuối Again
    card = fa.replay(CREATED, log, CFG, OFF)
    assert fa.derive_mastery(card, log, CFG) == "need_redo"


def test_cards_equal_detects_last_reviewed_drift():
    """Regression: đổi last_reviewed_at_utc phải làm cards_equal False (INV-08 audit timeline)."""
    log = [ev(30, 10, 3), ev(31, 9, 3)]
    a = fa.replay(CREATED, log, CFG, OFF)
    b = dict(a)
    b["last_reviewed_at_utc"] = "1999-01-01T00:00:00Z"
    assert fa.cards_equal(a, a)
    assert not fa.cards_equal(a, b)


def test_review_canonicalizes_log_event():
    """Regression: caller đưa UTC + microsecond → log lưu ở offset địa phương, precision giây."""
    reviewed_utc_micro = datetime(2026, 6, 30, 3, 0, 0, 123456, tzinfo=timezone.utc)  # 10:00 +07
    new_ev, _ = fa.review(CREATED, [], 2, reviewed_utc_micro, CFG, OFF)
    assert new_ev["reviewed_at"] == "2026-06-30T10:00:00+07:00"  # +07, không microsecond
    # replay từ log đã canonicalize vẫn cho card hợp lệ
    card = fa.replay(CREATED, [new_ev], CFG, OFF)
    assert card["last_reviewed_at_utc"] == "2026-06-30T03:00:00Z"
