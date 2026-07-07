# migrations/ — Di trú schema vN → vN+1 (spec 10.7, 10.3b, INV-19)

Trạng thái hiện tại: **`_system/VERSION = 1`, chưa có bước migration thật nào** (chưa có schema v2 để
migrate). Ở đây mới có `planner.py` — lõi tất định tính *đường di trú* (kiểm chứng bằng fixture). Không
dựng bước `v1_to_v2` giả khi chưa có thay đổi schema thật (tránh bịa).

## Hợp đồng một bước migration (khi có schema mới)

Mỗi bước là một file `vN_to_vN+1.py` trong thư mục này. Quy tắc **cứng** (spec 10.7/10.3b):

1. Chạy **trong transaction-FULL** (spec 10.3): BEGIN backup toàn vault → STAGE biến đổi → REGEN view.
2. **VALIDATE bằng schema version ĐÍCH** (N+1). PASS → commit + tăng `schema_version` (và `_system/VERSION`
   nếu là mốc hệ thống). FAIL → **abort, vault giữ nguyên version N** (rollback nguyên vẹn).
3. **KHÔNG** sửa file thật trực tiếp; mọi thay đổi qua staging của transaction (spec 10.3b).
4. Đi qua change request (spec 12): bump version schema là `system_change`, ghi `changelog.md`.

Tên file khớp mẫu `^v(\d+)_to_v(\d+)\.py$` với `to == from + 1`. Planner chỉ nhận bước liên tiếp.

## `planner.py` — API

- `discover_steps(migrations_dir) -> set[(N, M)]`: quét file đúng mẫu (M==N+1).
- `plan_migrations(vault_version, system_version, available_steps) -> {status, plan, reason}`:
  - `up_to_date` (vault == system), `ahead` (vault > system → E-SCHEMA-AHEAD),
  - `migratable` (đủ chuỗi bước → `plan=[(v,v+1),...]`), `no_path` (thiếu bước → E-SCHEMA-OUTDATED).

Planner KHÔNG thay validator: `validate.py` vẫn phát INV-19 (E-SCHEMA-OUTDATED/AHEAD). Planner trả lời
'migrate được không & theo trình tự nào' để lớp thực thi (tương lai) chạy đúng thứ tự trong transaction-FULL.

## Lớp THỰC THI — `executor.py` (Q2, 2026-07-04)

Đã dựng (DEC-045). Chạy plan trong transaction-FULL + validate-at-target + rollback:

- `_load_step(migrations_dir, N, M)`: load `vN_to_vM.py` → hàm `migrate(vault) -> list[transaction.Write]`.
- `execute_step(vault, system, N, M, migrate_fn, now=, validate_staged_fn=)`: begin(backup) → stage →
  VALIDATE ở version đích → occ_recheck → commit. FAIL → abort → vault giữ version N (rollback nguyên vẹn).
- `run_plan(vault, system, plan, migrations_dir, ...)`: chạy chuỗi bước tuần tự; DỪNG ở bước đầu FAIL.

**Cơ chế** (orchestration atomic migrate-or-rollback) đã kiểm end-to-end bằng **schema-v2-GIẢ-LẬP** trong
test (`phase11/test_migration_executor.py`, mock step sống trong tmp — KHÔNG để lại trong `_system` thật):
commit-khi-pass, rollback-khi-fail (vault giữ version cũ), bump version. `validate_staged_fn` là SEAM bơm
validate-at-target vì **validator-cho-version-đích THẬT chưa có** (DEC-011 vẫn đúng: transform + schema v2
THẬT để dành tới khi có version mới, qua change request). Bước migration THẬT đầu tiên (`v1_to_v2.py`) +
golden test `v1→v2 PASS` / `FAIL→rollback` sẽ thêm KHI có schema v2 thật — KHÔNG bịa bước giả trong `_system`.
