"""P07a — INV-05 phần TEMPORAL: `updated <= today` (spec dòng 666 `created <= updated <= today`,
dòng 559 'INV-05 dùng today = ngày lịch thật; KHÔNG áp day_cutoff'; §5.1 comment 'updated ... <= hôm nay').

Gap đã kiểm chứng (NOTE-009 / test_cli_loop_composition dòng 9): models.py CHỈ ép updated>=created,
KHÔNG ép updated<=today ⇒ state 'đến từ tương lai' lọt lưới. Fix GỐC: phần cấu trúc (created<=updated)
ở model (thuần); phần THỜI GIAN (updated<=today) ở validate.py (cần utc_offset + mốc now — cross-context).
today = now.astimezone(offset).date() — ngày lịch thật, KHÔNG day_cutoff (spec §8.5 tách bạch hai mốc).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V   # noqa: E402
import session         # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
LS = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"
TS = Path("topics") / "docker" / "topic_state.md"


def _copy(tmp):
    dst = tmp / "lv"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _set_updated(path: Path, value: str):
    from datetime import date
    raw, body = session._load_raw(path)
    raw["updated"] = date.fromisoformat(value)
    path.write_bytes(session._dump_state(raw, body))


def _codes(vault, now=None):
    rep = V.Report()
    V.validate_full_core(SYSTEM, vault, rep, now=now)
    return [e for e in rep.errors]


def test_future_updated_rejected_default_now(tmp_path):
    # updated 2099 là tương lai so với MỌI now thật → phải E-SCHEMA (INV-05 updated<=today).
    v = _copy(tmp_path)
    _set_updated(v / LS, "2099-01-01")
    errs = _codes(v)  # default now = now thật
    assert any(e["error_code"] == "E-SCHEMA" and "today" in e["message"].lower()
               for e in errs), f"phải bắt updated tương lai (INV-05), errors={errs}"


def test_updated_equals_today_ok_injected_now(tmp_path):
    # Tất định: updated == today(now bơm vào) → KHÔNG lỗi INV-05.
    v = _copy(tmp_path)
    now = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)  # local 2026-07-01 +07:00
    _set_updated(v / LS, "2026-07-01")
    errs = _codes(v, now=now)
    assert not any("today" in e["message"].lower() for e in errs), f"updated==today phải OK: {errs}"


def test_updated_future_relative_to_injected_now(tmp_path):
    # Tất định: updated 2026-07-05 > today(now=2026-07-01) → E-SCHEMA.
    v = _copy(tmp_path)
    now = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    _set_updated(v / LS, "2026-07-05")
    errs = _codes(v, now=now)
    assert any(e["error_code"] == "E-SCHEMA" and "today" in e["message"].lower()
               for e in errs), f"updated>today(now bơm) phải bị bắt: {errs}"


def test_topic_state_updated_future_rejected(tmp_path):
    # Áp cho CẢ topic_state (không chỉ lesson_state).
    v = _copy(tmp_path)
    now = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    _set_updated(v / TS, "2026-07-09")
    errs = _codes(v, now=now)
    assert any(e["error_code"] == "E-SCHEMA" and "today" in e["message"].lower()
               for e in errs), f"topic_state.updated tương lai phải bị bắt: {errs}"


def test_demo_vault_passes_with_injected_now(tmp_path):
    # Không hồi quy: demo (updated 2026-06-30) vẫn PASS với now hợp lý.
    v = _copy(tmp_path)
    now = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
    errs = _codes(v, now=now)
    assert not any("today" in e["message"].lower() for e in errs), f"demo phải sạch INV-05-today: {errs}"
