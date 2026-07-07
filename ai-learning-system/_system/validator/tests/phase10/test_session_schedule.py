"""P10 driver — cmd_schedule (CHỈ ĐỌC, spec 8.5): tích hợp trên vault thật + CLI introspect."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"


def test_schedule_demo_vault_new_item_not_due():
    # Vault demo: rv-001 mastery_state=new (log rỗng) → KHÔNG tự tới hạn (spec 8.5)
    at = datetime(2027, 1, 1, tzinfo=timezone.utc)  # xa về tương lai để chắc "quá hạn" nếu tính sai
    due = S.cmd_schedule(REAL_VAULT, ROOT, at, days=0)
    assert due == [], f"item 'new' không được tự tới hạn, nhưng: {due}"


def test_schedule_is_readonly_no_write(tmp_path):
    import shutil
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    before = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    S.cmd_schedule(v, ROOT, datetime(2027, 1, 1, tzinfo=timezone.utc), days=30)
    after = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    assert before == after, "cmd_schedule phải CHỈ ĐỌC, không được đổi file"


def test_schedule_in_cli_commands():
    assert "schedule" in S.CLI_COMMANDS and hasattr(S, "cmd_schedule")
