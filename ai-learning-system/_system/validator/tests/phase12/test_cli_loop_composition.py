"""P12 (một phần) — E2E COMPOSITION test: chuỗi lệnh CLI thật NỐI nhau, tất định.

Mục đích (bản chất): mỗi lệnh đã test riêng; test này kiểm chúng GHÉP nhau không vỡ bất biến —
learn → status → review → done → forget, assert validate_full_semantic (FULL = core+semantic,
đúng mức transaction dùng) PASS SAU MỖI bước ghi. Không AI, không ngẫu nhiên.

KHÔNG phải P12 pilot đầy đủ: pilot thật cần AI dạy + cross-AI handoff (còn lại). Đây là nền tất định.

INV-05 (đã sửa DEC-029): validator NAY ép cả `updated <= today`. `_full()` truyền now=AT để 'today'
khớp mốc thao tác — tất định, không lệ thuộc đồng hồ tường (updated ghi theo AT ⇒ today cũng theo AT).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
# 2026-07-01T10:00Z = 17:00 +07:00 (local date 2026-07-01) — > created demo (2026-06-30)
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)


def _full(vault: Path) -> V.Report:
    """FULL = core + semantic (đúng mức transaction validate_staged dùng); now=AT để INV-05 tất định."""
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return rep


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def test_baseline_demo_vault_full_passes(tmp_path):
    v = _fresh(tmp_path)
    assert _full(v).ok(), _full(v).errors


def test_full_cli_loop_composition(tmp_path):
    v = _fresh(tmp_path)
    assert _full(v).ok(), f"baseline: {_full(v).errors}"

    # ---- 1) LEARN topic mới ----
    committed, rep = S.cmd_learn(v, ROOT, "python", "Python cơ bản",
                                 "Biến & kiểu", "Hiểu biến và kiểu dữ liệu", AT)
    assert committed, f"learn không commit: {rep.errors}"
    assert _full(v).ok(), f"sau learn FULL fail: {_full(v).errors}"

    # ---- 2) STATUS phản ánh topic mới ----
    st = S.cmd_status(v, ROOT, AT)
    assert st["current_topic"] == "python"
    assert st["current_lesson"] == "python/lesson-001"

    # ---- 3) REVIEW item có sẵn của docker (grade 2=Good) ----
    committed, rep = S.cmd_review(v, ROOT, "docker/lesson-001", "rv-001", 2, AT)
    assert committed, f"review không commit: {rep.errors}"
    assert _full(v).ok(), f"sau review FULL fail: {_full(v).errors}"
    ls_raw = S._load_raw(v / "topics/docker/lessons/lesson-001/lesson_state.md")[0]
    rv = next(r for r in ls_raw["review_items"] if r["id"] == "rv-001")
    assert len(rv["log"]) == 1 and rv["mastery_state"] != "new", "review phải cập nhật log + rời 'new'"

    # ---- 4) DONE đóng sổ docker ----
    committed, rep = S.cmd_done(v, ROOT, "docker/lesson-001", AT)
    assert committed, f"done không commit: {rep.errors}"
    assert _full(v).ok(), f"sau done FULL fail: {_full(v).errors}"
    vs_raw = S._load_raw(v / "vault_state.md")[0]
    assert (vs_raw.get("open_session") or {}).get("lesson_id") is None, "done phải clear open_session"

    # ---- 5) FORGET lesson python (duy nhất) → topic rỗng, con trỏ đồng bộ ----
    committed, rep = S.cmd_forget(v, ROOT, "python/lesson-001", "dọn dẹp test", True, AT)
    assert committed, f"forget không commit: {rep.errors}"
    assert _full(v).ok(), f"sau forget FULL fail: {_full(v).errors}"
    assert not (v / "topics/python/lessons/lesson-001").exists(), "lesson dir phải bị xoá"
    ts_raw = S._load_raw(v / "topics/python/topic_state.md")[0]
    assert ts_raw["lessons"] == [], "index topic python phải rỗng sau forget"
    assert ts_raw["current_lesson"] is None, "current_lesson topic phải None sau forget lesson cuối"

    # ---- 6) transaction_log.md phải ghi vết mọi thao tác ghi ----
    log = (v / "transaction_log.md").read_text(encoding="utf-8")
    assert "tombstone" in log, "forget phải ghi tombstone vào transaction_log.md (INV-11/10.3a)"


def test_forget_requires_confirmation(tmp_path):
    v = _fresh(tmp_path)
    import pytest
    with pytest.raises(S.SessionError):
        S.cmd_forget(v, ROOT, "docker/lesson-001", "no confirm", False, AT)  # confirmed_by_user=False
