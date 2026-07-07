"""P07a — INV-03 mở rộng: prerequisites + current_lesson trỏ lesson tồn tại (E-REF-BROKEN)."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V   # noqa: E402
import session         # noqa: E402  (dùng _load_raw/_dump_state để sửa front-matter)

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
LS = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"
NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)  # >= ngày demo (2026-06-30) → INV-05 tất định


def _copy(tmp):
    dst = tmp / "lv"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _edit(path: Path, **changes):
    raw, body = session._load_raw(path)
    raw.update(changes)
    path.write_bytes(session._dump_state(raw, body))


def _codes(vault):
    rep = V.Report()
    V.validate_full_core(SYSTEM, vault, rep, now=NOW)
    return {e["error_code"] for e in rep.errors}


# ---- demo hợp lệ → không có E-REF-BROKEN -----------------------------
def test_valid_demo_no_ref_broken(tmp_path):
    assert "E-REF-BROKEN" not in _codes(_copy(tmp_path))


# ---- prerequisite trỏ lesson không tồn tại → E-REF-BROKEN ------------
def test_bad_prerequisite(tmp_path):
    v = _copy(tmp_path)
    _edit(v / LS, prerequisites=["docker/lesson-999"])
    assert "E-REF-BROKEN" in _codes(v)


# ---- vault_state.current_lesson trỏ lesson không tồn tại → E-REF-BROKEN
def test_bad_vault_current_lesson(tmp_path):
    v = _copy(tmp_path)
    # đổi cả vault + topic để tránh chỉ dính INV-25; INV-03 phải bắt tồn tại
    _edit(v / "vault_state.md", current_lesson="docker/lesson-999")
    _edit(v / "topics" / "docker" / "topic_state.md", current_lesson="docker/lesson-999")
    assert "E-REF-BROKEN" in _codes(v)


# ---- open_session.lesson_id trỏ lesson không tồn tại → E-REF-BROKEN (INV-03 'mọi tham chiếu') ----
def test_bad_open_session_lesson(tmp_path):
    # Sửa tay open_session trỏ lesson đã xoá/không tồn tại → validator (lưới an toàn) phải bắt dangling.
    v = _copy(tmp_path)
    _edit(v / "vault_state.md",
          open_session={"lesson_id": "docker/ghost", "started_at": None, "last_full_validate": None})
    assert "E-REF-BROKEN" in _codes(v)


# ---- vault_state.current_topic trỏ topic không tồn tại → E-REF-BROKEN (INV-03, cùng diễn giải DEC-031) ----
def test_bad_vault_current_topic(tmp_path):
    # current_topic là 1 tham chiếu tới topic; trỏ topic không có dir → phải bắt dangling.
    # current_lesson=None để cô lập (chỉ dính current_topic, không dính INV-25/current_lesson).
    v = _copy(tmp_path)
    _edit(v / "vault_state.md", current_topic="ghost-topic", current_lesson=None)
    assert "E-REF-BROKEN" in _codes(v)


def test_valid_empty_topic_current_topic_ok(tmp_path):
    # Topic RỖNG (có dir, không lesson) vẫn hợp lệ cho current_topic → KHÔNG false-positive.
    v = _copy(tmp_path)
    (v / "topics" / "empty-topic").mkdir()
    _edit(v / "vault_state.md", current_topic="empty-topic", current_lesson=None)
    assert "E-REF-BROKEN" not in _codes(v)


# ---- prerequisite hợp lệ (tự trỏ lesson tồn tại) → không lỗi ---------
def test_valid_prerequisite(tmp_path):
    v = _copy(tmp_path)
    _edit(v / LS, prerequisites=["docker/lesson-001"])  # tồn tại
    assert "E-REF-BROKEN" not in _codes(v)
