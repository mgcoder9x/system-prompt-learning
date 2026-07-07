"""P10-agent — scaffolding change_requests/ khớp vòng đời trạng thái tài liệu (chống trôi doc↔đĩa).

states trong system_change_prompt.md (khối change_request) phải có thư mục thật tương ứng dưới
change_requests/, và `log` (changelog.md) phải tồn tại. cr-0001 (v2.6) phải ở approved/ và được changelog trỏ.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

CR_DIR = ROOT / "change_requests"


def _lifecycle():
    text = (ROOT / "prompts" / "system_change_prompt.md").read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "Vòng đời trạng thái", level=2)["change_request"]


def test_state_folders_and_log_exist():
    cr = _lifecycle()
    for state in cr["states"]:
        assert (CR_DIR / state).is_dir(), f"thiếu thư mục change_requests/{state}/"
    assert (CR_DIR / cr["log"]).is_file(), f"thiếu change_requests/{cr['log']}"


def test_cr0001_approved_and_logged():
    cr_file = CR_DIR / "approved" / "cr-0001-fsrs-spec-v2.6.md"
    assert cr_file.is_file(), "thiếu approved/cr-0001-fsrs-spec-v2.6.md"
    changelog = (CR_DIR / "changelog.md").read_text(encoding="utf-8")
    assert "cr-0001" in changelog, "changelog.md không trỏ cr-0001"
