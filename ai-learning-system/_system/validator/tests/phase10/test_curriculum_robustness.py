"""P10 robustness — lệnh curriculum KHÔNG được crash traceback trên curriculum.md sửa-tay-hỏng.

Nguyên tắc thương mại (NOTE-018): driver LUÔN suy biến về mã E-* sạch, KHÔNG crash traceback thô.
Bug phát hiện qua adversarial probe: cmd_curriculum_insert / cmd_next_lesson / cmd_grade đọc RAW points
rồi gọi p.get('id') — nếu points sai kiểu (list non-dict / không phải list, YAML HỢP LỆ) → AttributeError
thô. Fix: validate qua M.Curriculum (insert/next_lesson) + guard isinstance (grade). RED-first.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import session as S      # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc)
CUR_REL = Path("topics") / "docker" / "curriculum.md"


def _vault_with_curriculum(tmp_path):
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    c, rep = S.cmd_curriculum(v, SYSTEM, "docker", json.dumps([{"objective": "A"}, {"objective": "B"}]), AT)
    assert c, rep.errors
    return v


def _write_malformed_points(v, points):
    """Ghi curriculum.md YAML HỢP LỆ nhưng points sai kiểu (mô phỏng sửa tay)."""
    raw = {"schema": "curriculum", "schema_version": 1, "topic_id": "docker",
           "current_point": "cp-001", "teachable": True,
           "created": date(2026, 7, 6), "updated": date(2026, 7, 6), "points": points}
    (v / CUR_REL).write_bytes(S._dump_state(raw, "\nbody\n"))


def test_insert_on_malformed_points_no_crash(tmp_path):
    v = _vault_with_curriculum(tmp_path)
    _write_malformed_points(v, ["just_a_string", "another"])   # list of non-dict
    with pytest.raises(S.SessionError) as ei:   # SchemaError ⊂ SessionError — KHÔNG được AttributeError
        S.cmd_curriculum_insert(v, SYSTEM, "docker", 1, json.dumps({"objective": "X"}), AT)
    assert getattr(ei.value, "error_code", "") == "E-SCHEMA"


def test_next_lesson_on_malformed_points_no_crash(tmp_path):
    v = _vault_with_curriculum(tmp_path)
    _write_malformed_points(v, ["x", "y"])
    with pytest.raises(S.SessionError) as ei:
        S.cmd_next_lesson(v, SYSTEM, "docker", AT)
    assert getattr(ei.value, "error_code", "") == "E-SCHEMA"


def test_insert_on_points_not_a_list_no_crash(tmp_path):
    v = _vault_with_curriculum(tmp_path)
    _write_malformed_points(v, "not-a-list")   # points là chuỗi
    with pytest.raises(S.SessionError) as ei:
        S.cmd_curriculum_insert(v, SYSTEM, "docker", 1, json.dumps({"objective": "X"}), AT)
    assert getattr(ei.value, "error_code", "") == "E-SCHEMA"


def test_grade_append_on_malformed_exam_results_no_crash(tmp_path, monkeypatch):
    """cmd_grade append đọc results cũ + r.get('submission_id') — exam_results.md sửa-tay-hỏng
    (results=list non-dict) KHÔNG được crash AttributeError → phải E-SCHEMA sạch."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _vault_with_curriculum(tmp_path)
    ep = v / "topics" / "docker" / "exam_results.md"
    raw = {"schema": "exam_results", "schema_version": 1, "topic_id": "docker",
           "results": ["just_a_string"]}
    ep.write_bytes(S._dump_state(raw, "\nbody\n"))
    sub = tmp_path / "exam" / "docker" / "s.py"
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.write_text("x\n", encoding="utf-8")
    with pytest.raises(S.SessionError) as ei:
        S.cmd_grade(v, SYSTEM, "docker", "ex-002", str(sub), target="docker", verdict="pass", at=AT)
    assert getattr(ei.value, "error_code", "") == "E-SCHEMA"


def test_grade_with_malformed_curriculum_target_topic_no_crash(tmp_path, monkeypatch):
    """grade target=topic KHÔNG cần curriculum → curriculum points hỏng không được làm crash;
    grade vẫn chạy (target topic hợp lệ)."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _vault_with_curriculum(tmp_path)
    _write_malformed_points(v, ["broken"])
    sub = tmp_path / "exam" / "docker" / "s.py"
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.write_text("x\n", encoding="utf-8")
    # KHÔNG được raise AttributeError; target=topic → commit được (curriculum points bị bỏ qua an toàn)
    committed, rep = S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub),
                                 target="docker", verdict="pass", at=AT)
    assert committed, rep.errors
