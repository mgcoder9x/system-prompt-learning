"""P11 — Migration EXECUTOR (spec 10.7 / 10.3b, INV-19).

Chạy KẾ HOẠCH di trú (từ planner.plan_migrations) trong transaction-FULL, validate-at-target, rollback
nguyên vẹn nếu FAIL. Bám đúng HỢP ĐỒNG một bước ở migrations/README.md:
  1. Mỗi bước = file `vN_to_vN+1.py` expose `migrate(vault) -> list[transaction.Write]` (biến đổi +
     bump schema_version tới N+1). KHÔNG sửa file thật trực tiếp — mọi thay đổi qua Write (staging).
  2. Chạy trong transaction-FULL: begin(backup) → stage → VALIDATE ở version ĐÍCH → occ_recheck → commit.
     Validate FAIL → abort → vault GIỮ version N (rollback nguyên vẹn).
  3. Chuỗi nhiều bước: chạy tuần tự; DỪNG ở bước đầu FAIL (vault ở version của bước trước — all-or-nothing
     mỗi bước, không partial trong một bước nhờ transaction).

Ranh giới trung thực (DEC-011 vẫn đúng): TRANSFORM v2 THẬT + validator-cho-version-đích THẬT chưa có
(hệ mới ở VERSION=1). `validate_staged_fn` là SEAM để bơm validate-at-target — mặc định dùng
transaction.validate_staged (validator hiện hành). Cơ chế ORCHESTRATION (atomic migrate-or-rollback) là
phần được dựng + kiểm ở đây; transform/schema v2 thật để dành tới khi có version mới (qua change request).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import transaction as TX


def _load_step(migrations_dir, frm: int, to: int):
    """Load module `vN_to_vM.py` → hàm migrate(vault) -> list[TX.Write]. Raise nếu thiếu/không đúng API."""
    path = Path(migrations_dir) / f"v{frm}_to_v{to}.py"
    if not path.is_file():
        raise FileNotFoundError(f"thiếu bước migration: {path}")
    spec = importlib.util.spec_from_file_location(f"mig_v{frm}_to_v{to}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "migrate"):
        raise AttributeError(f"{path.name} thiếu hàm migrate(vault) -> list[Write]")
    return mod.migrate


def execute_step(vault, system, frm: int, to: int, migrate_fn, now=None, validate_staged_fn=None):
    """Chạy MỘT bước v{frm}→v{to} trong transaction-FULL. Trả (committed: bool, report).

    validate_staged_fn(tx) -> Report: validate overlay ở version ĐÍCH. None → dùng tx.validate_staged
    (validator hiện hành). FAIL → abort (vault giữ version frm). PASS → occ_recheck → commit.
    """
    vault, system = Path(vault), Path(system)
    writes = migrate_fn(vault)  # list[TX.Write]: biến đổi + bump schema_version → to
    tx = TX.Transaction(vault, level="full", now=now)
    tx.begin(writes)
    tx.stage()
    rep = validate_staged_fn(tx) if validate_staged_fn is not None else tx.validate_staged(system)
    if not rep.ok():
        tx.abort()                      # spec 6b: FAIL trước 'committing' → file thật chưa đụng; giữ .tx truy vết
        return False, rep
    tx.occ_recheck()                    # OCC mốc 2 (begin→commit) — nếu lệch sẽ TxError E-CONCURRENT-EDIT
    tx.commit()                         # roll-forward: os.replace staged→target + materialize log + cleanup
    return True, rep


def run_plan(vault, system, plan, migrations_dir, now=None, validate_staged_fn=None) -> list[dict]:
    """Chạy chuỗi bước theo plan (từ planner). DỪNG ở bước đầu FAIL (vault ở version bước trước).
    Trả list kết quả mỗi bước: {step, committed, errors}."""
    results = []
    for (frm, to) in plan:
        migrate_fn = _load_step(migrations_dir, frm, to)
        committed, rep = execute_step(vault, system, frm, to, migrate_fn, now, validate_staged_fn)
        results.append({"step": (frm, to), "committed": committed, "errors": rep.errors})
        if not committed:
            break  # không chạy tiếp bước sau khi 1 bước FAIL (an toàn: không migrate nửa chừng)
    return results
