"""P10 driver — Task 7 (R7): auto-advance giáo trình móc vào /done.

Khi lesson đạt learned_gate (lesson_state.status == 'learned') VÀ lesson đó map một
curriculum_point CHƯA done → set point.status='done', dời current_point sang point chưa-done
đầu tiên theo order; hết point → current_point giữ nguyên (hoàn tất ngầm, KHÔNG field mới).
Chưa qua gate / không map / point đã done → KHÔNG đụng con trỏ (idempotent, backward-compat).

Tách rõ:
- UNIT (thuần) cho helper `_advance_curriculum` — phủ trọn logic advance (kể cả learned=True).
- INTEGRATION cho `cmd_done` — nhánh KHÔNG-advance (chưa gate) vẫn commit (regression + wiring False).
  Đường learned→advance end-to-end (cần lesson qua-gate thật) để E2E Task 10.

RED-first: chạy trước khi hiện thực helper/wiring → phải ĐỎ.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S      # noqa: E402
import validate as V     # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
TODAY = date(2026, 7, 2)
DONE_AT = datetime(2026, 7, 2, 12, 30, 0, tzinfo=timezone.utc)  # 19:30 +07
POINTS = json.dumps([{"objective": "Container là gì"}, {"objective": "Image & Dockerfile"}])

VS_REL = Path("vault_state.md")
CUR_REL = Path("topics") / "docker" / "curriculum.md"


def _cur(cp1_status="in_progress", cp1_lesson="docker/lesson-001",
         cp2_status="not_started", cp2_lesson=None, current="cp-001") -> dict:
    """Dựng curriculum raw tối thiểu (thuần) cho unit test."""
    return {
        "schema": "curriculum", "schema_version": 1, "topic_id": "docker",
        "current_point": current, "teachable": True,
        "created": date(2026, 6, 30), "updated": date(2026, 6, 30),
        "points": [
            {"id": "cp-001", "order": 1, "objective": "A", "status": cp1_status,
             "lesson_id": cp1_lesson, "source_refs": []},
            {"id": "cp-002", "order": 2, "objective": "B", "status": cp2_status,
             "lesson_id": cp2_lesson, "source_refs": []},
        ],
    }


# ================= UNIT: _advance_curriculum (thuần) =====================

def test_advance_learned_mapped_marks_done_and_advances():
    cur = _cur()
    changed = S._advance_curriculum(cur, "docker/lesson-001", learned=True, today=TODAY)
    assert changed is True
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["status"] == "done"
    assert cur["current_point"] == "cp-002"      # dời sang point chưa-done kế theo order
    assert cur["updated"] == TODAY


def test_advance_not_learned_is_noop():
    cur = _cur()
    changed = S._advance_curriculum(cur, "docker/lesson-001", learned=False, today=TODAY)
    assert changed is False
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["status"] == "in_progress"        # không đụng
    assert cur["current_point"] == "cp-001"
    assert cur["updated"] == date(2026, 6, 30)


def test_advance_unmapped_lesson_is_noop():
    cur = _cur()
    changed = S._advance_curriculum(cur, "docker/lesson-999", learned=True, today=TODAY)
    assert changed is False
    assert cur["current_point"] == "cp-001"
    assert all(p["status"] != "done" for p in cur["points"])


def test_advance_already_done_point_is_noop():
    # cp-001 đã done trước đó → learned lại KHÔNG re-advance (idempotent, chống nhảy 2 lần)
    cur = _cur(cp1_status="done", current="cp-002")
    changed = S._advance_curriculum(cur, "docker/lesson-001", learned=True, today=TODAY)
    assert changed is False
    assert cur["current_point"] == "cp-002"


def test_advance_last_point_completes_stays_on_existing():
    # cp-001 đã done, cp-002 là point cuối đang học → learned cp-002: done hết,
    # current_point giữ ở point tồn tại (KHÔNG dangling, không field 'completed' mới)
    cur = _cur(cp1_status="done", cp1_lesson="docker/lesson-001",
               cp2_status="in_progress", cp2_lesson="docker/lesson-002", current="cp-002")
    changed = S._advance_curriculum(cur, "docker/lesson-002", learned=True, today=TODAY)
    assert changed is True
    assert all(p["status"] == "done" for p in cur["points"])
    assert cur["current_point"] in {"cp-001", "cp-002"}   # trỏ point tồn tại (E-CURR-POINTER an toàn)
    ids = {p["id"] for p in cur["points"]}
    assert cur["current_point"] in ids


# ============ INTEGRATION: cmd_done nhánh KHÔNG-advance ==================

def _fresh_with_curriculum_mapped(tmp_path) -> Path:
    """Copy demo vault + dựng curriculum + map cp-001→lesson-001 (in_progress) + mở phiên."""
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    committed, rep = S.cmd_curriculum(v, SYSTEM, "docker", POINTS,
                                      datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc))
    assert committed, rep.errors
    # map cp-001 → lesson-001 (giả lập đã /next-lesson cho point đầu)
    cpath = v / CUR_REL
    raw, body = S._load_raw(cpath)
    raw["points"][0]["lesson_id"] = "docker/lesson-001"
    cpath.write_bytes(S._dump_state(raw, body))
    # mở phiên trên lesson-001
    vs = v / VS_REL
    vsraw, vsbody = S._load_raw(vs)
    vsraw["open_session"] = {"lesson_id": "docker/lesson-001",
                             "started_at": "2026-07-02T09:00:00+07:00",
                             "last_full_validate": None}
    vs.write_bytes(S._dump_state(vsraw, vsbody))
    return v


def test_done_with_curriculum_not_learned_commits_no_advance(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh_with_curriculum_mapped(tmp_path)
    committed, rep = S.cmd_done(v, SYSTEM, "docker/lesson-001", done_at=DONE_AT)
    assert committed, rep.errors                 # /done vẫn đóng sổ bình thường
    cur = S._load_raw(v / CUR_REL)[0]
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["status"] == "not_started"        # lesson chưa learned → KHÔNG advance
    assert cur["current_point"] == "cp-001"
    # toàn vẹn FULL
    rep2 = V.Report()
    V.validate_full_core(SYSTEM, v, rep2, now=DONE_AT)
    assert rep2.ok(), rep2.errors
