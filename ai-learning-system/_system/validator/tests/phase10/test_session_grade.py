"""P10 driver — Task 8.2 (R9): cmd_grade — ghi bản ghi chấm exam vào exam_results.md.

exam_results.md nằm TRONG vault (topics/<topic>/), là METADATA chấm (không code). Bài nộp
(Exam_Submission, có thể là code) nằm NGOÀI vault ở exam/ (sibling learning_vault) — cmd_grade
verify bài nộp TỒN TẠI trong exam/ + target ∈ {topic, curriculum_point} rồi lưu ref TƯƠNG ĐỐI
portable (INV-16). verdict là Class D (nội dung không kiểm). transaction-LIGHT (in-session).

Guard NGAY TRONG lệnh (R9.6): thiếu submission / target sai / trùng submission_id → từ chối,
KHÔNG tạo bản ghi bộ phận (LIGHT không chạy _check_exam_results nên lệnh tự bảo vệ). RED-first.
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

import session as S      # noqa: E402
import validate as V     # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 6, 10, 0, tzinfo=timezone.utc)
POINTS = json.dumps([{"objective": "Container là gì"}, {"objective": "Image & Dockerfile"}])

CUR_REL = Path("topics") / "docker" / "curriculum.md"
EXAM_REL = Path("topics") / "docker" / "exam_results.md"


def _setup(tmp_path, *, make_submission=True, with_curriculum=False):
    """vault = tmp/vault (copy demo); exam/ = tmp/exam (sibling, NGOÀI vault)."""
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    exam_dir = tmp_path / "exam" / "docker"
    sub = exam_dir / "solution.py"
    if make_submission:
        exam_dir.mkdir(parents=True, exist_ok=True)
        sub.write_text("print('hello docker')\n", encoding="utf-8")
    if with_curriculum:
        committed, rep = S.cmd_curriculum(v, SYSTEM, "docker", POINTS, AT)
        assert committed, rep.errors
    return v, sub


def _full_errors(vault: Path):
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, vault, rep, now=AT)
    return [e["error_code"] for e in rep.errors]


def test_grade_creates_record_and_validates(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v, sub = _setup(tmp_path)
    committed, rep = S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub),
                                 target="docker", verdict="pass — chạy đúng, có Dockerfile", at=AT)
    assert committed, rep.errors
    raw = S._load_raw(v / EXAM_REL)[0]
    assert raw["schema"] == "exam_results" and raw["topic_id"] == "docker"
    r0 = raw["results"][0]
    assert r0["submission_id"] == "ex-001"
    assert r0["target"] == "docker"
    assert r0["verdict"].startswith("pass")
    # ref TƯƠNG ĐỐI (portable, ra khỏi vault bằng ..), KHÔNG absolute
    assert r0["ref"].startswith("..") and ":" not in r0["ref"]
    # ref resolve về đúng bài nộp
    assert (v / "topics" / "docker" / r0["ref"]).resolve() == sub.resolve()
    # toàn vẹn: không E-EXAM-REF-BROKEN
    assert "E-EXAM-REF-BROKEN" not in _full_errors(v)


def test_grade_missing_submission_rejects(tmp_path):
    v, sub = _setup(tmp_path, make_submission=False)  # file bài nộp KHÔNG tồn tại
    with pytest.raises(S.SessionError):
        S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub),
                    target="docker", verdict="pass", at=AT)
    assert not (v / EXAM_REL).exists(), "không được tạo bản ghi khi bài nộp không tồn tại (R9.6)"


def test_grade_submission_outside_exam_rejects(tmp_path):
    v, _ = _setup(tmp_path, make_submission=False)
    stray = tmp_path / "not_exam" / "x.py"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_text("x\n", encoding="utf-8")
    with pytest.raises(S.SessionError):
        S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(stray),
                    target="docker", verdict="pass", at=AT)
    assert not (v / EXAM_REL).exists()


def test_grade_bad_target_rejects(tmp_path):
    v, sub = _setup(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub),
                    target="cp-999", verdict="pass", at=AT)  # không phải topic, không cp tồn tại
    assert not (v / EXAM_REL).exists()


def test_grade_target_curriculum_point_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v, sub = _setup(tmp_path, with_curriculum=True)
    committed, rep = S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub),
                                 target="cp-001", verdict="pass", at=AT)
    assert committed, rep.errors
    assert "E-EXAM-REF-BROKEN" not in _full_errors(v)


def test_grade_duplicate_submission_rejects(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v, sub = _setup(tmp_path)
    S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub), target="docker", verdict="pass", at=AT)
    with pytest.raises(S.SessionError):
        S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub), target="docker", verdict="redo", at=AT)


def test_grade_append_second_submission(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v, sub = _setup(tmp_path)
    sub2 = sub.parent / "solution2.py"
    sub2.write_text("print('v2')\n", encoding="utf-8")
    S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub), target="docker", verdict="pass", at=AT)
    committed, rep = S.cmd_grade(v, SYSTEM, "docker", "ex-002", str(sub2),
                                 target="docker", verdict="redo", at=AT)
    assert committed, rep.errors
    raw = S._load_raw(v / EXAM_REL)[0]
    ids = {r["submission_id"] for r in raw["results"]}
    assert ids == {"ex-001", "ex-002"}
    assert "E-EXAM-REF-BROKEN" not in _full_errors(v)


def test_grade_in_cli_commands():
    assert "grade" in S.CLI_COMMANDS and hasattr(S, "cmd_grade")
