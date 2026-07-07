"""P12 — Nghiệm thu TẤT ĐỊNH (Definition of Done, phần auto-test được).

Verify 3 cam kết cốt lõi §0/§1 (chưa test trực tiếp E2E trước đây):
  1. Determinism: validate 2 lần → report GIỐNG HỆT (cả nhánh PASS lẫn FAIL).
  2. Chống giả mạo FSRS: sửa tay due_date / last_reviewed_at_utc của review item đã ôn → E-REVIEW-MISCALC
     (Class A 'đúng tuyệt đối' — KHÔNG thể bịa trạng thái ôn). Grounded: cards_equal so due_date +
     last_reviewed_at_utc exact (đã đọc fsrs_adapter).
  3. Portability: copy vault sang path tuyệt đối khác → validate vẫn PASS (INV-16, không path theo-máy).

KHÔNG bao gồm phần AI-dạy-thật + cross-AI handoff (không auto-test được — nghiệm thu bán-thủ-công riêng).
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)  # > created demo (2026-06-30)
LS_REL = "topics/docker/lessons/lesson-001/lesson_state.md"


def _vault(tmp_path, name="vault") -> Path:
    v = tmp_path / name
    shutil.copytree(REAL_VAULT, v)
    return v


def _report_json(vault: Path) -> str:
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return json.dumps({"errors": rep.errors, "warnings": rep.warnings},
                      ensure_ascii=False, sort_keys=True)


def _codes(vault: Path) -> list[str]:
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return [e["error_code"] for e in rep.errors]


def _reviewed_vault(tmp_path) -> Path:
    """Vault sau khi ôn rv-001 (item có card/log/stability thật để test tamper)."""
    v = _vault(tmp_path)
    committed, rep = S.cmd_review(v, ROOT, "docker/lesson-001", "rv-001", 2, AT)
    assert committed, rep.errors
    return v


# ---- 1. DETERMINISM ----
def test_determinism_clean_vault(tmp_path):
    v = _vault(tmp_path)
    assert _report_json(v) == _report_json(v), "validate 2 lần trên vault sạch phải giống hệt"


def test_determinism_error_report(tmp_path):
    # vault có lỗi (tamper) → 2 lần validate phải cho CÙNG danh sách lỗi (báo lỗi tất định)
    v = _reviewed_vault(tmp_path)
    raw, body = S._load_raw(v / LS_REL)
    raw["review_items"][0]["card"]["last_reviewed_at_utc"] = "2020-01-01T00:00:00Z"
    (v / LS_REL).write_bytes(S._dump_state(raw, body))
    assert _report_json(v) == _report_json(v), "báo lỗi phải tất định giữa 2 lần chạy"


# ---- 2. CHỐNG GIẢ MẠO FSRS (Class A đúng tuyệt đối) ----
def test_tamper_last_reviewed_detected(tmp_path):
    v = _reviewed_vault(tmp_path)
    raw, body = S._load_raw(v / LS_REL)
    raw["review_items"][0]["card"]["last_reviewed_at_utc"] = "2020-01-01T00:00:00Z"  # sai
    (v / LS_REL).write_bytes(S._dump_state(raw, body))
    codes = _codes(v)
    assert "E-REVIEW-MISCALC" in codes, f"sửa last_reviewed_at_utc phải bị bắt; codes={codes}"
    # cô lập: last_reviewed_at_utc không vào view/derive_mastery → không kích E-VIEW/E-STATE-DERIVED
    assert "E-VIEW-MISMATCH" not in codes and "E-STATE-DERIVED" not in codes


def test_tamper_due_date_detected(tmp_path):
    v = _reviewed_vault(tmp_path)
    raw, body = S._load_raw(v / LS_REL)
    from datetime import date
    raw["review_items"][0]["card"]["due_date"] = date(2099, 12, 31)  # sai hẳn
    (v / LS_REL).write_bytes(S._dump_state(raw, body))
    assert "E-REVIEW-MISCALC" in _codes(v), "sửa due_date phải bị bắt E-REVIEW-MISCALC (spec DoD)"


# ---- 3. PORTABILITY (INV-16) ----
def test_portability_across_paths(tmp_path):
    a = _vault(tmp_path, "machineA")
    b = tmp_path / "deeply" / "nested" / "elsewhere" / "machineB"
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REAL_VAULT, b)
    assert _codes(a) == [], "vault ở path A phải PASS"
    assert _codes(b) == [], "vault copy sang path khác (sâu hơn) phải PASS — portable (INV-16)"
