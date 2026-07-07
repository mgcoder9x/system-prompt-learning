"""P10 driver — cmd_curriculum (CR-0008): dựng topics/<topic>/curriculum.md từ danh sách điểm học.

Transaction-FULL: validator kiểm E-CURR-* (cấu trúc sai → ABORT). Backend gán cp-NNN + order 1..N tất
định + current_point=cp-001 + teachable=true; AI (chat) soạn NỘI DUNG điểm (Class D). points truyền qua
JSON (an toàn free-text như DEC-046 nhưng dùng safe_dump). RED-first: cmd_curriculum chưa có.
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


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _full_errors(vault: Path):
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return rep.errors


def test_curriculum_creates_valid(tmp_path):
    v = _fresh(tmp_path)
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", POINTS, AT)
    assert committed, rep.errors
    raw = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    assert raw["schema"] == "curriculum" and raw["teachable"] is True
    assert raw["current_point"] == "cp-001"
    ids = [p["id"] for p in raw["points"]]
    orders = [p["order"] for p in raw["points"]]
    assert ids == ["cp-001", "cp-002"] and orders == [1, 2]
    assert all(p["status"] == "not_started" and p["lesson_id"] is None for p in raw["points"])
    assert _full_errors(v) == [], "vault phải PASS full sau khi dựng curriculum"


def test_curriculum_topic_not_exist(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum(v, ROOT, "khong-co", POINTS, AT)


def test_curriculum_already_exists(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_curriculum(v, ROOT, "docker", POINTS, AT)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum(v, ROOT, "docker", POINTS, AT)


def test_curriculum_empty_points(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum(v, ROOT, "docker", "[]", AT)


def test_curriculum_bad_json(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum(v, ROOT, "docker", "{khong phai json", AT)


def test_curriculum_point_missing_objective(tmp_path):
    v = _fresh(tmp_path)
    bad = json.dumps([{"objective": "ok"}, {"source_refs": []}])
    with pytest.raises(S.SessionError):
        S.cmd_curriculum(v, ROOT, "docker", bad, AT)


def test_curriculum_in_cli_commands():
    assert "curriculum" in S.CLI_COMMANDS and hasattr(S, "cmd_curriculum")
