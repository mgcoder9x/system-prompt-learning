"""P05 (regression) — INV-16 scan_abspath: URL portable KHÔNG bị bắt; abspath theo-máy VẪN bị bắt.

Gốc lỗi (2026-07-03): ABSPATH_RE cũ `[A-Za-z]:/` khớp 's:/' trong 'https://' → báo oan E-PORT-ABSPATH
cho ref URL (spec 5.3 cho phép). Fix gốc: ổ đĩa = 1 chữ cái độc lập (negative lookbehind), không phải
chữ trong 1 từ. Test này khoá cả hai chiều để không tái phát.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import vault_io as VIO  # noqa: E402


# ---- URL / ref portable: KHÔNG được bắt (báo oan cũ) ----
def test_https_url_not_flagged():
    assert VIO.scan_abspath("https://docs.docker.com") is False
    assert VIO.scan_abspath("http://example.org/path") is False
    assert VIO.scan_abspath('ref: "https://github.com/open-spaced-repetition/py-fsrs"') is False


def test_git_and_scheme_refs_not_flagged():
    assert VIO.scan_abspath("git@github.com:org/repo.git") is False
    assert VIO.scan_abspath("ftp://host/file") is False


# ---- abspath theo-máy: VẪN phải bắt (INV-16 còn hiệu lực) ----
def test_windows_drive_still_flagged():
    assert VIO.scan_abspath(r"C:\Users\toann\file") is True
    assert VIO.scan_abspath("D:/data/x") is True
    assert VIO.scan_abspath("mở file tại E:\\proj") is True  # sau khoảng trắng vẫn bắt


def test_unix_home_still_flagged():
    assert VIO.scan_abspath("/home/user/file") is True
    assert VIO.scan_abspath("/Users/toann/file") is True
