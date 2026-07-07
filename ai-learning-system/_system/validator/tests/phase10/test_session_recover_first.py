"""P10 tests — RECOVER-FIRST trong session driver (spec 10.3 'bắt buộc').

Trước MỌI ghi mới, /review và /done phải hoàn tất transaction dở (roll-forward) hoặc
chặn bằng E-TX-PARTIAL. Test bằng fault-injection: tạo tx 'interrupted' thật rồi kiểm hành vi.
"""
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session          # noqa: E402
import transaction as TX  # noqa: E402
import vault_io as VIO    # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
REVIEWED_AT = datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc)

LS_REL = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"
NOTE_REL = "notes.md"  # file trung tính: validate_full_core bỏ qua (không schema)


def _copy_vault(tmp_path) -> Path:
    dst = tmp_path / "learning_vault"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _make_interrupted_tx(vault: Path, target_rel: str, old: bytes, new: bytes) -> str:
    """Dựng một transaction ở trạng thái 'interrupted' THẬT: begin+stage xong, ép replace
    file đích thất bại (giữ manifest replace thành công) → commit dở → state=interrupted, .tx còn."""
    (vault / target_rel).write_bytes(old)
    h = VIO.content_hash(vault / target_rel)
    tx = TX.Transaction(vault, level="full")
    tx.begin([TX.Write(target_rel, new, expected_read_hash=h)])
    tx.stage()

    real_replace = os.replace

    def selective(src, dst):
        # chỉ ném lỗi khi replace ĐÚNG file đích (notes.md); manifest.json vẫn ghi được
        if str(dst).replace("\\", "/").endswith(target_rel):
            raise PermissionError("simulated cloud-lock")
        return real_replace(src, dst)

    orig = TX._os_replace
    orig_sleep = TX._sleep
    TX._os_replace = selective
    TX._sleep = lambda s: None
    try:
        with pytest.raises(TX.TxError) as ei:
            tx.commit()
        assert ei.value.code == "E-TX-PARTIAL"
    finally:
        TX._os_replace = orig
        TX._sleep = orig_sleep

    # xác nhận đúng tiền đề: file đích CHƯA đổi, .tx còn ở trạng thái interrupted
    assert (vault / target_rel).read_bytes() == old
    m = TX._read_manifest(vault / TX.TX_DIRNAME / tx.tx_id / "manifest.json")
    assert m["state"] == "interrupted"
    return tx.tx_id


# ---- A. recover-first hoàn tất tx dở TRƯỚC khi /review chạy ------------
def test_recover_first_finalizes_interrupted_then_review(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    tx_id = _make_interrupted_tx(vault, NOTE_REL, b"old\n", b"recovered\n")

    committed, rep = session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                                        grade=2, reviewed_at=REVIEWED_AT)
    assert committed is True, rep.errors
    # tx dở đã được roll-forward: notes.md mang nội dung staged; .tx cũ đã dọn
    assert (vault / NOTE_REL).read_bytes() == b"recovered\n"
    assert not (vault / TX.TX_DIRNAME / tx_id).exists()
    # /review vẫn commit đúng
    ls, _ = session._load_raw(vault / LS_REL)
    assert len(ls["review_items"][0]["log"]) == 1


# ---- B. partial không cứu được → chặn ghi mới (E-TX-PARTIAL) -----------
def test_recover_first_blocks_write_on_unrecoverable(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    _make_interrupted_tx(vault, NOTE_REL, b"old\n", b"recovered\n")
    before_ls = (vault / LS_REL).read_bytes()

    # phá vỡ khả năng roll-forward: đổi file đích sang nội dung THỨ BA (hash lạ)
    (vault / NOTE_REL).write_bytes(b"THIRD-hand-edit\n")

    with pytest.raises(TX.TxError) as ei:
        session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                           grade=2, reviewed_at=REVIEWED_AT)
    assert ei.value.code == "E-TX-PARTIAL"
    # ghi mới BỊ CHẶN: lesson_state không đổi
    assert (vault / LS_REL).read_bytes() == before_ls


# ---- C. vault sạch → recover-first là no-op ----------------------------
def test_recover_first_noop_on_clean_vault(tmp_path):
    vault = _copy_vault(tmp_path)
    assert session._recover_first(vault) == []


# ---- D. /done cũng RECOVER-FIRST --------------------------------------
def test_done_also_recovers_first(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    tx_id = _make_interrupted_tx(vault, NOTE_REL, b"old\n", b"recovered\n")

    committed, rep = session.cmd_done(vault, SYSTEM, "docker/lesson-001",
                                      done_at=datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc))
    assert committed is True, rep.errors
    assert (vault / NOTE_REL).read_bytes() == b"recovered\n"
    assert not (vault / TX.TX_DIRNAME / tx_id).exists()
