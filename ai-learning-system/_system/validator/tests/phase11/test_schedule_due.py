"""P10 — engine due (spec 8.5): tất định, đúng luật loại 'new'/điều kiện theo state/ưu tiên/cutoff."""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import schedule as SC  # noqa: E402
import models as M     # noqa: E402

UTC = timezone.utc
OFF = "+07:00"


class _L:  # lesson tối giản: engine chỉ cần lesson_id + review_items
    def __init__(self, lid, items):
        self.lesson_id = lid
        self.review_items = items


def _reviewed(item_id, state, ms, due_date, due_at_utc):
    card = M.Card(state=state, step=1, stability=10.0, difficulty=5.0,
                  due_at_utc=due_at_utc, due_date=due_date, last_reviewed_at_utc="2026-07-01T00:00:00Z")
    log = [M.LogEvent(reviewed_at="2026-07-01T07:00:00+07:00", rating=3)]
    return M.ReviewItem(id=item_id, prompt_ref=f"lesson.md#{item_id}", fsrs_config_version=1,
                        created=date(2026, 7, 1), card=card, log=log, mastery_state=ms)


def _new(item_id):
    card = M.Card(state="Learning", step=0, stability=None, difficulty=None,
                  due_at_utc="2026-07-01T00:00:00Z", due_date=date(2026, 7, 1), last_reviewed_at_utc=None)
    return M.ReviewItem(id=item_id, prompt_ref=f"lesson.md#{item_id}", fsrs_config_version=1,
                        created=date(2026, 7, 1), card=card, log=[], mastery_state="new")


NOW = datetime(2026, 7, 10, 3, 0, tzinfo=UTC)  # 10:00 +07:00 → logical_today 2026-07-10


def test_new_item_excluded():
    lessons = [_L("t/lesson-001", [_new("rv-001")])]
    assert SC.due_today(lessons, NOW, OFF) == []


def test_review_due_by_logical_today():
    due = _reviewed("rv-1", "Review", "in_review", date(2026, 7, 10), "2026-07-10T00:00:00Z")
    notdue = _reviewed("rv-2", "Review", "in_review", date(2026, 7, 11), "2026-07-11T00:00:00Z")
    lessons = [_L("t/lesson-001", [due, notdue])]
    got = [rv.id for _, rv in SC.due_today(lessons, NOW, OFF)]
    assert got == ["rv-1"]


def test_learning_due_by_due_at_utc():
    due = _reviewed("rv-1", "Learning", "need_redo", date(2026, 7, 10), "2026-07-10T02:00:00Z")   # <= NOW
    notdue = _reviewed("rv-2", "Learning", "need_redo", date(2026, 7, 10), "2026-07-10T05:00:00Z")  # > NOW
    lessons = [_L("t/lesson-001", [due, notdue])]
    got = [rv.id for _, rv in SC.due_today(lessons, NOW, OFF)]
    assert got == ["rv-1"]


def test_priority_order():
    m = _reviewed("rv-m", "Review", "mastered", date(2026, 7, 1), "2026-07-01T00:00:00Z")
    i = _reviewed("rv-i", "Review", "in_review", date(2026, 7, 1), "2026-07-01T00:00:00Z")
    n = _reviewed("rv-n", "Review", "need_redo", date(2026, 7, 1), "2026-07-01T00:00:00Z")
    lessons = [_L("t/lesson-001", [m, i, n])]
    got = [rv.id for _, rv in SC.due_today(lessons, NOW, OFF)]
    assert got == ["rv-n", "rv-i", "rv-m"]  # need_redo < in_review < mastered


def test_days_horizon_extends():
    soon = _reviewed("rv-1", "Review", "in_review", date(2026, 7, 12), "2026-07-12T00:00:00Z")
    lessons = [_L("t/lesson-001", [soon])]
    assert SC.due_today(lessons, NOW, OFF) == []                    # ngày 12 > hôm nay 10
    got = [rv.id for _, rv in SC.due_within(lessons, NOW, OFF, days=2)]
    assert got == ["rv-1"]                                          # trong 2 ngày tới → có


def test_day_cutoff_counts_as_previous_day():
    # 02:00 local, cutoff 4 → logical_today = hôm trước (2026-07-09)
    now_early = datetime(2026, 7, 9, 19, 0, tzinfo=UTC)  # = 2026-07-10 02:00 +07:00
    assert SC.logical_today(now_early, OFF, 4) == date(2026, 7, 9)
    item = _reviewed("rv-1", "Review", "in_review", date(2026, 7, 10), "2026-07-10T00:00:00Z")
    lessons = [_L("t/lesson-001", [item])]
    assert SC.due_today(lessons, now_early, OFF, day_cutoff_hour=4) == []  # chưa tới "hôm nay logic"
