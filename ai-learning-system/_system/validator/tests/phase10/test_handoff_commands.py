"""P10-agent — HANDOFF_TEST.md drift-guard: mọi lệnh trong bài test tiếp-quản phải TỒN TẠI trong registry.

NOTE-031: bản handoff cũ tham chiếu lệnh lệch/thiếu → AI nhận handoff gõ hỏng / dừng sớm. Test khoá:
(1) file tồn tại + non-empty; (2) mọi lệnh trong khối 'commands (máy đọc)' của HANDOFF_TEST đều XUẤT HIỆN
trong commands.md (registry — nguồn sự thật); (3) có mặt vòng giáo trình v2.7 (collect/curriculum/next-lesson/grade)
để handoff thực sự nghiệm thu hệ hiện tại, không phải chỉ vòng lõi cũ.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../_system
AI_ROOT = ROOT.parent                          # .../ai-learning-system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

HANDOFF = AI_ROOT / "HANDOFF_TEST.md"


def _handoff_commands():
    text = HANDOFF.read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "commands (máy đọc)", level=2)["commands"]


def test_handoff_exists_nonempty():
    assert HANDOFF.is_file(), "thiếu ai-learning-system/HANDOFF_TEST.md"
    assert HANDOFF.read_text(encoding="utf-8").strip()


def test_handoff_commands_exist_in_registry():
    registry_text = (ROOT / "commands.md").read_text(encoding="utf-8")
    missing = [c for c in _handoff_commands() if c not in registry_text]
    assert not missing, f"HANDOFF_TEST nhắc lệnh KHÔNG có trong registry commands.md: {missing}"


def test_handoff_covers_curriculum_cycle():
    cmds = set(_handoff_commands())
    need = {"/learn", "/validate", "/collect", "/curriculum", "/next-lesson", "/grade"}
    assert need <= cmds, f"HANDOFF_TEST thiếu lệnh vòng giáo trình v2.7: {sorted(need - cmds)}"
