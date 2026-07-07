"""P10/P08 — validate_staged(level='full') phải chạy SEMANTIC (spec 10.8: FULL = INV-01..26).

Trước fix, validate_staged 'full' chỉ chạy validate_full_core → /review /done bỏ lọt INV semantic
tại điểm commit. Test: stage lesson status=learned (mastery 0) → validate_staged 'full' bắt E-GATE-FAIL.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session          # noqa: E402
import transaction as TX  # noqa: E402
import vault_io as VIO    # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
LS_REL = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"


def _copy_vault(tmp_path) -> Path:
    dst = tmp_path / "learning_vault"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def test_validate_staged_full_runs_semantic(tmp_path):
    vault = _copy_vault(tmp_path)
    ls_path = vault / LS_REL
    raw, body = session._load_raw(ls_path)
    raw["status"] = "learned"          # learned nhưng mastery toàn 0 → vi phạm cổng (INV-07)
    new_bytes = session._dump_state(raw, body)
    h = VIO.content_hash(ls_path)

    tx = TX.Transaction(vault, level="full")
    tx.begin([TX.Write(LS_REL.as_posix(), new_bytes, expected_read_hash=h)])
    tx.stage()
    rep = tx.validate_staged(SYSTEM, "full")
    tx.abort()

    codes = {e["error_code"] for e in rep.errors}
    assert "E-GATE-FAIL" in codes, codes  # chứng minh semantic đã chạy trong validate_staged
