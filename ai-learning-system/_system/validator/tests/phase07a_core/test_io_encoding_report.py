"""P07a — E-IO-ENCODING: file non-UTF-8 trong vault → validator BÁO LỖI sạch, KHÔNG crash.

Spec §10.4 (bảng mã lỗi có E-IO-ENCODING) + §19 dòng 'Decode fail → E-IO-ENCODING'. read_text (P05)
raise EIoEncoding đúng, NHƯNG trước fix KHÔNG nơi nào ở validator catch → non-UTF-8 làm validator CRASH
(uncaught) thay vì trả report {pass:false, E-IO-ENCODING}. Đây là robustness gap: user lưu file cp1252/
latin-1 → phải nhận FAIL sạch, không phải traceback. Test: validator entry KHÔNG được raise; phải emit mã.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)
BAD_BYTES = b"\xff\xfe khong phai utf-8 hop le \x00\x81"  # 0x81 không hợp lệ UTF-8


def _copy(tmp):
    v = tmp / "lv"
    shutil.copytree(REAL_VAULT, v)
    return v


def _core_codes(vault):
    rep = V.Report()
    V.validate_full_core(ROOT, vault, rep, now=NOW)   # KHÔNG được raise
    return [e["error_code"] for e in rep.errors]


def _light_codes(vault):
    rep = V.Report()
    V.validate_light(vault, None, rep)                # KHÔNG được raise
    return [e["error_code"] for e in rep.errors]


def _semantic_codes(vault):
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=NOW)  # KHÔNG được raise
    return [e["error_code"] for e in rep.errors]


def test_core_reports_io_encoding_on_bad_lesson_md(tmp_path):
    v = _copy(tmp_path)
    (v / "topics/docker/lessons/lesson-001/lesson.md").write_bytes(BAD_BYTES)
    assert "E-IO-ENCODING" in _core_codes(v)


def test_core_reports_io_encoding_on_bad_state_file(tmp_path):
    v = _copy(tmp_path)
    (v / "topics/docker/lessons/lesson-001/lesson_state.md").write_bytes(BAD_BYTES)
    assert "E-IO-ENCODING" in _core_codes(v)


def test_light_reports_io_encoding(tmp_path):
    v = _copy(tmp_path)
    (v / "topics/docker/lessons/lesson-001/lesson.md").write_bytes(BAD_BYTES)
    assert "E-IO-ENCODING" in _light_codes(v)


def test_semantic_reports_io_encoding(tmp_path):
    v = _copy(tmp_path)
    (v / "topics/docker/lessons/lesson-001/lesson.md").write_bytes(BAD_BYTES)
    assert "E-IO-ENCODING" in _semantic_codes(v)


def test_demo_vault_no_io_encoding(tmp_path):
    # vault demo là UTF-8 sạch → KHÔNG có E-IO-ENCODING (không false-positive)
    assert "E-IO-ENCODING" not in _core_codes(_copy(tmp_path))
