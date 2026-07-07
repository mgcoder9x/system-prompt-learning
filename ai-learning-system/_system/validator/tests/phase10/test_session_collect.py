"""P10 driver — cmd_collect (CR-0008): ghi lát cắt tài liệu tham chiếu vào topics/<topic>/reference/<slug>.md.

Transaction-LIGHT (ghi-trong-phiên, spec 10.8). Đầu vào của việc dựng giáo trình (Reference_Store).
Backend ghi tất định; AI (chat) lo lấy nội dung (như cmd_learn/cmd_source). RED-first: cmd_collect chưa có.
Ranh giới an toàn: slug là TÊN FILE .md (không path/traversal); topic phải tồn tại; nội dung không rỗng;
abspath trong nội dung bị LIGHT validate chặn (INV-16).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _full_errors(vault: Path):
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return rep.errors


def test_collect_creates_reference_md(tmp_path):
    v = _fresh(tmp_path)
    committed, rep, ref = S.cmd_collect(v, ROOT, "docker", "roadmap", "# Lát cắt roadmap Docker\n", AT)
    assert committed, rep.errors
    assert ref == "reference/roadmap.md"
    p = v / "topics" / "docker" / "reference" / "roadmap.md"
    assert p.is_file() and "roadmap" in p.read_text(encoding="utf-8").lower()
    assert _full_errors(v) == [], "vault phải vẫn PASS full sau collect"


def test_collect_adds_md_extension(tmp_path):
    v = _fresh(tmp_path)
    _, _, ref = S.cmd_collect(v, ROOT, "docker", "note", "nội dung tham chiếu", AT)
    assert ref == "reference/note.md"
    assert (v / "topics" / "docker" / "reference" / "note.md").is_file()


def test_collect_bad_slug_rejected(tmp_path):
    v = _fresh(tmp_path)
    for bad in ("a/b", "..\\x", "../x", ""):
        with pytest.raises(S.SessionError):
            S.cmd_collect(v, ROOT, "docker", bad, "x", AT)


def test_collect_topic_not_exist(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_collect(v, ROOT, "khong-co", "x", "y", AT)


def test_collect_empty_content_rejected(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_collect(v, ROOT, "docker", "x", "   ", AT)


def test_collect_in_cli_commands(tmp_path):
    assert "collect" in S.CLI_COMMANDS and hasattr(S, "cmd_collect")
