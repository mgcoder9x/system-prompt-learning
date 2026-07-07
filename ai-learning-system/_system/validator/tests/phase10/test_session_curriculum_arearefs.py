"""P10 driver — curriculum mang area_refs (CR-0012/0013) + wiring PHỦ với blueprint approved.

- cmd_curriculum/insert nhận area_refs cho từng point (JSON), default [].
- Curriculum teachable phủ ĐỦ blueprint approved → commit + teachable + validate PASS.
- Thiếu phủ (teachable) dưới blueprint approved → E-BP-AREA-UNCOVERED → transaction ABORT (không teachable).
RED-first: cmd_curriculum chưa đọc area_refs → coverage fail.
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
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
AREAS = json.dumps([{"title": "Linux nền tảng"}, {"title": "Container & Image"}])


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _approved_blueprint(v: Path):
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)       # ma-001, ma-002
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)


def _full_errors(v: Path):
    rep = V.Report()
    V.validate_full_semantic(ROOT, v, rep, now=AT)
    return rep.errors


def test_curriculum_stores_area_refs(tmp_path):
    v = _fresh(tmp_path)
    pts = json.dumps([{"objective": "Học Linux", "area_refs": ["ma-001"]},
                      {"objective": "Học Container", "area_refs": ["ma-002"]}])
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert committed, rep.errors
    raw = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    assert [p["area_refs"] for p in raw["points"]] == [["ma-001"], ["ma-002"]]


def test_curriculum_covers_approved_blueprint(tmp_path):
    v = _fresh(tmp_path)
    _approved_blueprint(v)
    pts = json.dumps([{"objective": "Linux", "area_refs": ["ma-001"]},
                      {"objective": "Container", "area_refs": ["ma-002"]}])
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert committed, rep.errors
    raw = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    assert raw["teachable"] is True
    assert _full_errors(v) == []


def test_curriculum_incomplete_coverage_aborts(tmp_path):
    v = _fresh(tmp_path)
    _approved_blueprint(v)
    # chỉ phủ ma-001, thiếu ma-002 (mandatory) → coverage fail (teachable) → ABORT
    pts = json.dumps([{"objective": "Linux", "area_refs": ["ma-001"]}])
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert not committed
    assert any(e["error_code"] == "E-BP-AREA-UNCOVERED" for e in rep.errors), rep.errors
    assert not (v / "topics" / "docker" / "curriculum.md").is_file()  # rollback, không để lại file


def test_curriculum_no_blueprint_backward_compat(tmp_path):
    """Không blueprint → area_refs mặc định [] vẫn hợp lệ (P9 backward-compat)."""
    v = _fresh(tmp_path)
    pts = json.dumps([{"objective": "Linux"}, {"objective": "Container"}])
    committed, rep = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert committed, rep.errors
    raw = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    assert all(p["area_refs"] == [] for p in raw["points"])
    assert _full_errors(v) == []


def test_curriculum_insert_carries_area_refs(tmp_path):
    v = _fresh(tmp_path)
    pts = json.dumps([{"objective": "A", "area_refs": []}, {"objective": "B", "area_refs": []}])
    S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    new = json.dumps({"objective": "Chèn", "area_refs": ["ma-001"]})
    committed, rep = S.cmd_curriculum_insert(v, ROOT, "docker", 2, new, AT)
    assert committed, rep.errors
    raw = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    inserted = next(p for p in raw["points"] if p["order"] == 2)
    assert inserted["area_refs"] == ["ma-001"]
