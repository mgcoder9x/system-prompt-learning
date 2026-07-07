"""P10 driver — cmd_test (CHỈ ĐỌC, spec 9.3 + CR-0002): báo cáo cổng learned_gate, KHÔNG ghi."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
LESSON = "docker/lesson-001"
LS = "topics/docker/lessons/lesson-001/lesson_state.md"


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def test_demo_gate_fails_on_score(tmp_path):
    # demo mastery toàn 0 → chưa đạt ngưỡng → gate_pass False, chặn bởi E-GATE-FAIL
    v = _fresh(tmp_path)
    r = S.cmd_test(v, ROOT, LESSON)
    assert r["gate_pass"] is False
    assert all(not d["meets"] for d in r["axes"].values())
    assert any("E-GATE-FAIL" in b for b in r["blocking"])


def test_scores_met_but_no_evidence_blocks_gate(tmp_path):
    # nâng điểm đạt ngưỡng NHƯNG không có evidence → gate vẫn fail vì E-ASSESS-NOEVIDENCE (INV-22)
    v = _fresh(tmp_path)
    raw, body = S._load_raw(v / LS)
    raw["mastery"] = {
        "concept": {"score": 2, "evidence": []}, "explain": {"score": 2, "evidence": []},
        "apply": {"score": 2, "evidence": []}, "critique": {"score": 1, "evidence": []},
        "teachback": {"score": 2, "evidence": []},
    }
    (v / LS).write_bytes(S._dump_state(raw, body))
    r = S.cmd_test(v, ROOT, LESSON)
    assert all(d["meets"] for d in r["axes"].values()), "điểm đã đạt ngưỡng"
    assert r["gate_pass"] is False, "thiếu evidence → cổng vẫn chưa qua"
    assert any("E-ASSESS-NOEVIDENCE" in b for b in r["blocking"])


def test_default_lesson_uses_current(tmp_path):
    v = _fresh(tmp_path)
    r = S.cmd_test(v, ROOT, None)  # None → vault_state.current_lesson = docker/lesson-001
    assert r["lesson_id"] == "docker/lesson-001"


def test_test_is_readonly(tmp_path):
    v = _fresh(tmp_path)
    before = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    S.cmd_test(v, ROOT, LESSON)
    after = {p.name: p.stat().st_mtime_ns for p in v.rglob("*") if p.is_file()}
    assert before == after, "/test phải CHỈ ĐỌC (CR-0002)"


def test_unknown_lesson_raises(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_test(v, ROOT, "docker/lesson-999")


def test_test_in_cli_commands():
    assert "test" in S.CLI_COMMANDS and hasattr(S, "cmd_test")
