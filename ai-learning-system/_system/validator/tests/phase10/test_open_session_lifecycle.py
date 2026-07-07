"""P10 driver — vòng đời open_session (§5.4/§11B.2): /learn+/resume MỞ phiên, /done ĐÓNG, /status cảnh báo.

Gap (verified): không lệnh nào set open_session → cảnh báo unclosed của /status là code chết.
Fix: /learn set open_session (cùng write vault_state); /resume set open_session (CR-0003, bỏ read-only).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _open_lesson(vault) -> str | None:
    return (S._load_raw(vault / "vault_state.md")[0].get("open_session") or {}).get("lesson_id")


def test_learn_opens_session(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_learn(v, ROOT, "python", "Python", "Biến", "Hiểu biến", AT)
    assert _open_lesson(v) == "python/lesson-001", "/learn phải MỞ phiên (open_session.lesson_id)"
    st = S.cmd_status(v, ROOT, AT)
    assert st["unclosed_session"] is True, "/status phải cảnh báo phiên chưa /done (§11B.2)"
    assert st["open_session_started_at"], "started_at phải được ghi"


def test_learn_then_done_clears_session(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_learn(v, ROOT, "python", "Python", "Biến", "Hiểu biến", AT)
    assert _open_lesson(v) == "python/lesson-001"      # mở
    S.cmd_done(v, ROOT, "python/lesson-001", AT)
    assert _open_lesson(v) is None                     # đóng
    assert S.cmd_status(v, ROOT, AT)["unclosed_session"] is False


def test_resume_opens_session(tmp_path):
    # /resume MỞ phiên trên current_lesson (CR-0003 — đảo read-only DEC-016).
    v = _fresh(tmp_path)
    assert _open_lesson(v) is None                     # demo: chưa có phiên
    committed, rep, info = S.cmd_resume(v, ROOT, AT)
    assert committed is True
    assert _open_lesson(v) == "docker/lesson-001", "/resume phải MỞ phiên (open_session.lesson_id)"
    st = S.cmd_status(v, ROOT, AT)
    assert st["unclosed_session"] is True, "/status phải cảnh báo phiên chưa /done sau /resume (§11B.2)"


def test_resume_then_done_clears_session(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_resume(v, ROOT, AT)
    assert _open_lesson(v) == "docker/lesson-001"      # mở qua /resume
    S.cmd_done(v, ROOT, "docker/lesson-001", AT)
    assert _open_lesson(v) is None                     # /done đóng
    assert S.cmd_status(v, ROOT, AT)["unclosed_session"] is False


def test_forget_open_lesson_clears_session(tmp_path):
    # /forget lesson ĐANG là open_session → phải ĐÓNG phiên, KHÔNG để open_session dangling vào lesson đã xoá.
    # Gốc: cmd_forget trước chỉ sync current_lesson, bỏ quên open_session → con trỏ phiên treo (INV-03 spirit).
    v = _fresh(tmp_path)
    S.cmd_resume(v, ROOT, AT)                          # mở phiên trên docker/lesson-001
    assert _open_lesson(v) == "docker/lesson-001"
    committed, rep = S.cmd_forget(v, ROOT, "docker/lesson-001", "làm lại", True, AT)
    assert committed, rep.errors
    assert _open_lesson(v) is None, "/forget lesson đang mở phiên phải clear open_session (tránh dangling)"
    assert S.cmd_status(v, ROOT, AT)["unclosed_session"] is False
