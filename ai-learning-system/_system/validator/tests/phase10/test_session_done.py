"""P10 tests — session driver /done: đóng sổ (spec 11B.2, 10.8).

/done phải: clear open_session.lesson_id/started_at + set last_full_validate + regen view,
tất cả trong CÙNG một transaction-FULL, và validate_full_core(vault) PASS sau commit.
"""
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
TZ7 = timezone(timedelta(hours=7))
REVIEWED_AT = datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc)
DONE_AT = datetime(2026, 7, 2, 12, 30, 0, tzinfo=timezone.utc)  # 19:30 +07

VS_REL = Path("vault_state.md")
TS_REL = Path("topics") / "docker" / "topic_state.md"
LS_REL = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"


def _copy_vault(tmp_path) -> Path:
    dst = tmp_path / "learning_vault"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _raw(vault: Path, rel: Path) -> dict:
    raw, _ = session._load_raw(vault / rel)
    return raw


def _validate_ok(vault: Path) -> V.Report:
    rep = V.Report()
    V.validate_full_core(SYSTEM, vault, rep, now=DONE_AT)
    return rep


def _set_open_session(vault: Path):
    """Mô phỏng /learn đã mở phiên: open_session.lesson_id != null."""
    vs = vault / VS_REL
    raw, body = session._load_raw(vs)
    raw["open_session"] = {
        "lesson_id": "docker/lesson-001",
        "started_at": "2026-07-02T09:00:00+07:00",
        "last_full_validate": None,
    }
    vs.write_bytes(session._dump_state(raw, body))


# ---- 1. /done clear cờ + validate PASS ---------------------------------
def test_done_clears_open_session_and_validates(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    _set_open_session(vault)
    assert _raw(vault, VS_REL)["open_session"]["lesson_id"] == "docker/lesson-001"

    committed, rep = session.cmd_done(vault, SYSTEM, "docker/lesson-001", done_at=DONE_AT)
    assert committed is True, rep.errors
    assert rep.ok()

    sess = _raw(vault, VS_REL)["open_session"]
    assert sess["lesson_id"] is None
    assert sess["started_at"] is None
    assert sess["last_full_validate"] is not None

    assert _validate_ok(vault).ok()


# ---- 2. /review rồi /done: end-to-end đóng sổ đúng ---------------------
def test_review_then_done_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    _set_open_session(vault)

    c1, r1 = session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                                grade=2, reviewed_at=REVIEWED_AT)
    assert c1, r1.errors
    c2, r2 = session.cmd_done(vault, SYSTEM, "docker/lesson-001", done_at=DONE_AT)
    assert c2, r2.errors

    # cờ đã clear, item review vẫn còn (log 1 event), validate PASS
    assert _raw(vault, VS_REL)["open_session"]["lesson_id"] is None
    assert len(_raw(vault, LS_REL)["review_items"][0]["log"]) == 1
    assert _validate_ok(vault).ok()


# ---- 3. tất định: 2 vault song song → bytes GIỐNG HỆT ------------------
def test_done_determinism(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v1 = _copy_vault(tmp_path / "a"); _set_open_session(v1)
    v2 = _copy_vault(tmp_path / "b"); _set_open_session(v2)

    session.cmd_done(v1, SYSTEM, "docker/lesson-001", done_at=DONE_AT)
    session.cmd_done(v2, SYSTEM, "docker/lesson-001", done_at=DONE_AT)

    assert (v1 / VS_REL).read_bytes() == (v2 / VS_REL).read_bytes()
    assert (v1 / TS_REL).read_bytes() == (v2 / TS_REL).read_bytes()


# ---- 4. OCC: vault_state đổi giữa đọc-context và begin → E-STALE-CONTEXT
def test_done_occ_stale_context(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)

    orig_begin = TX.Transaction.begin

    def begin_after_tamper(self, writes, tombstones=None):
        (self.root / writes[0].target).write_text("tampered\n", encoding="utf-8")
        return orig_begin(self, writes, tombstones)

    monkeypatch.setattr(TX.Transaction, "begin", begin_after_tamper)
    with pytest.raises(TX.TxError) as ei:
        session.cmd_done(vault, SYSTEM, "docker/lesson-001", done_at=DONE_AT)
    assert ei.value.code == "E-STALE-CONTEXT"


def test_done_syncs_topic_index_status_from_lesson(tmp_path):
    """Bug (pilot self-simulate): topic_state.lessons[].status là VIEW của lesson_state.status (spec §4),
    nhưng /done regen review_schedule/assessment/has_draft mà KHÔNG đồng bộ index status → khi status lesson
    đổi (vd in_progress→needs_review) → E-INDEX-MISMATCH. RED-first."""
    vault = _copy_vault(tmp_path)
    raw, body = session._load_raw(vault / LS_REL)   # docker lesson demo: in_progress
    raw["status"] = "needs_review"                  # đổi status (không cần cổng learned)
    (vault / LS_REL).write_bytes(session._dump_state(raw, body))
    committed, rep = session.cmd_done(vault, SYSTEM, "docker/lesson-001", DONE_AT)
    assert committed, f"/done phải commit sau khi đồng bộ index status: {rep.errors}"
    ts = _raw(vault, TS_REL)
    entry = next(e for e in ts["lessons"] if e["id"] == "docker/lesson-001")
    assert entry["status"] == "needs_review", "topic index status phải đồng bộ từ lesson_state.status (spec §4)"
