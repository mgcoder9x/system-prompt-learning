"""P10-agent — audit.py (báo cáo CHỈ-ĐỌC 'folder đã làm gì') đúng + ROBUST (vault hỏng không crash)."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../_system
sys.path.insert(0, str(ROOT))                  # import audit (ở _system/)
sys.path.insert(0, str(ROOT / "validator"))

import audit as AU        # noqa: E402
import session as S       # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
NOW = datetime(2026, 7, 4, 12, 0, tzinfo=timezone.utc)
LS_REL = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"


def _copy(tmp):
    v = tmp / "v"
    shutil.copytree(VAULT_SRC, v)
    return v


def test_audit_real_vault_pass_and_structure(tmp_path):
    v = _copy(tmp_path)
    rep = AU.audit(v, SYSTEM, now=NOW)
    assert rep["integrity"]["pass"] is True, rep["integrity"]["errors"]
    assert rep["current"]["topic"] == "docker"
    docker = next(t for t in rep["topics"] if t["topic"] == "docker")
    lids = {l["lesson_id"] for l in docker["lessons"]}
    assert "docker/lesson-001" in lids
    assert rep["summary"]["n_topics"] >= 1 and rep["summary"]["n_review_items"] >= 1


def test_audit_reports_corruption_no_crash(tmp_path):
    v = _copy(tmp_path)
    p = v / LS_REL
    p.write_text(p.read_text(encoding="utf-8").replace("concept: {score: 0", "concept: {score: 99"),
                 encoding="utf-8")
    rep = AU.audit(v, SYSTEM, now=NOW)          # KHÔNG được crash
    assert rep["integrity"]["pass"] is False
    assert any(e.get("error_code") == "E-SCHEMA" for e in rep["integrity"]["errors"])


def test_audit_activity_history_from_log(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _copy(tmp_path)
    # tạo hoạt động thật → transaction_log.md ghi lại
    S.cmd_review(v, SYSTEM, "docker/lesson-001", "rv-001", 2,
                 datetime(2026, 7, 4, 9, 0, tzinfo=timezone.utc))
    rep = AU.audit(v, SYSTEM, now=NOW)
    assert rep["summary"]["n_transactions"] >= 1
    assert any(any("lesson_state.md" in w for w in a["writes"]) for a in rep["activity"])


def test_audit_empty_activity_when_no_log(tmp_path):
    v = _copy(tmp_path)   # vault demo chưa có transaction_log.md
    rep = AU.audit(v, SYSTEM, now=NOW)
    assert rep["activity"] == []
