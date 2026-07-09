"""Phase 1 orchestrator (headless) — hiện thực SPEC_PHASE1_ORCHESTRATOR + trust model DEC-081.

Bản chất (QĐ-2/A2): CHÍNH SẢN PHẨM (orchestrator) ép kernel, không phụ thuộc thiện chí LLM.
- Orchestrator ĐƯỢC author NỘI DUNG DẠY (transcript + evidence trong lesson.md) — vai AI hợp lệ
  (kernel KHÔNG có lệnh ghi nội dung dạy; đây là "việc AI trong phiên" — DEC-081).
- NHƯNG phán quyết "learned" CHỈ hợp lệ khi kernel `cmd_done` COMMIT (FULL-validate PASS): evidence bịa /
  chưa đủ cổng → kernel chặn (E-ASSESS-FAKEQUOTE / E-GATE-FAIL). KERNEL LÀ CỔNG, không phải orchestrator.
- LLM được INJECT (Phase 1 = stub tất định, offline). KHÔNG đổi kernel (moat giữ nguyên).
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Protocol

# Kernel REUSE (in-process — SD-2, đúng API mà suite 520 đang gọi). KHÔNG đổi kernel.
_KERNEL = Path(__file__).resolve().parents[2] / "ai-learning-system" / "_system" / "validator"
if str(_KERNEL) not in sys.path:
    sys.path.insert(0, str(_KERNEL))

import session as S      # driver kernel: cmd_learn/cmd_done/_load_raw/_dump_state
import canonical as C    # normalize_for_match — MIRROR đúng luật verbatim của validator (E-ASSESS-FAKEQUOTE)

# 5 trục cổng learned_gate (đồng bộ validate._GATE; critique=1, còn lại=2 — kernel là chân lý ngưỡng).
GATE_AXES = ("concept", "explain", "apply", "critique", "teachback")


class LLM(Protocol):
    """Nhà cung cấp nội dung (Phase 1 = stub; Phase 4 = adapter BYO-key/local). CHỈ đề xuất, KHÔNG ghi vault."""
    def propose_question(self, context: str) -> str: ...
    def propose_evidence(self, answer_text: str, axis: str) -> str: ...


class EvidenceNotVerbatim(ValueError):
    """R-ORCH-3: evidence-đề-xuất KHÔNG phải chuỗi con verbatim của câu trả lời THẬT của người học."""


def _is_verbatim(quote: str, answer: str) -> bool:
    """Mirror validate._check_gate_and_evidence: normalize rồi kiểm substring (dung sai như kernel)."""
    nq = C.normalize_for_match(quote)
    return bool(nq) and nq in C.normalize_for_match(answer)


class TeachingSession:
    """Một buổi dạy tối thiểu (headless) cho MỘT lesson đã tồn tại. Orchestrator ép kernel làm cổng."""

    def __init__(self, vault, system, llm: LLM, at: datetime):
        self.vault = Path(vault)
        self.system = Path(system)
        self.llm = llm
        self.at = at
        self._answers: dict[str, str] = {}   # axis -> câu trả lời THẬT của người học
        self._quotes: dict[str, str] = {}    # axis -> quote verbatim (đã kiểm)
        self._scores: dict[str, int] = {}    # axis -> điểm (do người/AI chấm; kernel gác ngưỡng)

    def ask(self, context: str) -> str:
        """Lấy câu hỏi từ LLM. KHÔNG ghi vault."""
        return self.llm.propose_question(context)

    def submit_answer(self, axis: str, learner_text: str, score: int) -> None:
        """Nhận câu trả lời THẬT + điểm. LLM đề xuất evidence quote; orchestrator KIỂM verbatim (R-ORCH-3)
        → không verbatim thì TỪ CHỐI (raise), KHÔNG tự sửa lời người học, KHÔNG lưu."""
        if axis not in GATE_AXES:
            raise ValueError(f"trục không hợp lệ: {axis!r}")
        proposed = self.llm.propose_evidence(learner_text, axis)
        if not _is_verbatim(proposed, learner_text):
            raise EvidenceNotVerbatim(f"trục {axis!r}: quote đề xuất không có trong câu trả lời thật (R-ORCH-3)")
        self._answers[axis] = learner_text
        self._quotes[axis] = proposed
        self._scores[axis] = int(score)

    def _author(self, lesson_id: str) -> None:
        """Author lesson_state (status=learned + mastery) + lesson.md (Sessions + transcript + evidence),
        theo đúng công thức đã được test kernel chứng minh PASS. KHÔNG chốt — chỉ đề xuất nội dung."""
        topic, name = lesson_id.split("/", 1)
        ld = self.vault / "topics" / topic / "lessons" / name
        lp = ld / "lesson_state.md"
        raw, body = S._load_raw(lp)
        raw["status"] = "learned"
        for ax in GATE_AXES:
            raw["mastery"][ax] = {"score": self._scores.get(ax, 0), "evidence": []}
        lp.write_bytes(S._dump_state(raw, body))

        date = self.at.date().isoformat()
        transcript = " ".join(self._answers[ax] for ax in GATE_AXES if ax in self._answers)
        evs = "\n".join(
            f'#### Evidence ev-{ax}\n\n```yaml\naxis: {ax}\ntimestamp: {date}\n'
            f'quote: "{self._quotes[ax]}"\nai_assessment: "đạt"\n```\n'
            for ax in GATE_AXES if ax in self._quotes)
        md = (f"# {name}\n\n## Mục tiêu\nHọc.\n\n## Sessions\n\n"
              f"### Session {date}\n#### Bạn trả lời q1\n{transcript}\n\n{evs}")
        (ld / "lesson.md").write_text(md, encoding="utf-8")

    def finalize(self, lesson_id: str):
        """Author nội dung rồi CHỐT qua kernel `cmd_done` (CỔNG FULL-validate). Trả (learned, report).
        learned = committed AND report.ok() — phán quyết do KERNEL, KHÔNG do orchestrator tự nhận (R-ORCH-1/4)."""
        self._author(lesson_id)
        committed, report = S.cmd_done(self.vault, self.system, lesson_id, self.at)
        return (bool(committed) and report.ok()), report
