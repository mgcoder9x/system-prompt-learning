"""Phase 1 orchestrator — RED-first tests cho SPEC_PHASE1_ORCHESTRATOR (R-ORCH-1..4).

Chứng minh trust model DEC-081: orchestrator author nội-dung-dạy; KERNEL cmd_done là CỔNG.
Tách khỏi kernel (product/) → KHÔNG đụng suite 520 của kernel. LLM = stub tất định (offline).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

WS = Path(__file__).resolve().parents[2]                 # workspace root
KERNEL_SYS = WS / "ai-learning-system" / "_system"
DEMO = KERNEL_SYS / "validator" / "tests" / "fixtures" / "demo_vault"
sys.path.insert(0, str(WS / "product"))                  # cho 'import orchestrator...'
sys.path.insert(0, str(KERNEL_SYS / "validator"))        # kernel (session/validate) cho setup

import session as S       # noqa: E402  (kernel — setup)
import validate as V      # noqa: E402
from orchestrator.teaching_session import TeachingSession, EvidenceNotVerbatim, GATE_AXES  # noqa: E402

AT = datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc)
DONE_AT = datetime(2026, 7, 6, 5, 0, tzinfo=timezone.utc)
# điểm đạt cổng (_GATE: critique=1, còn lại=2)
PASS_SCORES = {"concept": 2, "explain": 2, "apply": 2, "critique": 1, "teachback": 2}
# câu trả lời THẬT của người học cho mỗi trục
ANSWERS = {
    "concept": "Git là hệ quản lý phiên bản phân tán theo dõi thay đổi mã nguồn.",
    "explain": "git init tạo một kho chứa cục bộ với thư mục ẩn chấm git.",
    "apply": "Tôi gõ git init trong thư mục dự án để bắt đầu theo dõi.",
    "critique": "Nếu quên git init thì các lệnh git khác sẽ báo lỗi không phải kho.",
    "teachback": "Tóm lại git init khởi tạo kho cục bộ để bắt đầu quản lý phiên bản.",
}


class StubLLM:
    """LLM tất định (offline). propose_evidence trả nguyên câu trả lời (⇒ verbatim) trừ khi fake_axis."""
    def __init__(self, fake_axis: str | None = None):
        self.fake_axis = fake_axis

    def propose_question(self, context: str) -> str:
        return f"Bạn hiểu gì về {context}?"

    def propose_evidence(self, answer_text: str, axis: str) -> str:
        if axis == self.fake_axis:
            return "CHUOI BIA KHONG HE CO TRONG CAU TRA LOI"
        return answer_text


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(DEMO, v)
    return v


def _new_topic(v: Path, topic="gitlearn") -> str:
    c, rep = S.cmd_learn(v, KERNEL_SYS, topic, "Git", "Bài 1", "Hiểu git init", AT)
    assert c, rep.errors
    return f"{topic}/lesson-001"


def _full_codes(v: Path):
    rep = V.Report()
    V.validate_full_semantic(KERNEL_SYS, v, rep, now=DONE_AT)
    return [e["error_code"] for e in rep.errors]


def test_happy_path_learned_via_kernel(tmp_path):
    """R-ORCH-1: dạy đủ 5 trục, evidence verbatim, điểm đạt → kernel cmd_done COMMIT → learned=True + validate PASS."""
    v = _fresh(tmp_path)
    lid = _new_topic(v)
    ts = TeachingSession(v, KERNEL_SYS, StubLLM(), DONE_AT)
    for ax in GATE_AXES:
        ts.submit_answer(ax, ANSWERS[ax], PASS_SCORES[ax])
    learned, report = ts.finalize(lid)
    assert learned, report.errors
    raw = S._load_raw(v / "topics" / "gitlearn" / "lessons" / "lesson-001" / "lesson_state.md")[0]
    assert raw["status"] == "learned"
    assert "E-GATE-FAIL" not in _full_codes(v) and "E-ASSESS-FAKEQUOTE" not in _full_codes(v)


def test_gate_fail_not_learned(tmp_path):
    """R-ORCH-1/4: thiếu trục (điểm 0 < ngưỡng) → kernel KHÔNG commit → learned=False + E-GATE-FAIL. Orchestrator KHÔNG tự nhận."""
    v = _fresh(tmp_path)
    lid = _new_topic(v)
    ts = TeachingSession(v, KERNEL_SYS, StubLLM(), DONE_AT)
    for ax in ("concept", "explain", "apply"):   # thiếu critique + teachback
        ts.submit_answer(ax, ANSWERS[ax], PASS_SCORES[ax])
    learned, report = ts.finalize(lid)
    assert not learned
    assert any(e["error_code"] == "E-GATE-FAIL" for e in report.errors), report.errors


def test_reject_non_verbatim_evidence(tmp_path):
    """R-ORCH-3: LLM đề xuất quote KHÔNG có trong câu trả lời thật → orchestrator TỪ CHỐI (raise), không lưu."""
    v = _fresh(tmp_path)
    _new_topic(v)
    ts = TeachingSession(v, KERNEL_SYS, StubLLM(fake_axis="concept"), DONE_AT)
    with pytest.raises(EvidenceNotVerbatim):
        ts.submit_answer("concept", ANSWERS["concept"], 2)


def test_fakequote_caught_by_kernel_defense_in_depth(tmp_path):
    """R-ORCH-3 backstop: nếu kiểm verbatim của orchestrator bị BỎ QUA (giả lập bằng nhét quote bịa
    trực tiếp), kernel cmd_done VẪN chặn (E-ASSESS-FAKEQUOTE) → learned=False. Kernel là cổng."""
    v = _fresh(tmp_path)
    lid = _new_topic(v)
    ts = TeachingSession(v, KERNEL_SYS, StubLLM(), DONE_AT)
    for ax in GATE_AXES:
        ts.submit_answer(ax, ANSWERS[ax], PASS_SCORES[ax])
    ts._quotes["concept"] = "CHUOI BIA HOAN TOAN KHONG CO TRONG TRANSCRIPT"   # bỏ qua kiểm (giả lập bug)
    learned, report = ts.finalize(lid)
    assert not learned
    assert any(e["error_code"] == "E-ASSESS-FAKEQUOTE" for e in report.errors), report.errors


def test_deterministic_offline(tmp_path):
    """R-ORCH determinism: cùng stub + cùng at → cùng kết quả (không mạng)."""
    results = []
    for i in range(2):
        v = _fresh(tmp_path / f"run{i}")
        lid = _new_topic(v)
        ts = TeachingSession(v, KERNEL_SYS, StubLLM(), DONE_AT)
        for ax in GATE_AXES:
            ts.submit_answer(ax, ANSWERS[ax], PASS_SCORES[ax])
        learned, report = ts.finalize(lid)
        results.append((learned, tuple(sorted(e["error_code"] for e in report.errors))))
    assert results[0] == results[1]
