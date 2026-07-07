"""P07a — INV-19: vault_state.schema_version tương thích _system/VERSION (số nguyên).

vault < system → E-SCHEMA-OUTDATED; vault > system → E-SCHEMA-AHEAD; thiếu VERSION → E-SCHEMA-CONFIG.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402
import models as M    # noqa: E402


def _vs(n):
    return M.VaultState(**{"schema": "vault_state", "schema_version": n, "utc_offset": "+07:00"})


def _sysdir(tmp, ver):
    (tmp / "VERSION").write_text(str(ver), encoding="utf-8")
    return tmp


def _codes(vault_state, system_root):
    rep = V.Report()
    V._check_schema_version(vault_state, system_root, rep)
    return [e["error_code"] for e in rep.errors]


def test_equal_ok(tmp_path):
    assert _codes(_vs(1), _sysdir(tmp_path, 1)) == []


def test_vault_outdated(tmp_path):
    assert "E-SCHEMA-OUTDATED" in _codes(_vs(1), _sysdir(tmp_path, 2))


def test_vault_ahead(tmp_path):
    assert "E-SCHEMA-AHEAD" in _codes(_vs(2), _sysdir(tmp_path, 1))


def test_missing_version(tmp_path):
    assert "E-SCHEMA-CONFIG" in _codes(_vs(1), tmp_path)  # không có file VERSION


def test_real_system_version_is_int():
    # _system/VERSION thật phải đọc được thành int (nền INV-19)
    assert V._read_system_version(ROOT) == 1


def test_demo_vault_no_inv19_error():
    rep = V.Report()
    V.validate_full_core(ROOT, ROOT / "validator" / "tests" / "fixtures" / "demo_vault", rep,
                         now=datetime(2026, 7, 1, tzinfo=timezone.utc))
    codes = {e["error_code"] for e in rep.errors}
    assert "E-SCHEMA-OUTDATED" not in codes and "E-SCHEMA-AHEAD" not in codes
    assert rep.ok(), rep.errors
