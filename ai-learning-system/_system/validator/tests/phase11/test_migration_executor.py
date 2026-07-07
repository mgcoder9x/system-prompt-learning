"""P11 — Migration EXECUTOR (spec 10.7/10.3b, Q2): chạy plan trong transaction-FULL, validate-at-target,
rollback nguyên vẹn nếu FAIL. RED-first.

Chứng minh CƠ CHẾ bằng schema-v2-GIẢ-LẬP (mock step trong tmp, KHÔNG để lại trong _system thật):
- validate-at-target được INJECT (validate_staged_fn) vì validator v2 thật CHƯA có (DEC-011 vẫn đúng cho
  transform/schema v2 THẬT). Phần được kiểm ở đây là ORCHESTRATION: begin→stage→validate→commit/abort.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "migrations"))
sys.path.insert(0, str(ROOT / "validator"))

import executor as E   # noqa: E402  (RED: chưa tồn tại)
import transaction as TX  # noqa: E402
import validate as V   # noqa: E402
import vault_io as VIO  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
NOW = datetime(2026, 7, 4, 9, 0, tzinfo=timezone.utc)
VS = "vault_state.md"

# mock step v1→v2: bump schema_version 1→2 (transform giả lập, đủ để test orchestration)
MOCK_STEP = (
    "import transaction as TX\n"
    "import vault_io as VIO\n"
    "from pathlib import Path\n"
    "def migrate(vault):\n"
    "    p = Path(vault) / 'vault_state.md'\n"
    "    text = p.read_text(encoding='utf-8')\n"
    "    new = text.replace('schema_version: 1', 'schema_version: 2')\n"
    "    return [TX.Write('vault_state.md', new.encode('utf-8'), expected_read_hash=VIO.content_hash(p))]\n"
)


def _vault(tmp):
    dst = tmp / "lv"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _migdir(tmp):
    d = tmp / "mig"
    d.mkdir()
    (d / "v1_to_v2.py").write_text(MOCK_STEP, encoding="utf-8")
    return d


def _ok(_tx):
    return V.Report()  # rỗng → ok()


def _fail(_tx):
    r = V.Report()
    r.err("E-SCHEMA", "vault_state.md", "giả lập validate-at-target FAIL")
    return r


def test_execute_step_commits_on_validate_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _vault(tmp_path)
    step = E._load_step(_migdir(tmp_path), 1, 2)
    committed, rep = E.execute_step(v, SYSTEM, 1, 2, step, now=NOW, validate_staged_fn=_ok)
    assert committed is True, rep.errors
    assert "schema_version: 2" in (v / VS).read_text(encoding="utf-8")  # đã bump
    assert not (v / ".tx").exists() or not list((v / ".tx").iterdir())  # không còn tx subdir (dọn xong)


def test_execute_step_rollback_on_validate_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _vault(tmp_path)
    before = (v / VS).read_bytes()
    step = E._load_step(_migdir(tmp_path), 1, 2)
    committed, rep = E.execute_step(v, SYSTEM, 1, 2, step, now=NOW, validate_staged_fn=_fail)
    assert committed is False
    assert any(e["error_code"] == "E-SCHEMA" for e in rep.errors)
    assert (v / VS).read_bytes() == before   # vault GIỮ NGUYÊN version cũ (rollback nguyên vẹn)


def test_run_plan_stops_on_first_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _vault(tmp_path)
    before = (v / VS).read_bytes()
    res = E.run_plan(v, SYSTEM, [(1, 2)], _migdir(tmp_path), now=NOW, validate_staged_fn=_fail)
    assert res[0]["committed"] is False
    assert (v / VS).read_bytes() == before


def test_run_plan_happy_single_step(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _vault(tmp_path)
    res = E.run_plan(v, SYSTEM, [(1, 2)], _migdir(tmp_path), now=NOW, validate_staged_fn=_ok)
    assert res[0]["committed"] is True
    assert "schema_version: 2" in (v / VS).read_text(encoding="utf-8")
