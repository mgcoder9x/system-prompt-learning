"""P10 driver — CR-0015: /curriculum --set-area-refs (retrofit area_refs cho Curriculum_Point ĐÃ CÓ).

Backend cmd_curriculum_set_area_refs: tìm point theo id → REPLACE area_refs → transaction-FULL
(validator gate E-CURR-* + E-BP-* trước commit). Mở luồng curriculum-first → áp-khung-về-sau (NOTE-039).
RED-first: backend chưa tồn tại → AttributeError trước khi hiện thực.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _base_curriculum(v: Path):
    """Dựng curriculum 2 điểm cp-001/cp-002 KHÔNG area_refs, KHÔNG blueprint (isolate set-area-refs)."""
    pts = json.dumps([{"objective": "Điểm A"}, {"objective": "Điểm B"}])
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert committed, rep.errors


def _points(v: Path):
    return S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]["points"]


def test_set_area_refs_updates_point(tmp_path):
    v = _fresh(tmp_path)
    _base_curriculum(v)
    committed, rep = S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-001"]), AT)
    assert committed, rep.errors
    pts = _points(v)
    cp1 = next(p for p in pts if p["id"] == "cp-001")
    cp2 = next(p for p in pts if p["id"] == "cp-002")
    assert cp1["area_refs"] == ["ma-001"]
    assert cp2["area_refs"] == []            # điểm khác KHÔNG đổi


def test_set_area_refs_replace_not_append(tmp_path):
    v = _fresh(tmp_path)
    _base_curriculum(v)
    S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-001"]), AT)
    committed, rep = S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-002"]), AT)
    assert committed, rep.errors
    cp1 = next(p for p in _points(v) if p["id"] == "cp-001")
    assert cp1["area_refs"] == ["ma-002"]    # THAY, không nối ["ma-001","ma-002"]


def test_set_area_refs_empty_clears(tmp_path):
    v = _fresh(tmp_path)
    _base_curriculum(v)
    S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-001"]), AT)
    committed, rep = S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps([]), AT)
    assert committed, rep.errors
    cp1 = next(p for p in _points(v) if p["id"] == "cp-001")
    assert cp1["area_refs"] == []            # list rỗng = xoá ánh xạ (hợp lệ)


def test_set_area_refs_unknown_point(tmp_path):
    v = _fresh(tmp_path)
    _base_curriculum(v)
    before = _points(v)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-999", json.dumps(["ma-001"]), AT)
    assert _points(v) == before              # KHÔNG ghi bộ phận


def test_set_area_refs_bad_json(tmp_path):
    v = _fresh(tmp_path)
    _base_curriculum(v)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps("notalist"), AT)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps([1, 2]), AT)  # phần tử non-str


def test_set_area_refs_no_curriculum(tmp_path):
    v = _fresh(tmp_path)   # demo docker KHÔNG có curriculum.md
    with pytest.raises(S.SessionError):
        S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-001"]), AT)


def test_set_area_refs_corrupt_curriculum_clean_schema_error(tmp_path):
    """curriculum.md sửa-tay-hỏng (points sai kiểu) → E-SCHEMA sạch, KHÔNG crash traceback (DEC-071 class)."""
    v = _fresh(tmp_path)
    cpath = v / "topics" / "docker" / "curriculum.md"
    cpath.write_text(
        "---\nschema: curriculum\nschema_version: 1\ntopic_id: docker\n"
        "current_point: cp-001\nteachable: true\npoints: \"not a list\"\n"
        "created: 2026-07-01\nupdated: 2026-07-01\n---\nbody\n", encoding="utf-8")
    with pytest.raises(S.SessionError) as ei:
        S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-001"]), AT)
    assert getattr(ei.value, "error_code", None) == "E-SCHEMA"
