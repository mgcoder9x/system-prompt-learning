"""P10 driver — cmd_next_lesson (CR-0008): 'nhảy bài' — sinh lesson kế cho current_point của giáo trình.

Transaction-FULL: tạo lessons/lesson-NNN từ template (objective = objective của current_point), set
point.lesson_id, append topic_state.lessons[] + regen view (INV-25/09 từ TẤT CẢ lesson), trỏ
vault_state.current_lesson. Chỉ khi teachable=true (R6.8) + current_point CHƯA có lesson. RED-first.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
POINTS = json.dumps([{"objective": "Container là gì"}, {"objective": "Image & Dockerfile"}])


def _fresh_with_curriculum(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", POINTS, AT)
    assert committed, rep.errors
    return v


def _full_errors(vault: Path):
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return rep.errors


def test_next_lesson_creates_and_maps(tmp_path):
    v = _fresh_with_curriculum(tmp_path)
    committed, rep = S.cmd_next_lesson(v, ROOT, "docker", AT)
    assert committed, rep.errors
    # lesson-002 (kế lesson-001 demo) được tạo đủ 3 file
    ld = v / "topics" / "docker" / "lessons" / "lesson-002"
    for f in ("lesson.md", "lesson_state.md", "lesson_notes.md"):
        assert (ld / f).is_file(), f"thiếu {f}"
    # curriculum: cp-001 (current_point) được gắn lesson_id
    cur = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["lesson_id"] == "docker/lesson-002"
    # topic_state index có cả lesson-001 + lesson-002 (INV-25)
    ts = S._load_raw(v / "topics" / "docker" / "topic_state.md")[0]
    ids = {e["id"] for e in ts["lessons"]}
    assert ids == {"docker/lesson-001", "docker/lesson-002"}
    # vault_state trỏ lesson mới
    vs = S._load_raw(v / "vault_state.md")[0]
    assert vs["current_lesson"] == "docker/lesson-002"
    # toàn vẹn FULL sau khi nhảy bài
    assert _full_errors(v) == [], "vault phải PASS full sau next-lesson"


def test_next_lesson_requires_teachable(tmp_path):
    v = _fresh_with_curriculum(tmp_path)
    # ép teachable=false
    cpath = v / "topics" / "docker" / "curriculum.md"
    raw, body = S._load_raw(cpath)
    raw["teachable"] = False
    cpath.write_bytes(S._dump_state(raw, body))
    with pytest.raises(S.SessionError):
        S.cmd_next_lesson(v, ROOT, "docker", AT)


def test_next_lesson_point_already_has_lesson(tmp_path):
    v = _fresh_with_curriculum(tmp_path)
    S.cmd_next_lesson(v, ROOT, "docker", AT)  # cp-001 → lesson-002
    # current_point vẫn cp-001 (chưa /done auto-advance) + đã có lesson → từ chối
    with pytest.raises(S.SessionError):
        S.cmd_next_lesson(v, ROOT, "docker", AT)


def test_next_lesson_no_curriculum(tmp_path):
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)  # docker CHƯA có curriculum
    with pytest.raises(S.SessionError):
        S.cmd_next_lesson(v, ROOT, "docker", AT)


def test_next_lesson_in_cli_commands():
    assert "next_lesson" in S.CLI_COMMANDS and hasattr(S, "cmd_next_lesson")
