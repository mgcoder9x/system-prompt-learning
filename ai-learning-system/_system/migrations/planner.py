"""P11 — Migration planner (spec 10.7, INV-19).

Lõi TẤT ĐỊNH, THUẦN (không I/O ngoài discover, không đụng dữ liệu): tính đường di trú giữa
schema_version của vault và _system/VERSION, dựa trên tập bước vN_to_vN+1 có sẵn.

Đây KHÔNG thay thế validator: validator vẫn phát E-SCHEMA-OUTDATED/AHEAD (INV-19). Planner chỉ trả
lời câu 'có migrate được không, theo trình tự nào'. Việc THỰC THI một bước phải chạy trong
transaction-FULL (validate ở version ĐÍCH, rollback nếu FAIL) — xem README.md; chưa có bước thật nào
vì hệ thống mới ở VERSION=1 (không bịa bước v1→v2 khi chưa có schema v2).
"""
from __future__ import annotations

import re
from pathlib import Path

_STEP_RE = re.compile(r"^v(\d+)_to_v(\d+)\.py$")


def discover_steps(migrations_dir) -> set[tuple[int, int]]:
    """Quét file tên `vN_to_vM.py` với M == N+1 → set[(N, M)]. Bỏ file sai mẫu hoặc M != N+1."""
    steps: set[tuple[int, int]] = set()
    d = Path(migrations_dir)
    if not d.is_dir():
        return steps
    for p in d.iterdir():
        if not p.is_file():
            continue
        m = _STEP_RE.match(p.name)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if b == a + 1:
                steps.add((a, b))
    return steps


def plan_migrations(vault_version: int, system_version: int,
                    available_steps: set[tuple[int, int]]) -> dict:
    """Tính kế hoạch di trú (tất định).

    Trả dict: {status, plan, reason}.
      status = up_to_date  : vault == system → không cần migrate.
      status = ahead       : vault > system  → chặn (ứng E-SCHEMA-AHEAD).
      status = migratable  : vault < system và có đủ chuỗi bước liên tiếp → plan = [(v, v+1), ...].
      status = no_path     : vault < system nhưng thiếu >=1 bước → không migrate được (ứng E-SCHEMA-OUTDATED).
    """
    if vault_version == system_version:
        return {"status": "up_to_date", "plan": [], "reason": ""}
    if vault_version > system_version:
        return {"status": "ahead", "plan": [],
                "reason": f"vault {vault_version} > system {system_version} — vault mới hơn hệ thống (E-SCHEMA-AHEAD)"}
    chain = [(v, v + 1) for v in range(vault_version, system_version)]
    missing = [s for s in chain if s not in available_steps]
    if missing:
        return {"status": "no_path", "plan": [],
                "reason": f"vault {vault_version} < system {system_version} nhưng thiếu bước migration {missing} (E-SCHEMA-OUTDATED)"}
    return {"status": "migratable", "plan": chain, "reason": ""}
