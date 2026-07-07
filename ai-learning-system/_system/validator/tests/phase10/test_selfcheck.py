"""P10-agent — selfcheck.py (first-run self-check) đúng: dương trên repo thật, âm khi thiếu file.

selfcheck là công cụ 'chạy-lần-đầu-sau-copy' (stdlib-only, không cần venv). Test khoá: (1) repo thật →
ok=True + báo 'NGUYÊN VẸN'; (2) thư mục rỗng → ok=False + liệt kê THIẾU (có răng); (3) mọi path trong
REQUIRED trỏ file thật tồn tại (chống drift danh sách so với cấu trúc thực).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../_system
AI_ROOT = ROOT.parent                          # .../ai-learning-system
sys.path.insert(0, str(ROOT))                  # để import selfcheck (ở _system/)

import selfcheck as SC  # noqa: E402


def test_selfcheck_ok_on_real_repo():
    ok, lines = SC.check(AI_ROOT)
    assert ok is True, [l for l in lines if "THIẾU" in l]
    assert any("NGUYÊN VẸN" in l for l in lines)


def test_selfcheck_fails_on_empty_dir(tmp_path):
    ok, lines = SC.check(tmp_path)          # thư mục trống → thiếu mọi file cốt lõi
    assert ok is False
    assert any("KHÔNG đủ" in l for l in lines)
    assert any(l.startswith("[THIẾU]") for l in lines)


def test_required_paths_exist():
    # danh sách REQUIRED phải khớp cấu trúc THỰC (không trỏ file đã đổi tên/di chuyển)
    missing = [r for r in SC.REQUIRED if not (AI_ROOT / r).is_file()]
    missing += [d for d in SC.REQUIRED_DIRS if not (AI_ROOT / d).is_dir()]
    assert not missing, f"REQUIRED trỏ path không tồn tại: {missing}"
