"""P07a — CR-0004: `sources[].added <= today` (mở rộng nguyên tắc toàn-vẹn-thời-gian INV-05 sang nguồn).

RED-first. Song song _check_updated_not_future (DEC-029): phần THỜI GIAN ở validator (cần utc_offset +
mốc now cross-context), tái dùng _today_local. added=None → bỏ qua (Optional). added tương lai → E-SCHEMA.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V   # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
SRC_REL = Path("topics") / "docker" / "sources.md"


def _copy(tmp):
    dst = tmp / "lv"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _write_sources(vault: Path, added: str):
    (vault / SRC_REL).write_text(
        "---\n"
        "schema: sources\n"
        "schema_version: 1\n"
        "topic_id: docker\n"
        "sources:\n"
        "  - id: src-001\n"
        "    kind: doc\n"
        '    ref: "https://docs.docker.com/get-started/"\n'
        "    status: raw\n"
        "    trust: high\n"
        '    scope: "lesson 1"\n'
        f"    added: {added}\n"
        "    anchors: []\n"
        "---\n\n# Nguồn — docker\n",
        encoding="utf-8")


def _codes(vault, now=None):
    rep = V.Report()
    V.validate_full_core(SYSTEM, vault, rep, now=now)
    return rep.errors


NOW = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)  # local 2026-07-01 +07:00


def test_source_added_future_rejected(tmp_path):
    v = _copy(tmp_path)
    _write_sources(v, "2026-07-09")   # > today(now bơm 2026-07-01)
    errs = _codes(v, now=NOW)
    assert any(e["error_code"] == "E-SCHEMA" and "added" in e["message"].lower()
               for e in errs), f"added tương lai phải bị bắt (CR-0004): {errs}"


def test_source_added_future_default_now(tmp_path):
    v = _copy(tmp_path)
    _write_sources(v, "2099-01-01")   # tương lai so với MỌI now thật
    errs = _codes(v)                  # default now = now thật
    assert any(e["error_code"] == "E-SCHEMA" and "added" in e["message"].lower()
               for e in errs), f"added 2099 phải bị bắt: {errs}"


def test_source_added_today_ok(tmp_path):
    v = _copy(tmp_path)
    _write_sources(v, "2026-07-01")   # == today(now bơm)
    errs = _codes(v, now=NOW)
    assert not any("added" in e["message"].lower() for e in errs), f"added==today phải OK: {errs}"


def test_source_added_past_ok(tmp_path):
    v = _copy(tmp_path)
    _write_sources(v, "2026-06-30")   # < today
    errs = _codes(v, now=NOW)
    assert not any("added" in e["message"].lower() for e in errs), f"added quá khứ phải OK: {errs}"
