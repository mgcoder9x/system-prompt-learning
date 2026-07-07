"""P05 tests — IO/discovery/ignore (spec 19, INV-16/20)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import vault_io as VIO  # noqa: E402  (đặt tên vault_io để không đụng stdlib io)


def test_utf8_roundtrip(tmp_path):
    p = tmp_path / "vn.md"
    p.write_text("Định nghĩa: đóng gói phụ thuộc — má/mà/mả", encoding="utf-8")
    assert "đóng gói" in VIO.read_text(p)


def test_non_utf8_raises(tmp_path):
    p = tmp_path / "bad.md"
    p.write_bytes(b"\xff\xfe\x00 khong phai utf-8 hop le")  # byte không hợp lệ UTF-8
    with pytest.raises(VIO.EIoEncoding):
        VIO.read_text(p)


def test_read_text_strips_utf8_bom(tmp_path):
    # Editor Windows (Notepad/PowerShell Set-Content) hay thêm BOM UTF-8 (EF BB BF) đầu file.
    # read_text phải BỎ BOM → split_frontmatter (startswith '---') và _load_raw đọc NHẤT QUÁN.
    # Bug thật (pilot): BOM → validator báo 'thiếu front-matter' nhưng driver _load_raw lại đọc được → lệch.
    p = tmp_path / "bom.md"
    p.write_bytes(b"\xef\xbb\xbf" + "---\nschema: lesson_state\n---\n# Body\n".encode("utf-8"))
    text = VIO.read_text(p)
    assert text.startswith("---"), "read_text phải bỏ BOM đầu file (không để lọt \\ufeff)"
    fm, body = VIO.split_frontmatter(text)
    assert fm is not None and "schema: lesson_state" in fm


def test_read_text_bom_does_not_mask_real_bad_encoding(tmp_path):
    # utf-8-sig chỉ bỏ BOM đầu; byte UTF-8 THẬT hỏng vẫn phải raise (giữ DEC-034).
    p = tmp_path / "bad2.md"
    p.write_bytes(b"\xef\xbb\xbf---\n" + b"\xff\xfe bad \x81")
    with pytest.raises(VIO.EIoEncoding):
        VIO.read_text(p)


def test_split_frontmatter_keeps_body_dashes(tmp_path):
    text = "---\nschema: lesson_state\n---\n# Body\n\n---\n\nthematic break vẫn còn\n"
    fm, body = VIO.split_frontmatter(text)
    assert "schema: lesson_state" in fm
    assert "thematic break vẫn còn" in body and "---" in body  # không cắt sai dấu --- trong body


def test_split_frontmatter_none_when_no_fm():
    fm, body = VIO.split_frontmatter("# No frontmatter\n")
    assert fm is None


def test_discover_ignores_scratch_tx_and_conflict(tmp_path):
    (tmp_path / "topics" / "docker").mkdir(parents=True)
    (tmp_path / "topics" / "docker" / "topic.md").write_text("x", encoding="utf-8")
    (tmp_path / "topics" / "copywriting").mkdir()
    (tmp_path / "topics" / "copywriting" / "topic.md").write_text("x", encoding="utf-8")  # 'copy' KHÔNG bị bỏ
    (tmp_path / "_scratch").mkdir()
    (tmp_path / "_scratch" / "review-2026-06-30.md").write_text("x", encoding="utf-8")
    (tmp_path / ".tx").mkdir()
    (tmp_path / ".tx" / "m.md").write_text("x", encoding="utf-8")
    (tmp_path / "topics" / "docker" / "topic (Toan's conflicted copy 2026-06-30).md").write_text("x", encoding="utf-8")

    files, warns = VIO.discover_md(tmp_path)
    names = {f.name for f in files}
    assert "topic.md" in names
    rels = {str(f.relative_to(tmp_path)).replace("\\", "/") for f in files}
    assert "topics/copywriting/topic.md" in rels          # giữ 'copywriting'
    assert not any("_scratch" in r for r in rels)          # bỏ _scratch
    assert not any(".tx" in r for r in rels)               # bỏ .tx
    assert any("W-IGNORED-CLOUD-CONFLICT" in w for w in warns)  # cloud conflict có warning
    assert not any("conflicted copy" in r for r in rels)


def test_scan_abspath():
    assert VIO.scan_abspath("đường dẫn d:\\OneDrive\\vault")
    assert VIO.scan_abspath("/Users/toan/x")
    assert not VIO.scan_abspath("topics/docker/lesson-001")
