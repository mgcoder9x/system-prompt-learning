"""P12 — drift-guard: PILOT_RUNBOOK.md chỉ tham chiếu lệnh CÓ THẬT (chống trôi runbook↔CLI).

Runbook là prose (nghiệm thu người+AI), nhưng phần lệnh phải kiểm được: mọi lệnh trong khối máy-đọc
`pilot_commands` phải ∈ session.CLI_COMMANDS ∪ {'validate' (validate.py)}. Thêm lệnh ma vào runbook → đỏ.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A   # noqa: E402
import session as S  # noqa: E402

RUNBOOK = ROOT / "PILOT_RUNBOOK.md"


def _pilot_commands():
    text = RUNBOOK.read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "pilot_commands (máy đọc)", level=3)["pilot_commands"]


def test_runbook_exists_nonempty():
    assert RUNBOOK.is_file() and RUNBOOK.read_text(encoding="utf-8").strip()


def test_pilot_commands_are_real():
    known = set(S.CLI_COMMANDS) | {"validate"}   # validate = validate.py (không ở CLI_COMMANDS)
    unknown = [c for c in _pilot_commands() if c not in known]
    assert not unknown, f"runbook tham chiếu lệnh không tồn tại: {unknown}"


def test_pilot_covers_core_daily_loop():
    # nhịp ngày lõi (§11B) phải có mặt trong runbook
    pc = set(_pilot_commands())
    assert {"status", "learn", "review", "done", "resume"} <= pc
