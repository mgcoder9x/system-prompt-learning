"""P08 — dọn thư mục rỗng sau xoá file (enabler cho /forget).

Xoá file lesson để lại dir rỗng → validator bắt E-INDEX-MISMATCH. Transaction phải prune dir rỗng
nhất quán ở overlay + commit + recovery. Chỉ rmdir dir RỖNG (không mất dữ liệu).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import transaction as TX  # noqa: E402
import vault_io as VIO    # noqa: E402


def _mk(tmp, rel, content="x"):
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---- 1. helper: dọn dir rỗng đi lên, dừng ở root ---------------------
def test_prune_helper(tmp_path):
    f = _mk(tmp_path, "a/b/c.txt")
    f.unlink()
    TX._prune_empty_dirs(f, tmp_path)
    assert not (tmp_path / "a").exists()   # a, b rỗng → dọn hết
    assert tmp_path.is_dir()               # dừng ở root


# ---- 2. helper: KHÔNG dọn dir còn file khác --------------------------
def test_prune_keeps_nonempty(tmp_path):
    f = _mk(tmp_path, "a/c.txt")
    _mk(tmp_path, "a/d.txt")
    f.unlink()
    TX._prune_empty_dirs(f, tmp_path)
    assert (tmp_path / "a").is_dir() and (tmp_path / "a" / "d.txt").exists()


# ---- 3. commit delete → file mất + dir rỗng bị dọn -------------------
def test_commit_delete_prunes(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    p = _mk(tmp_path, "topics/t/lessons/l1/lesson_state.md")
    _mk(tmp_path, "keep.txt")  # để root không rỗng
    h = VIO.content_hash(p)
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("topics/t/lessons/l1/lesson_state.md", None, expected_read_hash=h, op="delete")])
    tx.stage()
    # bỏ qua validate (test cơ chế); commit trực tiếp
    tx.occ_recheck()
    tx.commit()
    assert not (tmp_path / "topics" / "t").exists()  # cả chuỗi dir rỗng đã dọn
    assert (tmp_path / "keep.txt").exists()


# ---- 4. overlay: dir rỗng sau staged-delete KHÔNG lọt vào overlay ----
def test_overlay_omits_emptied_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    p = _mk(tmp_path, "topics/t/lessons/l1/lesson_state.md")
    _mk(tmp_path, "vault_state.md", "root")
    h = VIO.content_hash(p)
    tx = TX.Transaction(tmp_path, level="full")
    tx.begin([TX.Write("topics/t/lessons/l1/lesson_state.md", None, expected_read_hash=h, op="delete")])
    tx.stage()
    overlay = tx._build_overlay()
    try:
        assert not (overlay / "topics" / "t" / "lessons" / "l1").exists()  # dir rỗng đã prune
        assert (overlay / "vault_state.md").exists()                       # file khác vẫn còn
    finally:
        shutil.rmtree(overlay, ignore_errors=True)
        tx.abort()
