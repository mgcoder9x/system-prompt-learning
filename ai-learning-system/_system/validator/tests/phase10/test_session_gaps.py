"""P10 driver — cmd_gaps (CHỈ ĐỌC, spec 11A.2): liệt kê open_gaps mọi lesson."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"


def test_gaps_demo_empty():
    # demo docker/lesson-001 có open_gaps: [] → rỗng
    assert S.cmd_gaps(REAL_VAULT, ROOT) == []


def test_gaps_lists_when_present(tmp_path):
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    ls = v / "topics/docker/lessons/lesson-001/lesson_state.md"
    txt = ls.read_text(encoding="utf-8").replace(
        "open_gaps: []",
        "open_gaps:\n  - id: gap-001\n    desc: Nhầm container với máy ảo\n    detected: 2026-06-30")
    ls.write_text(txt, encoding="utf-8")
    gaps = S.cmd_gaps(v, ROOT)
    assert len(gaps) == 1
    g = gaps[0]
    assert g["lesson_id"] == "docker/lesson-001" and g["gap_id"] == "gap-001"
    assert g["detected"] == "2026-06-30" and "máy ảo" in g["desc"]


def test_gaps_readonly(tmp_path):
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    before = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    S.cmd_gaps(v, ROOT)
    after = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    assert before == after, "gaps phải CHỈ ĐỌC"


def test_gaps_in_cli_commands():
    assert "gaps" in S.CLI_COMMANDS and hasattr(S, "cmd_gaps")
