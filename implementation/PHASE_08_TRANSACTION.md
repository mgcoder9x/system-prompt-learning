# P08 — Transaction Engine (Manifest + OCC + Recovery)

**Mục tiêu:** ghi transaction-safe: không partial commit âm thầm, không ghi đè sửa tay, recovery được sau crash (spec 10.3).
**Phụ thuộc:** P05 (IO/bytes hash), P06 (LIGHT) + P07a (FULL-core) để validate staged. (P07b semantic bổ sung ở GĐ2, không chặn cơ chế transaction.)
**Giai đoạn MVP:** GĐ1 (cơ chế) — bắt buộc có sớm vì mọi ghi đi qua nó.

## Xây gì

`_system/validator/transaction.py`:

- `atomic_write_manifest(path, data)` — tmp + `fsync` + `os.replace` + fsync dir (spec 10.3).
- `begin(files, expected_read_hashes)` — tạo `.tx/<tx_id>/` **cùng gốc mỗi file**; so `current_hash==expected_read_hash` (lệch→`E-STALE-CONTEXT`); lưu backup+before_hash+staged_path; manifest `state=prepared`.
- `stage(writes)` — ghi ra `staged/`, cập nhật `staged_hash`.
- `validate_staged(level)` — gọi validator trên overlay staged.
- `occ_recheck()` — so `current_hash==before_hash` trước commit (lệch→`E-CONCURRENT-EDIT`).
- `commit()` — ghi **tombstones + danh sách op vào MANIFEST** (durable, atomic) TRƯỚC → `state=committing` → `os.replace` từng file **có retry exponential-backoff** (0.1→0.2→0.5→1→2s, WinError 32 cloud lock) → cập nhật `committed_files` → `state=committed` → **materialize `transaction_log.md` từ manifest** → dọn. `transaction_log.md` là **view dẫn xuất từ manifest**, KHÔNG phải nơi lưu gốc; nếu crash sau replace nhưng trước khi ghi log, recovery **roll-forward log/tombstone từ manifest**.
- `recover()` — RECOVER-FIRST: quét manifest `committing/interrupted`; roll-forward file chưa commit + **materialize lại transaction_log/tombstone từ manifest**; hash không khớp cả staged lẫn backup → `E-TX-PARTIAL`.
- Multi-root: mỗi gốc manifest riêng cùng `tx_id`; recovery xét đủ mọi root.
- **Tombstone (`10.3a`) là field trong manifest** (nguồn bền vững), không phải hậu tố best-effort. INV-11 tha xoá dựa trên tombstone **đã durable trong manifest của đúng tx_id**; `transaction_log.md` chỉ là bản materialize. Migration-as-transaction (`10.3b`).

## INV/mục spec liên quan

10.3 (transaction-safe), 10.3a (tombstone→INV-11), 10.3b (migration), INV-06/INV-11 (baseline từ backup), mã lỗi `E-TX-PARTIAL/E-STALE-CONTEXT/E-CONCURRENT-EDIT`.

## Cách test — FAULT INJECTION (`_system/validator/tests/phase08_tx/`)

```text
[ ] Happy path: begin→stage→validate PASS→commit→file thật đổi, .tx dọn, log ghi.
[ ] FAIL validate → abort: file thật KHÔNG đổi, state=aborted.
[ ] Crash sau khi replace 1/3 file (state=committing): recover() roll-forward đủ 3 → committed.
[ ] Crash khi manifest ghi dở: atomic_write_manifest đảm bảo hoặc bản cũ hoặc bản mới, không JSON rách.
[ ] E-STALE-CONTEXT: đổi file giữa T-read và begin → chặn.
[ ] E-CONCURRENT-EDIT: đổi file thật giữa begin và commit → chặn.
[ ] os.replace ném PermissionError 4 lần rồi OK (mock) → retry thành công; ném mãi → E-TX-PARTIAL.
[ ] INV-11 baseline: item in_review biến mất KHÔNG tombstone → E-REVIEW-LOST; CÓ tombstone (/forget) → tha.
[ ] Crash SAU khi replace hết file NHƯNG TRƯỚC khi ghi transaction_log: deletion đã xảy ra + tombstone ở manifest
    → recover() phải materialize log/tombstone từ manifest → INV-11 vẫn tha (KHÔNG false E-REVIEW-LOST); nếu manifest thiếu tombstone → E-TX-PARTIAL.
[ ] Cross-device: staged ở gốc khác đích → phải fail thiết kế (test khẳng định .tx cùng gốc).
[ ] Multi-root tx: thiếu manifest 1 root khi recover → E-TX-PARTIAL.
```

## Cạm bẫy

- `os.replace` **chỉ atomic 1 file/1 filesystem** — đừng hứa atomic cả transaction; recovery mới là thứ giữ toàn vẹn (spec 10.3 vá v2.3).
- Dùng **content-hash bytes**, không `mtime` (cloud-sync chạm mtime).
- `.tx/` phải cùng filesystem với đích (tránh `Errno 18`).
