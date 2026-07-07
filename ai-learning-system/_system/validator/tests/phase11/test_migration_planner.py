"""P11 — migration planner (spec 10.7/INV-19): lõi tất định tính đường di trú.

Kiểm bằng fixture (không cần schema v2 thật). Đối chiếu semantics với INV-19 của validator:
ahead ↔ E-SCHEMA-AHEAD; vault<system ↔ E-SCHEMA-OUTDATED (migratable hay no_path là chi tiết remedy).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "migrations"))
sys.path.insert(0, str(ROOT / "validator"))

import planner as P   # noqa: E402
import validate as V  # noqa: E402


# ---- plan_migrations: 4 trạng thái ----------------------------------
def test_up_to_date():
    r = P.plan_migrations(1, 1, set())
    assert r["status"] == "up_to_date" and r["plan"] == []


def test_ahead():
    r = P.plan_migrations(3, 2, {(1, 2)})
    assert r["status"] == "ahead" and r["plan"] == []


def test_migratable_single_step():
    r = P.plan_migrations(1, 2, {(1, 2)})
    assert r["status"] == "migratable" and r["plan"] == [(1, 2)]


def test_migratable_chain():
    r = P.plan_migrations(1, 3, {(1, 2), (2, 3)})
    assert r["status"] == "migratable" and r["plan"] == [(1, 2), (2, 3)]


def test_no_path_gap_in_chain():
    r = P.plan_migrations(1, 3, {(1, 2)})  # thiếu (2,3)
    assert r["status"] == "no_path" and r["plan"] == []


def test_no_path_no_steps():
    r = P.plan_migrations(1, 2, set())
    assert r["status"] == "no_path"


def test_no_path_reason_lists_missing():
    r = P.plan_migrations(1, 3, {(1, 2)})
    assert "(2, 3)" in r["reason"]


# ---- discover_steps: parse tên file ---------------------------------
def test_discover_parses_consecutive_only(tmp_path):
    for name in ("v1_to_v2.py", "v2_to_v3.py", "v1_to_v3.py", "readme.txt", "v2_to_v2.py"):
        (tmp_path / name).write_text("", encoding="utf-8")
    steps = P.discover_steps(tmp_path)
    assert steps == {(1, 2), (2, 3)}  # v1_to_v3 (nhảy) và v2_to_v2 (không tiến) bị loại


def test_discover_empty_when_no_dir(tmp_path):
    assert P.discover_steps(tmp_path / "khong_ton_tai") == set()


def test_real_migrations_dir_has_no_step_yet():
    # Thực tế: VERSION=1, chưa có bước migration thật (không bịa v1→v2)
    assert P.discover_steps(ROOT / "migrations") == set()


# ---- planner nhất quán với version thật của hệ thống ----------------
def test_planner_up_to_date_with_real_system_version():
    sysver = V._read_system_version(ROOT)  # =1
    steps = P.discover_steps(ROOT / "migrations")
    r = P.plan_migrations(sysver, sysver, steps)
    assert r["status"] == "up_to_date"
