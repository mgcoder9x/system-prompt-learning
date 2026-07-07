"""P10 — Engine "item tới hạn" (spec 8.5). Tất định, THUẦN (không I/O).

Dùng chung cho /review (liệt kê), /status (đếm due), /schedule (n ngày). Bản chất một chỗ, không rải.

Quy tắc 8.5 (verbatim, không bịa):
- Loại item `mastery_state == "new"` (log rỗng, chưa từng review): KHÔNG tự tới hạn — chỉ vào danh sách
  khi được chọn học/ôn theo lệnh. (priority không định nghĩa cho "new" ⇒ khẳng định điều này.)
- Điều kiện tới hạn theo card.state: {Learning, Relearning} → `due_at_utc <= now_utc`;
  Review → `due_date <= logical_today`.
- Sắp: (priority(mastery_state), due_date asc, due_at_utc asc, lesson_id asc, item_id asc);
  priority: need_redo=0 < in_review=1 < mastered=2.
- logical_today = (now_local - day_cutoff_hour giờ).date(); cutoff CHỈ áp cho lọc Review theo due_date.

`days` (mở rộng n-ngày cho /schedule — spec 8.5 chỉ chốt "hôm nay"=days 0; xem decisions/DEC-015):
dịch chân trời: Review → due_date <= logical_today + days; Learning/Relearning → due_at_utc <= now_utc + days.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fsrs_adapter import _parse_offset

PRIORITY = {"need_redo": 0, "in_review": 1, "mastered": 2}


def logical_today(now_utc: datetime, utc_offset: str, day_cutoff_hour: int = 4):
    now_local = now_utc.astimezone(_parse_offset(utc_offset))
    return (now_local - timedelta(hours=day_cutoff_hour)).date()


def _parse_due_utc(s: str) -> datetime:
    """'YYYY-MM-DDTHH:MM:SSZ' → aware UTC (định dạng canonical, models._UTC_RE)."""
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _item_due(card, now_utc: datetime, lt, days: int) -> bool:
    st = card.state
    if st in ("Learning", "Relearning"):
        return _parse_due_utc(card.due_at_utc) <= now_utc + timedelta(days=days)
    if st == "Review":
        return card.due_date <= lt + timedelta(days=days)
    return False


def due_within(lessons, now_utc: datetime, utc_offset: str,
               day_cutoff_hour: int = 4, days: int = 0) -> list[tuple[str, object]]:
    """Trả list (lesson_id, review_item) tới hạn trong `days` ngày tới, sắp theo khóa 8.5.
    days=0 = ĐÚNG 'cần ôn hôm nay' của spec 8.5."""
    lt = logical_today(now_utc, utc_offset, day_cutoff_hour)
    out = []
    for lesson in lessons:
        for rv in lesson.review_items:
            if rv.mastery_state not in PRIORITY:   # "new" (chưa review) → không tự tới hạn
                continue
            if _item_due(rv.card, now_utc, lt, days):
                out.append((lesson.lesson_id, rv))
    out.sort(key=lambda t: (PRIORITY[t[1].mastery_state], t[1].card.due_date,
                            t[1].card.due_at_utc, t[0], t[1].id))
    return out


def due_today(lessons, now_utc: datetime, utc_offset: str, day_cutoff_hour: int = 4):
    """'Cần ôn hôm nay' — spec 8.5 (days=0)."""
    return due_within(lessons, now_utc, utc_offset, day_cutoff_hour, days=0)
