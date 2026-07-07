"""P10 driver — lệnh blueprint (CR-0013): build(draft)/edit/approve/amend Topic_Blueprint.

Transaction-FULL: validator kiểm E-BP-* (cấu trúc sai → ABORT). Backend gán ma-NNN + order 1..N tất định
khi build; edit/amend GIỮ id ổn định (R1.2). approve: draft→approved chỉ khi Blueprint_Validator PASS
(R4.2/4.6). amend approved chỉ khi có --confirm (R4.3/4.4). RED-first: các cmd_blueprint* chưa có.
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
AREAS = json.dumps([{"title": "Linux nền tảng"}, {"title": "Container & Image"}])


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _bp_raw(v: Path):
    return S._load_raw(v / "topics" / "docker" / "blueprint.md")[0]


def _full_errors(v: Path):
    rep = V.Report()
    V.validate_full_semantic(ROOT, v, rep, now=AT)
    return rep.errors


# ---- build (draft) ------------------------------------------------------
def test_blueprint_build_creates_draft(tmp_path):
    v = _fresh(tmp_path)
    committed, rep = S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    assert committed, rep.errors
    raw = _bp_raw(v)
    assert raw["schema"] == "blueprint" and raw["status"] == "draft"
    ids = [a["id"] for a in raw["areas"]]
    orders = [a["order"] for a in raw["areas"]]
    assert ids == ["ma-001", "ma-002"] and orders == [1, 2]
    assert all(a["mandatory"] is True for a in raw["areas"])  # mặc định mandatory
    assert _full_errors(v) == []


def test_blueprint_build_topic_not_exist(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint(v, ROOT, "khong-co", AREAS, AT)


def test_blueprint_build_already_exists(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)


def test_blueprint_build_empty(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint(v, ROOT, "docker", "[]", AT)


def test_blueprint_build_bad_json(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint(v, ROOT, "docker", "{khong phai json", AT)


def test_blueprint_build_missing_title(tmp_path):
    v = _fresh(tmp_path)
    bad = json.dumps([{"title": "ok"}, {"mandatory": True}])
    with pytest.raises(S.SessionError):
        S.cmd_blueprint(v, ROOT, "docker", bad, AT)


# ---- edit (draft only), giữ id ổn định (R1.2) ---------------------------
def test_blueprint_edit_draft_preserves_ids(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    # sắp xếp lại + thêm 1 area mới: giữ id ma-001/ma-002, area mới nhận ma-003
    new = json.dumps([
        {"id": "ma-002", "title": "Container & Image"},
        {"id": "ma-001", "title": "Linux nền tảng"},
        {"title": "Compose"},
    ])
    committed, rep = S.cmd_blueprint_edit(v, ROOT, "docker", new, AT)
    assert committed, rep.errors
    raw = _bp_raw(v)
    by_id = {a["id"]: a for a in raw["areas"]}
    assert set(by_id) == {"ma-001", "ma-002", "ma-003"}       # id cũ giữ nguyên, mới = ma-003
    assert by_id["ma-002"]["order"] == 1 and by_id["ma-001"]["order"] == 2  # sắp lại theo vị trí
    assert by_id["ma-003"]["order"] == 3
    assert _full_errors(v) == []


def test_blueprint_edit_rejected_when_approved(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint_edit(v, ROOT, "docker", AREAS, AT)


# ---- approve (draft→approved) -------------------------------------------
def test_blueprint_approve_sets_approved(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    committed, rep = S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    assert committed, rep.errors
    assert _bp_raw(v)["status"] == "approved"
    assert _full_errors(v) == []


def test_blueprint_approve_missing(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint_approve(v, ROOT, "docker", AT)


def test_blueprint_approve_already_approved(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    with pytest.raises(S.SessionError):
        S.cmd_blueprint_approve(v, ROOT, "docker", AT)


# ---- amend (approved, cần --confirm) ------------------------------------
def test_blueprint_amend_requires_confirm(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    new = json.dumps([{"id": "ma-001", "title": "Linux"}, {"id": "ma-002", "title": "Container"}])
    with pytest.raises(S.SessionError):
        S.cmd_blueprint_amend(v, ROOT, "docker", new, False, AT)  # thiếu confirm → từ chối


def test_blueprint_amend_with_confirm_applies(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    new = json.dumps([{"id": "ma-001", "title": "Linux CẬP NHẬT"}, {"id": "ma-002", "title": "Container"}])
    committed, rep = S.cmd_blueprint_amend(v, ROOT, "docker", new, True, AT)
    assert committed, rep.errors
    by_id = {a["id"]: a for a in _bp_raw(v)["areas"]}
    assert by_id["ma-001"]["title"] == "Linux CẬP NHẬT"
    assert _bp_raw(v)["status"] == "approved"  # vẫn approved sau amend
    assert _full_errors(v) == []


def test_blueprint_amend_on_draft_rejected(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", AREAS, AT)  # còn draft
    with pytest.raises(S.SessionError):
        S.cmd_blueprint_amend(v, ROOT, "docker", AREAS, True, AT)


def test_blueprint_in_cli_commands():
    assert "blueprint" in S.CLI_COMMANDS and hasattr(S, "cmd_blueprint")
