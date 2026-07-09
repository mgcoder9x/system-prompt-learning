"""Phase 2 (M2 của QĐ-3=C3) — Báo cáo retention READ-ONLY, tính từ log FSRS sẵn có.

Bản chất: M2 là PROXY độ-bền-gợi-nhớ, KHÔNG phải 'chứng minh hiểu thật' (ranh giới trung thực).
Chỉ ĐỌC (như audit.py/schedule.py) → KHÔNG đổi vault, KHÔNG đổi kernel. rating: 1=Again,2=Hard,3=Good,4=Easy.

Hai ngưỡng báo minh bạch (không ép một số):
- retention_rate  = (rating≥2, KHÔNG-Again — quy ước FSRS 'nhớ được') / tổng reviews trong cửa sổ.
- solid_recall_rate = (rating≥3, Good/Easy — 'nhớ chắc') / tổng.
- lapses = số rating==1 (Again — quên).
Cửa sổ mặc định 7/30/90 ngày, so với mốc `now` BƠM VÀO (tất định, không lệ đồng hồ).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

_KERNEL = Path(__file__).resolve().parents[2] / "ai-learning-system" / "_system" / "validator"
if str(_KERNEL) not in sys.path:
    sys.path.insert(0, str(_KERNEL))


def retention_report(events, now: datetime, windows=(7, 30, 90)) -> dict:
    """events: list[(reviewed_at: datetime tz-aware, rating: int 1..4)]. now: mốc tham chiếu tz-aware.
    Trả dict {'<w>d': {reviews, retention_rate, solid_recall_rate, lapses}}. Cửa sổ rỗng → rate = None."""
    out: dict = {}
    for w in windows:
        cutoff = now - timedelta(days=w)
        inw = [r for (t, r) in events if t >= cutoff]
        n = len(inw)
        out[f"{w}d"] = {
            "reviews": n,
            "retention_rate": (sum(1 for r in inw if r >= 2) / n) if n else None,
            "solid_recall_rate": (sum(1 for r in inw if r >= 3) / n) if n else None,
            "lapses": sum(1 for r in inw if r == 1),
        }
    return out


def _parse(ts: str) -> datetime:
    """reviewed_at là ISO offset địa phương, precision giây → datetime tz-aware."""
    return datetime.fromisoformat(ts)


def compute_from_vault(vault, system, now: datetime, windows=(7, 30, 90)) -> dict:
    """Đọc MỌI lesson_state (qua kernel _all_lesson_models — REUSE, read-only) → gộp log FSRS → báo cáo.
    Bổ sung: tổng review_items, số đã-review (có stability), số 'mastered', stability trung bình (ngày)."""
    import session as S   # kernel REUSE (in-process); chỉ đọc
    models = S._all_lesson_models(Path(vault))
    events, stabilities, mastered, total_items = [], [], 0, 0
    for m in models:
        for it in m.review_items:
            total_items += 1
            if it.mastery_state == "mastered":
                mastered += 1
            if it.card.stability is not None:
                stabilities.append(float(it.card.stability))
            for ev in it.log:
                events.append((_parse(ev.reviewed_at), ev.rating))
    return {
        "windows": retention_report(events, now, windows),
        "total_review_items": total_items,
        "reviewed_items": len(stabilities),
        "mastered_items": mastered,
        "avg_stability_days": (sum(stabilities) / len(stabilities)) if stabilities else None,
    }
