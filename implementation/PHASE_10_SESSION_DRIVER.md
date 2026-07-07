# P10 (driver) — session.py: `/review` `/done` chạy transaction-FULL thật

**Mục tiêu:** driver code ghép FSRS + views + transaction thành thao tác MUTATE vault thật, an toàn (transaction-FULL-core), validate-gated.
**Phụ thuộc:** P01 (fsrs_adapter), P03 (models), P07a (validate_full_core), P08 (transaction), P09 (views) — tất cả đã xanh.
**Giai đoạn:** khép GĐ1 thành vòng dùng được.

## Sự thật interface (đã đọc code + verify, KHÔNG đoán)

1. **Convention replay là AUTHORITATIVE ở validator** `_check_replay` (validate.py): reviewed item được dựng lại bằng
   `FA.replay(datetime.combine(rv.created, 00:00, tz_local), log, cfg, offset)` rồi so `FA.cards_equal`.
   ⇒ **Driver PHẢI sinh card bằng ĐÚNG hàm/convention đó** (local-midnight của `created`), để INV-08 đúng *by construction*.
   (seed due giờ-trong-ngày không ảnh hưởng vì card mới có stability=None; đã xác nhận trong comment validator + spike.)
2. **derive_mastery** là authority INV-21: `mastery_state = FA.derive_mastery(card_dict, log, cfg)`.
3. **INV-24**: `rv.fsrs_config_version` phải == `cfg["fsrs_config_version"]`.
4. **views.regen_all(lessons_models, stage="core")** → `{review_schedule:{generated_from_hash, items:[{lesson_id,item_id,due_date(date),mastery_state}]}, assessment:{generated_from_hash, <ax>_avg}}`.
   Cần **model LessonState của MỌI lesson trong topic**, trong đó lesson vừa review phải là bản MỚI.
5. **YAML round-trip (verify thực nghiệm 2026-07-01):** `yaml.safe_dump` một `date` obj → `2026-07-12` (unquoted) → `safe_load` → `date`;
   một `str` "2026-07-12T13:00:00Z" → quoted → `str`. ⇒ dựng front-matter dict với **type native đúng** (date fields = `date` obj; due_at_utc/reviewed_at/last_reviewed_at_utc = `str`; stability None = null) rồi `safe_dump(sort_keys=False, allow_unicode=True)`.
6. **Transaction.validate_staged(system_root, "full")** dựng overlay = vault thật + staged, chạy `validate_full_core`. ⇒ **validator là lưới an toàn**: driver đề xuất, validator định đoạt; card/view sai → transaction ABORT, không commit bẩn.
7. **`/review` `/done` là transaction 1-GỐC (vault)**: chỉ đụng lesson_state + topic_state (+vault_state.open_session). KHÔNG đụng `_system/` ⇒ **không cần multi-root orchestrator** (đó là việc của `/system`, defer).

## Thiết kế `session.py`

- `_replay_card(created, log, cfg, offset)` — bọc đúng convention validator (local-midnight).
- `_card_for_yaml(card_dict)` — đổi `due_date` str→`date` obj; giữ str cho due_at_utc/last_reviewed_at_utc; stability/difficulty float|None.
- `_dump_state(raw_dict)` — `"---\n"+yaml.safe_dump(raw, sort_keys=False, allow_unicode=True)+"---\n"+body`.
- `_regen_topic_views(vault, topic, updated_lesson_raw)` — parse mọi lesson_state của topic thành model (thay lesson vừa đổi bằng bản mới), gọi `VW.regen_all`, ghép vào topic_state raw.
- `cmd_review(vault, system, lesson_id, item_id, grade, reviewed_at)`:
  1. load cfg; đọc lesson_state.md raw (+ hash cũ).
  2. tìm item; `new_event = {reviewed_at: FA.canonical_reviewed_at(...), rating: MAP[grade]}`; `new_log = log+[event]`.
  3. `card = _replay_card(created, new_log, cfg, offset)`; `mastery_state = FA.derive_mastery(card, new_log, cfg)`.
  4. cập nhật raw: item.card/_log/mastery_state; `updated = reviewed_local_date`.
  5. regen topic views → topic_state raw mới (+ hash cũ).
  6. `Transaction(vault, "full").begin([Write(lesson_state, new_bytes, hash_cũ), Write(topic_state, new_bytes, hash_cũ)])`
     → `stage()` → `validate_staged(system,"full")`; PASS → `occ_recheck()` → `commit()`; FAIL → `abort()` + trả report lỗi.
- `cmd_done(vault, system, ...)` — regen views + clear `vault_state.open_session` + validate FULL + commit (khép sổ).
- `_recover_first(vault)` — **spec 10.3 (BẮT BUỘC)**: gọi `TX.recover(vault)` ở ĐẦU mỗi lệnh, TRƯỚC khi đọc context. Hoàn tất tx dở (roll-forward) hoặc chặn `E-TX-PARTIAL`. Đặt trước khi đọc để bản đọc là hậu-recovery (tránh `E-STALE-CONTEXT` giả khi tx dở đụng đúng file lệnh sắp ghi).
- **CLI `main(argv)` (spec 10.5)** — `/review` `/done` là LỆNH SHELL độc lập môi trường:
  `session.py review --system --vault --lesson --item --grade [--at] [--json]` và
  `session.py done --system --vault --lesson [--at] [--json]`. In report `validate_staged` **nguyên văn**
  (tái dùng `Report.dump`) + dòng `committed=`. Exit: `0`=committed+PASS, `1`=không commit
  (validator FAIL / TxError / bad grade / item lạ), `2`=lỗi tham số. `--grade` không giới hạn choices
  để `EReviewBadGrade` phát mã `E-REVIEW-BADGRADE` đúng bảng 10.4.

## Kịch bản test (golden, phase10) — ĐÃ HIỆN THỰC & XANH (11 test)

`tests/phase10/test_session_review.py` (7) + `test_session_done.py` (4). Chạy trên COPY vault demo thật.

```
[x] cmd_review item lần đầu (grade Good): sau commit → validate_full_core(vault) PASS;
    item.log 1 event; mastery_state='in_review'; stability != null; topic_state.review_schedule cập nhật.
[x] Tất định: cmd_review 2 lần trên 2 bản sao → lesson_state.md + topic_state.md bytes GIỐNG HỆT.
[x] Validator là lưới an toàn: monkeypatch FA.review trả card lệch (stability+100)
    → validate_staged FAIL (E-REVIEW-MISCALC) → ABORT → file thật KHÔNG đổi.
[x] grade sai (5) → EReviewBadGrade, không transaction (.tx không tồn tại).
[x] OCC: sửa tay lesson_state giữa đọc-context và begin → E-STALE-CONTEXT.
[x] item không tồn tại → SessionError.
[x] INV-05: updated >= created sau commit.
[x] /done clear open_session.lesson_id/started_at + set last_full_validate → validate PASS.
[x] /review rồi /done end-to-end: cờ clear, item review giữ nguyên, validate PASS.
[x] /done tất định: 2 vault song song → vault_state + topic_state bytes GIỐNG HỆT.
[x] /done OCC: vault_state đổi giữa đọc-context và begin → E-STALE-CONTEXT.
[x] RECOVER-FIRST: tx 'interrupted' thật (ép replace file đích fail) → /review roll-forward
    file đó + dọn .tx cũ rồi commit bình thường; /done cũng recover-first.
[x] RECOVER-FIRST chặn ghi: partial + file đích bị sửa tay (hash lạ) → E-TX-PARTIAL, ghi mới BỊ CHẶN.
[x] vault sạch → _recover_first trả [] (no-op).
[x] CLI review/done happy → exit 0, JSON committed+pass, validator thật PASS end-to-end.
[x] CLI grade sai → exit 1 E-REVIEW-BADGRADE; item lạ → exit 1 E-DRIVER; --at naive → exit 2 E-ARG (file không đổi).
[x] CLI subprocess THẬT (python session.py review ...) → exit 0 (chạy như lệnh shell độc lập môi trường).
```

## Sự thật kiểm chứng thêm khi hiện thực (không đoán)

- **`yaml.safe_dump` tự quyết quoting an toàn round-trip**: verify thực nghiệm (PyYAML 6.0.3) — dump `+07:00`/`+05:30` KHÔNG quote (safe_load lại ra str đúng), nhưng dump `+10:00`/`+11:00`/`+12:00`/`-10:00`/`+14:00` CÓ quote (nếu để trần sẽ bị resolver sexagesimal biến thành int). ⇒ `_dump_state` dùng `safe_dump` là an toàn round-trip *by construction* cho MỌI utc_offset hợp lệ, không cần tự quote thủ công.
- **`due_at_utc`/`last_reviewed_at_utc`/`reviewed_at`** (chuỗi có `:` và offset/`Z`) → `safe_dump` quote → `safe_load` ra str. **`due_date`/`created`/`updated`** (date obj) → unquoted `YYYY-MM-DD` → date. Khớp `_STR_FIELDS` + model strict.
- **`cmd_review` dùng thẳng `FA.review`** (không tự chế convention): `created_at = datetime.combine(rv.created, 00:00, tz_local)` — ĐÚNG convention `validate._check_replay` ⇒ INV-08 đúng by-construction (đã chứng minh qua test lưới-an-toàn: chỉ cần lệch card là validator bắt).
- **`/done` không sửa nội dung lesson** — chỉ clear cờ + regen view (idempotent) + FULL-validate + commit trong CÙNG transaction (spec 11B.2). Nội dung học là việc AI ghi trong phiên.

## Cạm bẫy (root-cause, không vá ngọn)

- KHÔNG tự chế convention replay riêng cho driver — phải DÙNG CHUNG với validator, nếu không INV-08 lệch.
- KHÔNG dump due_date dạng string (model strict reject) — phải là `date` obj.
- Driver KHÔNG được tự tuyên bố PASS — chỉ commit khi `validate_staged` PASS thật.


## Bổ sung: `cmd_forget` (spec 10.3a + 11A `/forget`) — ĐÃ XONG

Xoá lesson CÓ THẨM QUYỀN: ghi TOMBSTONE (tha INV-11) + xoá mọi file lesson + gỡ khỏi `topic_state.lessons`
+ regen view (loại lesson) + đồng bộ `current_lesson` (topic+vault). Transaction-FULL. Chưa `--confirm` → từ chối.
Topic-level DEFER (blast radius lớn — khai báo trung thực).

Nền (enabler, đã fix gốc): `transaction._prune_empty_dirs` dọn thư mục rỗng sau khi xoá file — nhất quán ở
overlay/commit/recovery. Lý do: xoá file lesson để lại dir rỗng → `_validate_topic` báo `E-INDEX-MISMATCH`
(đã kiểm chứng thực nghiệm). Chỉ rmdir dir RỖNG (không mất dữ liệu), idempotent (an toàn crash).

INV-11 giờ được cắm thật vào `Transaction.validate_staged` (FULL) qua `_check_review_preservation`
(so review-state backup↔staged + tombstone). Trước đó `check_review_not_lost` là hàm mồ côi.

Test: `phase10/test_session_forget.py` (4: cần confirm; topic-level defer; lesson lạ; forget item in_review
→ tombstone tha INV-11 → commit + validate PASS + tombstone trong transaction_log), `test_session_cli.py`
(+2: forget cần --confirm), `phase08_tx/test_inv11_wired.py` (4), `test_dir_prune.py` (4).
