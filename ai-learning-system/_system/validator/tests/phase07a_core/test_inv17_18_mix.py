"""P07a — INV-17/18: tách bạch hai gốc (E-MIX-*).

INV-17: không code/dependency/repo trong learning_vault/. INV-18: không dữ liệu học trong _system/.
QUAN TRỌNG: vault + _system THẬT không được dính (chống bắt oan).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402

VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"


def _codes_vault(v):
    rep = V.Report(); V._check_no_code_in_vault(v, rep)
    return {e["error_code"] for e in rep.errors}


def _codes_sys(s):
    rep = V.Report(); V._check_no_data_in_system(s, rep)
    return {e["error_code"] for e in rep.errors}


# ---- INV-17 ----------------------------------------------------------
def test_vault_clean_ok(tmp_path):
    (tmp_path / "topics").mkdir()
    (tmp_path / "vault_state.md").write_text("x", encoding="utf-8")
    assert _codes_vault(tmp_path) == set()


def test_vault_py_file(tmp_path):
    (tmp_path / "script.py").write_text("print(1)", encoding="utf-8")
    assert "E-MIX-CODE" in _codes_vault(tmp_path)


def test_vault_node_modules(tmp_path):
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("1", encoding="utf-8")
    assert "E-MIX-CODE" in _codes_vault(tmp_path)


def test_vault_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text("fsrs==6.3.1", encoding="utf-8")
    assert "E-MIX-CODE" in _codes_vault(tmp_path)


def test_vault_scratch_py_ignored(tmp_path):
    (tmp_path / "_scratch").mkdir()
    (tmp_path / "_scratch" / "tmp.py").write_text("x", encoding="utf-8")
    assert _codes_vault(tmp_path) == set()  # _scratch phi-thẩm-quyền


# ---- INV-18 ----------------------------------------------------------
def test_system_clean_ok(tmp_path):
    (tmp_path / "fsrs_config.yaml").write_text("x", encoding="utf-8")
    (tmp_path / "VERSION").write_text("1", encoding="utf-8")
    assert _codes_sys(tmp_path) == set()


def test_system_vault_state(tmp_path):
    (tmp_path / "vault_state.md").write_text("x", encoding="utf-8")
    assert "E-MIX-DATA" in _codes_sys(tmp_path)


def test_system_topics_dir(tmp_path):
    (tmp_path / "topics").mkdir()
    assert "E-MIX-DATA" in _codes_sys(tmp_path)


def test_system_data_under_validator_excluded(tmp_path):
    (tmp_path / "validator").mkdir()
    (tmp_path / "validator" / "lesson_state.md").write_text("x", encoding="utf-8")  # fixture test, hợp lệ
    assert _codes_sys(tmp_path) == set()  # validator/ được loại trừ


# ---- chống bắt oan: vault + _system THẬT sạch ------------------------
def test_real_vault_and_system_clean():
    assert _codes_vault(VAULT_SRC) == set()
    assert _codes_sys(ROOT) == set()
