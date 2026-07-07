"""P10-agent — HUONG_DAN.md (hướng dẫn NGƯỜI HỌC) drift-guard: mọi lệnh nêu phải TỒN TẠI trong registry.

Hướng dẫn liệt kê lệnh cho người dùng; nếu nó nhắc lệnh KHÔNG có trong commands.md (đổi tên/bịa) → người
dùng gõ sẽ hỏng. Test khoá: (1) file tồn tại + non-empty; (2) mọi lệnh trong khối 'commands (máy đọc)' của
hướng dẫn đều XUẤT HIỆN trong commands.md (registry — nguồn sự thật); (3) có các lệnh học cốt lõi.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../_system
AI_ROOT = ROOT.parent                          # .../ai-learning-system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

GUIDE = AI_ROOT / "HUONG_DAN.md"


def _guide_commands():
    text = GUIDE.read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "commands (máy đọc)", level=2)["commands"]


def test_guide_exists_nonempty():
    assert GUIDE.is_file(), "thiếu ai-learning-system/HUONG_DAN.md (hướng dẫn người học)"
    assert GUIDE.read_text(encoding="utf-8").strip()


def test_guide_commands_exist_in_registry():
    registry_text = (ROOT / "commands.md").read_text(encoding="utf-8")
    missing = [c for c in _guide_commands() if c not in registry_text]
    assert not missing, f"HUONG_DAN nhắc lệnh KHÔNG có trong registry commands.md: {missing}"


def test_guide_covers_core_learning_commands():
    cmds = set(_guide_commands())
    core = {"/learn", "/review", "/done", "/status"}
    assert core <= cmds, f"hướng dẫn thiếu lệnh học cốt lõi: {sorted(core - cmds)}"
