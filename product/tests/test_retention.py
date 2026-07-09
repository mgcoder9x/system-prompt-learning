"""Phase 2 (M2 QĐ-3=C3) — RED-first tests cho báo cáo retention (READ-ONLY, tính từ log FSRS).

M2 = proxy độ-bền-gợi-nhớ (KHÔNG phải 'chứng minh hiểu'). rating: 1=Again,2=Hard,3=Good,4=Easy.
- retention_rate = (rating≥2, không-Again — quy ước FSRS) / tổng reviews trong cửa sổ.
- solid_recall_rate = (rating≥3, Good/Easy) / tổng.
- lapses = số rating==1.
Read-only → KHÔNG đổi vault, KHÔNG đổi kernel. Tách product/ → không đụng suite 520.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
KERNEL_SYS = WS / "ai-learning-system" / "_system"
DEMO = KERNEL_SYS / "validator" / "tests" / "fixtures" / "demo_vault"
sys.path.insert(0, str(WS / "product"))

from orchestrator.retention import retention_report, compute_from_vault  # noqa: E402

TZ = timezone(timedelta(hours=7))
NOW = datetime(2026, 7, 10, 10, 0, tzinfo=TZ)


def _ev(days_ago: int, rating: int):
    return (NOW - timedelta(days=days_ago), rating)


def test_rates_basic():
    # 4 review trong cửa sổ: rating 1,2,3,4
    events = [_ev(1, 1), _ev(2, 2), _ev(3, 3), _ev(1, 4)]
    r = retention_report(events, NOW, windows=(7,))["7d"]
    assert r["reviews"] == 4
    assert r["retention_rate"] == 3 / 4       # rating 2,3,4 ≥ 2
    assert r["solid_recall_rate"] == 2 / 4    # rating 3,4 ≥ 3
    assert r["lapses"] == 1                    # rating 1


def test_window_filtering():
    events = [_ev(3, 3), _ev(40, 4)]           # 1 trong 7 ngày, 1 cách 40 ngày
    r7 = retention_report(events, NOW, windows=(7,))["7d"]
    r90 = retention_report(events, NOW, windows=(90,))["90d"]
    assert r7["reviews"] == 1
    assert r90["reviews"] == 2


def test_empty_window_returns_none_not_crash():
    r = retention_report([], NOW, windows=(30,))["30d"]
    assert r["reviews"] == 0
    assert r["retention_rate"] is None and r["solid_recall_rate"] is None


def test_hard_counts_retention_not_solid():
    # rating 2 (Hard): tính vào retention (≥2) nhưng KHÔNG vào solid (≥3)
    r = retention_report([_ev(1, 2)], NOW, windows=(7,))["7d"]
    assert r["retention_rate"] == 1.0
    assert r["solid_recall_rate"] == 0.0


def test_deterministic():
    events = [_ev(1, 3), _ev(2, 1), _ev(5, 4)]
    a = retention_report(events, NOW, windows=(7, 30))
    b = retention_report(events, NOW, windows=(7, 30))
    assert a == b


def test_compute_from_vault_readonly_no_crash():
    # đọc demo_vault THẬT (read-only) → trả cấu trúc, không crash (dù 0 review cũng OK)
    out = compute_from_vault(DEMO, KERNEL_SYS, NOW)
    assert set(out) >= {"windows", "total_review_items", "reviewed_items", "mastered_items", "avg_stability_days"}
    assert "7d" in out["windows"] and "30d" in out["windows"] and "90d" in out["windows"]
