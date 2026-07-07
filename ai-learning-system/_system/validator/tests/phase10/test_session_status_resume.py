"""P10 driver — cmd_status / cmd_resume (CHỈ ĐỌC, spec 11B/11B.2) trên vault thật + read-only + CLI."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_status_demo_vault():
    st = S.cmd_status(REAL_VAULT, ROOT, AT)
    assert st["current_topic"] == "docker"
    assert st["current_lesson"] == "docker/lesson-001"
    assert st["due_today"] == 0            # rv-001 mastery_state=new → không tự tới hạn (spec 8.5)
    assert st["unclosed_session"] is False  # open_session.lesson_id = null trong demo
    assert st["suggestion"] == "resume"     # không due + có current_lesson → resume


def test_resume_returns_info_and_opens_session(tmp_path):
    # /resume giờ là WRITE (CR-0003): trả (committed, rep, info) + MỞ phiên trên current_lesson.
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    committed, rep, info = S.cmd_resume(v, ROOT, AT)
    assert committed is True
    assert info["current_lesson"] == "docker/lesson-001"
    assert info["status"] == "in_progress"
    assert "Socrates" in (info["next_action"] or "")  # next_action thật của demo lesson-001
    assert info["unclosed_session"] is True
    # phiên đã được ghi vào vault_state (open_session.lesson_id)
    sess = (S._load_raw(v / "vault_state.md")[0].get("open_session") or {})
    assert sess.get("lesson_id") == "docker/lesson-001"
    assert sess.get("started_at")


def test_status_readonly(tmp_path):
    # /status vẫn CHỈ ĐỌC (không đổi mtime). /resume KHÔNG còn read-only (xem test write ở trên).
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    before = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    S.cmd_status(v, ROOT, AT)
    after = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    assert before == after, "status phải CHỈ ĐỌC"


def test_status_reports_unclosed_session(tmp_path):
    # dựng vault có open_session.lesson_id != null → phải cảnh báo (spec 11B.2)
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    vs = v / "vault_state.md"
    txt = vs.read_text(encoding="utf-8").replace(
        "open_session:\n  lesson_id: null",
        "open_session:\n  lesson_id: docker/lesson-001")
    vs.write_text(txt, encoding="utf-8")
    st = S.cmd_status(v, ROOT, AT)
    assert st["unclosed_session"] is True
    assert st["open_session_lesson"] == "docker/lesson-001"


def test_in_cli_commands():
    assert {"status", "resume"} <= set(S.CLI_COMMANDS)
    assert hasattr(S, "cmd_status") and hasattr(S, "cmd_resume")
