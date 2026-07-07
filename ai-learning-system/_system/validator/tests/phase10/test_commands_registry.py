"""P10-agent — _system/commands.md (registry) khớp CLI thật + spec 11A.3 (chống trôi doc↔CLI)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A     # noqa: E402
import session         # noqa: E402
import validate as V   # noqa: E402


def _backends():
    text = (ROOT / "commands.md").read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "backends (máy đọc)", level=2)["backends"]


def _cli_subs():
    ap = session._build_parser()
    sa = [a for a in ap._actions if isinstance(a, argparse._SubParsersAction)][0]
    return set(sa.choices)


# ---- lệnh có backend session.py khớp ĐÚNG subcommand CLI thật --------
def test_session_backends_match_cli():
    backends = _backends()
    session_cmds = {b.split()[1] for b in backends.values() if b and b.startswith("session.py ")}
    assert session_cmds == _cli_subs() == set(session.CLI_COMMANDS)


# ---- mỗi backend session.py có hàm cmd_<x> thật ----------------------
def test_session_backends_have_cmd_functions():
    for b in _backends().values():
        if b and b.startswith("session.py "):
            assert hasattr(session, f"cmd_{b.split()[1]}"), b


# ---- /validate trỏ validate.py (có main) -----------------------------
def test_validate_backend_exists():
    backends = _backends()
    assert "/validate" in backends and backends["/validate"] == "validate.py"
    assert hasattr(V, "main")


# ---- registry phủ đủ lệnh spec 11A.3 ---------------------------------
def test_registry_covers_spec_commands():
    expected = {"/learn", "/review", "/resume", "/status", "/schedule", "/ask", "/source",
                "/test", "/gaps", "/skip", "/done", "/system", "/forget", "/fix", "/validate"}
    assert expected <= set(_backends())


# ---- backend null CHỈ được là các lệnh cố-ý-không-backend (chống bỏ sót) ----
def test_null_backends_are_intentional():
    """Lệnh null backend phải nằm trong tập cố-ý: /skip (session-flow, không ghi),
    /system (chỉ tạo CR), /fix (defer — rủi ro auto-format, xem decisions/DEC-026).
    Thêm lệnh mới mà quên backend (không thuộc tập này) → đỏ."""
    intentional_null = {"/skip", "/system", "/fix"}
    actual_null = {k for k, v in _backends().items() if v is None}
    assert actual_null <= intentional_null, f"lệnh thiếu backend ngoài dự kiến: {actual_null - intentional_null}"
