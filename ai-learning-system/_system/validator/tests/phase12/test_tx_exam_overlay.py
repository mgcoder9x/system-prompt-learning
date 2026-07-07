"""P12 regression (DEC-073) — E-EXAM-REF-BROKEN GIẢ trong transaction-overlay.

Bug tích hợp THẬT (do cross-AI handoff #2 phát hiện, E2E cũ bỏ sót vì chỉ validate STANDALONE):
  transaction._build_overlay() copy NỘI DUNG VAULT vào thư mục TEMP; exam/ là SIBLING NGOÀI vault
  nên KHÔNG có trong overlay. validate_staged chạy validate_full_semantic (FULL) trên overlay →
  _check_exam_results resolve ref bài nộp về TEMP (không có exam/) → E-EXAM-REF-BROKEN GIẢ →
  BẤT KỲ lệnh FULL-transaction nào SAU khi 1 topic có exam_results.md (từ /grade) đều bị ABORT oan.

Fix GỐC (DEC-073, KHÔNG hack theo tên temp-dir/__file__ như bản copy Gemini — giữ portability INV-16):
  thread vault root THẬT (transaction.self.root) vào validate → _check_exam_results resolve ref +
  exam/ về vault thật. Standalone (real_vault_root=None) giữ hành vi cũ.

RED-first: probe _probe.py trước fix in `next_lesson committed: False ['E-EXAM-REF-BROKEN']`;
sau fix `True []`. Test dưới KHOÁ cả hai chiều: (1) không báo GIẢ; (2) vẫn bắt ref hỏng THẬT (teeth).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S       # noqa: E402
import validate as V      # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc)
POINTS = json.dumps([{"objective": "Container la gi"}, {"objective": "Image va Dockerfile"}])

_IGNORE = {".tx", "_scratch", ".cache", ".git", "__pycache__", ".pytest_cache", ".venv"}


def _build_vault_with_exam(tmp_path):
    """Dựng vault (copy demo) + curriculum teachable + exam_results.md (ref bài nộp THẬT ngoài vault)."""
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    c, rep = S.cmd_curriculum(v, SYSTEM, "docker", POINTS, AT)
    assert c, rep.errors
    sub = tmp_path / "exam" / "docker" / "sol.py"
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.write_text("print('ok')\n", encoding="utf-8")
    c, rep = S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub), target="cp-001", verdict="pass", at=AT)
    assert c, rep.errors
    assert (v / "topics" / "docker" / "exam_results.md").is_file()
    return v


def test_full_tx_after_exam_results_no_false_exam_ref(tmp_path, monkeypatch):
    """Lệnh FULL-transaction (next_lesson) SAU khi có exam_results.md KHÔNG bị E-EXAM-REF-BROKEN giả."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _build_vault_with_exam(tmp_path)
    c, rep = S.cmd_next_lesson(v, SYSTEM, "docker", AT)
    codes = [e["error_code"] for e in rep.errors]
    assert c, f"full-tx phải commit, nhưng abort với {codes}"
    assert "E-EXAM-REF-BROKEN" not in codes, codes


def _simulate_overlay(v: Path) -> Path:
    """Sao chép NỘI DUNG VAULT sang TEMP (KHÔNG kèm sibling exam/) — mô phỏng _build_overlay."""
    ov = Path(tempfile.mkdtemp(prefix="tx_overlay_sim_"))
    for src in v.rglob("*"):
        rel = src.relative_to(v)
        if _IGNORE & set(rel.parts):
            continue
        dst = ov / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return ov


def _exam_codes_on_overlay(v: Path, overlay: Path):
    rep = V.Report()
    # real_vault_root=v (vault THẬT có sibling exam/) — đúng như transaction truyền self.root
    V.validate_full_semantic(SYSTEM, overlay, rep, now=AT, real_vault_root=v)
    return [e["error_code"] for e in rep.errors if e["error_code"] == "E-EXAM-REF-BROKEN"]


def test_overlay_with_real_root_no_false_positive(tmp_path, monkeypatch):
    """validate trên overlay TEMP (không có exam/) + real_vault_root=vault thật → KHÔNG báo giả."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _build_vault_with_exam(tmp_path)
    overlay = _simulate_overlay(v)
    try:
        assert _exam_codes_on_overlay(v, overlay) == []
    finally:
        shutil.rmtree(overlay, ignore_errors=True)


def test_overlay_still_detects_broken_ref(tmp_path, monkeypatch):
    """TEETH: nếu bài nộp bị XOÁ khỏi exam/ thật, overlay-validate (real_vault_root=vault thật) VẪN
    phải bắt E-EXAM-REF-BROKEN — fix KHÔNG được làm mù detection."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _build_vault_with_exam(tmp_path)
    (tmp_path / "exam" / "docker" / "sol.py").unlink()  # bài nộp THẬT biến mất → ref hỏng thật
    overlay = _simulate_overlay(v)
    try:
        assert "E-EXAM-REF-BROKEN" in _exam_codes_on_overlay(v, overlay)
    finally:
        shutil.rmtree(overlay, ignore_errors=True)


def test_standalone_unchanged_valid(tmp_path, monkeypatch):
    """Standalone (real_vault_root=None mặc định) trên vault thật vẫn PASS (không đổi hành vi cũ)."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _build_vault_with_exam(tmp_path)
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, v, rep, now=AT)  # KHÔNG truyền real_vault_root
    assert [e["error_code"] for e in rep.errors] == []
