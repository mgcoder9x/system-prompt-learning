# P07a — Validator FULL-CORE (cấu trúc + FSRS + view) — GĐ1

**Mục tiêu:** đủ INV để `/done` GĐ1 "transaction-safe + đúng tuyệt đối ở tầng cấu trúc" mà CHƯA cần claim/evidence.
**Phụ thuộc:** P01 (replay), P02 (hash), P03 (models), P05 (IO), P09 (views).
**Giai đoạn MVP:** **GĐ1** (đây là phần P08 và `/done` cần để validate staged).

## INV thuộc P07a (FULL-core)

- **Cấu trúc:** INV-01 (model), INV-02 (id↔path), INV-03 (ref tồn tại), **INV-04 (id duy nhất cross-file)**, INV-05 (ngày).
- **Không trùng:** **INV-10 (mỗi `prompt_ref` chỉ một review item)** → `E-REVIEW-DUP`.
- **FSRS:** INV-08 (replay `log`→card, `cards_equal` P01), INV-21 (`derive_mastery` khớp).
- **View:** INV-09 (regen object + **deep-compare** + so hash → `E-VIEW-MISMATCH`/`E-VIEW-STALE`) — cần P09.
- **Portability/vùng:** INV-16 (abspath), INV-17/18 (không trộn root), **INV-20 (`_scratch`/`.tx` phi-thẩm-quyền: không ref trỏ vào, validator bỏ nội dung)**, INV-19 (semver → `E-SCHEMA-OUTDATED`/`E-SCHEMA-AHEAD`), INV-24 (`fsrs_config_version` tồn tại).
- **Index/cache:** INV-25 (lessons↔folder, status↔lesson_state, current_lesson↔vault_state).
- **INV-06 / INV-11** chỉ enforce đầy đủ khi có baseline transaction → kiểm ở **P08** (ngoài transaction chỉ kiểm hệ quả tĩnh).

## Cách test — GOLDEN SUITE CORE (`_system/validator/tests/phase07a_core/`)

Mỗi vault hỏng = 1 INV; tên file = mã lỗi kỳ vọng (spec 10.6).

```text
[ ] valid_vault_core/ (topic+lesson+views đúng, CHƯA có claim/evidence) → FULL-core PASS.
[ ] invalid/E-REF-BROKEN__prompt_ref_missing/
[ ] invalid/E-REVIEW-DUP__two_items_same_prompt_ref/
[ ] invalid/E-REVIEW-MISCALC__drifted_card/
[ ] invalid/E-STATE-DERIVED__wrong_mastery/
[ ] invalid/E-VIEW-STALE__old_hash/
[ ] invalid/E-VIEW-MISMATCH__edited_view_same_hash/
[ ] invalid/E-INDEX-MISMATCH__folder_vs_index/
[ ] invalid/E-INDEX-MISMATCH__current_lesson_cache/
[ ] invalid/E-SCHEMA-AHEAD__vault_newer/
[ ] invalid/E-SCHEMA-OUTDATED__vault_older/
[ ] invalid/E-PORT-ABSPATH__abspath_in_state/
[ ] invalid/E-REF-BROKEN__ref_into_scratch/   (INV-20: file thật trỏ vào _scratch/ → gãy khi xoá)
[ ] Chạy 2 lần trên valid_vault_core → report giống hệt (deterministic).
```

## Cạm bẫy

- INV-09 phải **deep-compare nội dung view TRƯỚC, rồi hash** (spec 4) — hash một mình bỏ sót view sửa tay giữ hash cũ.
- INV-20: validator phải **bỏ nội dung** `_scratch`/`.tx` nhưng vẫn cấm file thật tham chiếu vào đó.
- FULL-core phải chạy được **độc lập** (`--level full --scope core`) để P08 gọi khi `/done` ở GĐ1.
