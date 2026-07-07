"""P08/INV-06 — chuyển status lesson hợp lệ (spec 6.1), kiểm DIFF backup↔staged trong transaction.

Pure: check_status_transition/extract_lesson_status. Wiring: validate_staged bắt E-STATE-ILLEGAL
(stub validate_full_semantic để cách ly).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import transaction as TX  # noqa: E402
import validate as V      # noqa: E402
import vault_io as VIO    # noqa: E402

REL = "topics/docker/lessons/lesson-001/lesson_state.md"


def _ls(status: str) -> str:
    return (f"---\nschema: lesson_state\nschema_version: 1\nlesson_id: docker/lesson-001\n"
            f"title: t\nstatus: {status}\ncreated: 2026-06-30\nupdated: 2026-06-30\n"
            f"objective: o\nmastery:\n  concept: {{score: 0, evidence: []}}\n"
            f"  explain: {{score: 0, evidence: []}}\n  apply: {{score: 0, evidence: []}}\n"
            f"  critique: {{score: 0, evidence: []}}\n  teachback: {{score: 0, evidence: []}}\n"
            f"review_items: []\n---\n")


# ---- pure: extract_lesson_status --------------------------------------
def test_extract_status():
    assert V.extract_lesson_status(_ls("in_progress")) == "in_progress"
    assert V.extract_lesson_status("no frontmatter") is None


# ---- pure: cạnh hợp lệ / không hợp lệ / giữ nguyên -------------------
def test_valid_edges():
    for a, b in [("not_started", "in_progress"), ("in_progress", "learned"),
                 ("in_progress", "needs_review"), ("needs_review", "in_progress"),
                 ("learned", "needs_review")]:
        rep = V.Report(); V.check_status_transition(a, b, rep)
        assert rep.ok(), (a, b)


def test_same_status_ok():
    rep = V.Report(); V.check_status_transition("in_progress", "in_progress", rep)
    assert rep.ok()


def test_illegal_edges():
    for a, b in [("not_started", "learned"), ("learned", "in_progress"),
                 ("needs_review", "learned"), ("learned", "not_started")]:
        rep = V.Report(); V.check_status_transition(a, b, rep)
        assert "E-STATE-ILLEGAL" in {e["error_code"] for e in rep.errors}, (a, b)


# ---- wiring: validate_staged bắt cạnh không hợp lệ -------------------
def _staged_codes(tmp_path, monkeypatch, before, after):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    monkeypatch.setattr(V, "validate_full_semantic", lambda *a, **k: None)
    p = tmp_path / REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_ls(before), encoding="utf-8")
    h = VIO.content_hash(p)
    tx = TX.Transaction(tmp_path, level="full")
    tx.begin([TX.Write(REL, _ls(after).encode("utf-8"), expected_read_hash=h)])
    tx.stage()
    rep = tx.validate_staged(ROOT, "full")
    tx.abort()
    return {e["error_code"] for e in rep.errors}


def test_wired_illegal_transition(tmp_path, monkeypatch):
    assert "E-STATE-ILLEGAL" in _staged_codes(tmp_path, monkeypatch, "not_started", "learned")


def test_wired_legal_transition(tmp_path, monkeypatch):
    assert "E-STATE-ILLEGAL" not in _staged_codes(tmp_path, monkeypatch, "in_progress", "learned")
