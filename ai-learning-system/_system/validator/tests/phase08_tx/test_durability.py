"""P08 durability — staged/committed data bền vững ngang manifest (spec 10.3).

GIỚI HẠN TRUNG THỰC: test này kiểm CONTRACT (os.fsync được gọi đúng chỗ), KHÔNG mô phỏng
mất điện thật (không thể trong unit test). Nó chứng minh dữ liệu commit đi qua flush+fsync
như manifest, bịt lỗ 'rename mà chưa fsync data'.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import transaction as TX  # noqa: E402
import vault_io as VIO    # noqa: E402


# ---- 1. helper _write_bytes_durable: đúng 1 fsync + nội dung đúng ------
def test_write_bytes_durable_fsyncs_once(tmp_path, monkeypatch):
    calls = []
    real = os.fsync
    monkeypatch.setattr(os, "fsync", lambda fd: (calls.append(fd), real(fd))[1])
    p = tmp_path / "x.bin"
    TX._write_bytes_durable(p, b"hello-\xe2\x9c\x93")
    assert p.read_bytes() == b"hello-\xe2\x9c\x93"
    assert len(calls) == 1  # đúng 1 fsync cho file staged


# ---- 2. stage() dùng đường ghi bền vững cho MỖI staged file -----------
def test_stage_fsyncs_each_staged_file(tmp_path, monkeypatch):
    # đếm fsync xảy ra trong lúc stage(); baseline begin() không fsync data file.
    (tmp_path / "a.txt").write_text("A0", encoding="utf-8")
    (tmp_path / "b.txt").write_text("B0", encoding="utf-8")
    ha = VIO.content_hash(tmp_path / "a.txt")
    hb = VIO.content_hash(tmp_path / "b.txt")

    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"A1", expected_read_hash=ha),
              TX.Write("b.txt", b"B1", expected_read_hash=hb)])

    # đo riêng giai đoạn stage: đếm fsync trên đúng 2 staged path
    fsynced_sizes = []
    real = os.fsync

    def spy(fd):
        try:
            fsynced_sizes.append(os.fstat(fd).st_size)
        except OSError:
            pass
        return real(fd)

    monkeypatch.setattr(os, "fsync", spy)
    tx.stage()
    # 2 staged file (2 byte mỗi cái) phải được fsync; manifest save cũng fsync (kích thước khác)
    assert fsynced_sizes.count(2) >= 2, fsynced_sizes


# ---- 3. commit vẫn đúng chức năng sau khi thêm fsync (không hồi quy) ---
def test_commit_still_correct_with_durability(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    (tmp_path / "a.txt").write_text("old", encoding="utf-8")
    h = VIO.content_hash(tmp_path / "a.txt")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"new", expected_read_hash=h)])
    tx.stage()
    tx.occ_recheck()
    tx.commit()
    assert (tmp_path / "a.txt").read_bytes() == b"new"
    assert not (tmp_path / TX.TX_DIRNAME / tx.tx_id).exists()  # cleanup xong
