"""P07a — Exam_Results ref-integrity (Class A): E-EXAM-REF-BROKEN.

exam_results.md là bản ghi CHẤM (metadata, KHÔNG code) TRONG vault; bài nộp (Exam_Submission) có thể là
CODE nên nằm NGOÀI vault (ai-learning-system/exam/...). Máy chỉ đảm bảo (Class A) ref-integrity:
  - `ref` trỏ bài nộp TỒN TẠI (đường dẫn tương đối tới exam/ ngoài vault)  → nếu không: E-EXAM-REF-BROKEN
  - `target` là topic hiện tại HOẶC một Curriculum_Point tồn tại           → nếu không: E-EXAM-REF-BROKEN
`verdict` là Class D (không kiểm nội dung). RED-first: V._check_exam_results chưa tồn tại → đỏ.

Đây là ENFORCEMENT của schema exam_results (đã duyệt CR-0007), giống Task 3 (validator đọc-kiểm) —
KHÔNG cần CR-0008 (CR đó cho LỆNH GHI cmd_grade). Tiền lệ DEC-034/058.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402


def _result(sid: str, ref: str, target: str, graded: str = "2026-06-30", verdict: str = "Đạt cơ bản") -> str:
    return (f"  - submission_id: {sid}\n"
            f"    ref: \"{ref}\"\n"
            f"    target: {target}\n"
            f"    graded_at: {graded}\n"
            f"    verdict: \"{verdict}\"\n")


def _write_exam_results(topic_dir: Path, results_yaml: str) -> None:
    topic_dir.mkdir(parents=True, exist_ok=True)
    fm = ("---\n"
          "schema: exam_results\n"
          "schema_version: 1\n"
          "topic_id: docker\n"
          "results:\n"
          f"{results_yaml}"
          "---\n\n# Kết quả chấm bài thực hành\n")
    (topic_dir / "exam_results.md").write_text(fm, encoding="utf-8")


def _make_submission(vault_root: Path, rel_from_topic: str = "docker/ex-001") -> None:
    """Tạo bài nộp NGOÀI vault: ai-learning-system/exam/<...>. vault_root = .../learning_vault."""
    p = vault_root.parent / "exam" / rel_from_topic
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("print('bai nop cua nguoi hoc')\n", encoding="utf-8")


def _codes(topic_dir: Path, vault_root: Path) -> list[str]:
    rep = V.Report()
    V._check_exam_results(topic_dir, vault_root, rep)
    return [e["error_code"] for e in rep.errors]


def test_valid_exam_result_no_error(tmp_path):
    v = tmp_path / "learning_vault"
    td = v / "topics" / "docker"
    _make_submission(v, "docker/ex-001")
    _write_exam_results(td, _result("ex-001", "../../../exam/docker/ex-001", "docker"))
    assert _codes(td, v) == []


def test_absent_exam_results_no_error(tmp_path):
    v = tmp_path / "learning_vault"
    td = v / "topics" / "docker"
    td.mkdir(parents=True)
    assert _codes(td, v) == []


def test_broken_submission_ref(tmp_path):
    v = tmp_path / "learning_vault"
    td = v / "topics" / "docker"
    # KHÔNG tạo bài nộp → ref trỏ file không tồn tại
    _write_exam_results(td, _result("ex-001", "../../../exam/docker/ex-999", "docker"))
    assert "E-EXAM-REF-BROKEN" in _codes(td, v)


def test_broken_target(tmp_path):
    v = tmp_path / "learning_vault"
    td = v / "topics" / "docker"
    _make_submission(v, "docker/ex-001")
    # target cp-999 không phải topic, không có curriculum → không hợp lệ
    _write_exam_results(td, _result("ex-001", "../../../exam/docker/ex-001", "cp-999"))
    assert "E-EXAM-REF-BROKEN" in _codes(td, v)
