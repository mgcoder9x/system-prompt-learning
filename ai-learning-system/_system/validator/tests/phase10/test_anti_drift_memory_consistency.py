"""P10-agent — anti_drift_rules.md + memory_rules.md khớp nguồn kiểm-được (chống trôi).

- anti_drift.code_enforced[].code phải ⊆ tập mã lỗi thật (validation_rules.md → error_codes).
- memory context_boot.load_only phải == danh sách nạp spec §11B.1.
- cả hai file tồn tại, non-empty.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

RULES = ROOT / "rules"

# spec §11B.1: chỉ nạp 3 nhóm này khi /resume|/status
SPEC_BOOT_LOAD_ONLY = {"state_files", "lesson_notes", "latest_sessions_only"}


def _error_codes():
    text = (RULES / "validation_rules.md").read_text(encoding="utf-8")
    return set(A.extract_yaml_under_heading(text, "error_codes (máy đọc)", level=3)["error_codes"])


def _anti_drift():
    text = (RULES / "anti_drift_rules.md").read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "anti_drift (máy đọc)", level=3)["anti_drift"]


def _context_boot():
    text = (RULES / "memory_rules.md").read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "context_boot (máy đọc)", level=3)["context_boot"]


def test_anti_drift_codes_are_real():
    codes = {row["code"] for row in _anti_drift()["code_enforced"]}
    real = _error_codes()
    assert codes <= real, f"anti_drift dùng mã không có thật trong validation_rules: {sorted(codes - real)}"


def test_anti_drift_has_process_layer():
    # Trung thực: phải liệt kê cả rủi ro chỉ process chặn được (không code)
    assert _anti_drift()["process_enforced"], "thiếu lớp process_enforced"


def test_memory_boot_matches_spec():
    load_only = set(_context_boot()["load_only"])
    assert load_only == SPEC_BOOT_LOAD_ONLY, f"lệch spec §11B.1: {load_only ^ SPEC_BOOT_LOAD_ONLY}"


def test_both_rule_files_present_nonempty():
    for name in ("anti_drift_rules.md", "memory_rules.md"):
        p = RULES / name
        assert p.is_file() and p.read_text(encoding="utf-8").strip(), f"thiếu/rỗng rules/{name}"
