"""P10 — cmd_forget: xoá lesson có thẩm quyền (tombstone + INV-11) (spec 10.3a, 11A /forget)."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session          # noqa: E402
import validate as V    # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
REVIEWED_AT = datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc)
FORGET_AT = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)

VS_REL = Path("vault_state.md")
TS_REL = Path("topics") / "docker" / "topic_state.md"
LDIR = Path("topics") / "docker" / "lessons" / "lesson-001"


def _copy_vault(tmp_path) -> Path:
    dst = tmp_path / "learning_vault"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _raw(vault, rel):
    return session._load_raw(vault / rel)[0]


# ---- 1. chưa xác nhận → từ chối ---------------------------------------
def test_forget_requires_confirmation(tmp_path):
    vault = _copy_vault(tmp_path)
    with pytest.raises(session.SessionError):
        session.cmd_forget(vault, SYSTEM, "docker/lesson-001", "x", False, FORGET_AT)


# ---- 2. topic-level chưa hỗ trợ → SessionError ------------------------
def test_forget_topic_level_deferred(tmp_path):
    vault = _copy_vault(tmp_path)
    with pytest.raises(session.SessionError):
        session.cmd_forget(vault, SYSTEM, "docker", "x", True, FORGET_AT)


# ---- 3. lesson không tồn tại → SessionError ---------------------------
def test_forget_unknown_lesson(tmp_path):
    vault = _copy_vault(tmp_path)
    with pytest.raises(session.SessionError):
        session.cmd_forget(vault, SYSTEM, "docker/lesson-999", "x", True, FORGET_AT)


# ---- 4. forget lesson có item in_review → tombstone tha INV-11, commit, PASS
def test_forget_lesson_with_protected_item(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    # đưa rv-001 thành in_review (item được bảo vệ INV-11)
    c1, r1 = session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                                grade=2, reviewed_at=REVIEWED_AT)
    assert c1, r1.errors
    assert _raw(vault, Path("topics/docker/lessons/lesson-001/lesson_state.md"))["review_items"][0]["mastery_state"] == "in_review"

    committed, rep = session.cmd_forget(vault, SYSTEM, "docker/lesson-001",
                                        "học sai hướng, làm lại", True, FORGET_AT)
    assert committed is True, rep.errors
    assert rep.ok()

    # lesson dir bị xoá sạch (prune), index + con trỏ đồng bộ
    assert not (vault / LDIR).exists()
    assert _raw(vault, TS_REL)["lessons"] == []
    assert _raw(vault, TS_REL)["current_lesson"] is None
    assert _raw(vault, VS_REL)["current_lesson"] is None

    # tombstone materialize trong transaction_log.md (audit)
    log = (vault / "transaction_log.md").read_text(encoding="utf-8")
    assert "tombstone" in log and "rv-001" in log

    # end-to-end: validator thật trên vault sau forget → PASS
    rep2 = V.Report()
    V.validate_full_semantic(SYSTEM, vault, rep2, now=FORGET_AT)
    assert rep2.ok(), rep2.errors
