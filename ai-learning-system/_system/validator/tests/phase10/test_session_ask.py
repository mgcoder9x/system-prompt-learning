"""P10 driver — cmd_ask: ghi câu hỏi phụ vào lesson.md ## Hỏi phụ (spec 14A/11), transaction-LIGHT."""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)
LESSON = "docker/lesson-001"
LP = "topics/docker/lessons/lesson-001/lesson.md"


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def test_ask_appends_bullet_under_hoiphu(tmp_path):
    v = _fresh(tmp_path)
    q = "Container khác chroot ở điểm nào?"
    committed, rep = S.cmd_ask(v, ROOT, LESSON, q, AT)
    assert committed, rep.errors
    body = (v / LP).read_text(encoding="utf-8")
    assert "## Hỏi phụ" in body
    # bullet mới nằm NGAY dưới heading, có ngày + nội dung câu hỏi
    lines = body.split("\n")
    hi = next(i for i, l in enumerate(lines) if l.strip() == "## Hỏi phụ")
    assert lines[hi + 1] == f"- [2026-07-02] {q}"
    # heading bắt buộc vẫn còn (không phá cấu trúc)
    assert "## Mục tiêu" in body and "## Sessions" in body


def test_ask_creates_section_if_absent(tmp_path):
    v = _fresh(tmp_path)
    lp = v / LP
    txt = lp.read_text(encoding="utf-8")
    # cắt bỏ section Hỏi phụ (giả lập lesson chưa có)
    txt = txt.split("## Hỏi phụ")[0].rstrip() + "\n"
    lp.write_text(txt, encoding="utf-8")
    committed, rep = S.cmd_ask(v, ROOT, LESSON, "Câu hỏi mới?", AT)
    assert committed, rep.errors
    body = lp.read_text(encoding="utf-8")
    assert "## Hỏi phụ" in body and "Câu hỏi mới?" in body


def test_ask_light_gate_blocks_abspath(tmp_path):
    v = _fresh(tmp_path)
    # câu hỏi chứa đường dẫn tuyệt đối theo-máy → LIGHT bắt E-PORT-ABSPATH → KHÔNG commit
    committed, rep = S.cmd_ask(v, ROOT, LESSON, r"Vì sao file ở C:\Users\me\x lỗi?", AT)
    assert not committed
    assert any(e["error_code"] == "E-PORT-ABSPATH" for e in rep.errors)


def test_ask_unknown_lesson_raises(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_ask(v, ROOT, "docker/lesson-999", "q?", AT)


def test_ask_in_cli_commands():
    assert "ask" in S.CLI_COMMANDS and hasattr(S, "cmd_ask")
