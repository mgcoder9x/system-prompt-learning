# P03 — Pydantic Schema Models (strict)

**Mục tiêu:** biến schema spec (mục 5) thành model pydantic `strict=True` — đây là "chân lý schema" (spec 19), bắt lỗi cấu trúc, KHÔNG tự ép kiểu.
**Phụ thuộc:** P00.
**Giai đoạn MVP:** GĐ1.

## Xây gì

`_system/validator/models.py` — mọi model đặt `model_config = ConfigDict(strict=True)`:

- `VaultState` — spec 5.4: `utc_offset`, `date_policy`, `day_cutoff_hour:int`, `current_topic/lesson`,
  `export_policy` enum, `open_session{lesson_id,started_at,last_full_validate}`.
- `Card` — spec 5.1 vá v2.6: `state` enum **Learning|Review|Relearning** (KHÔNG có New); `step:int`; `stability/difficulty:Optional[float]`;
  `due_at_utc:str`, `due_date:date`, `last_reviewed_at_utc:Optional[str]`.
  **Validator theo "đã-review-chưa" (v2.6/F-A):** `@model_validator(after)` ở ReviewItem — `log == []` (chưa review) ⇒ `stability/difficulty/last_reviewed_at_utc` PHẢI None; `log != []` ⇒ `stability/difficulty` PHẢI có. KHÔNG dùng `state==New` (py-fsrs không có New).
- `ReviewItem` — `id`, `prompt_ref`, `fsrs_config_version:int`, `created:date`, `card`, `log:list`, `mastery_state` enum.
- `LessonState` — `mastery` (5 trục = {score:0..3, evidence:list[str]}), `open_gaps`, `review_items`, `status` enum, ngày.
- `TopicState` — `lessons` index (id+status), `current_lesson`, `has_draft_knowledge:bool`, `review_schedule`, `assessment`.
- `Sources`, `Anchor`, `Claim` (id/class/status/text/source_refs/premise_refs/draft_reason), `Evidence` (axis/timestamp/quote/ai_assessment).
- Field validator: id pattern (`rv-*`,`gap-*`,`src-*`,`clm-*`,`ev-*`).
- **Kiểu ngày:** model dùng type Python thật — `created/updated/timestamp: date`, `due_date: date`, `due_at_utc/last_reviewed_at_utc: str` (canonical UTC vì file quote sẵn). `normalize_yaml_object` (P02) chạy **trước** pydantic và trả về **date object** (không phải string), nên `strict=True` nhận đúng type. Việc stringify date→"YYYY-MM-DD" CHỈ xảy ra trong `canonical_hash` (P02), không ở model. Đây là chỗ hoà giải mâu thuẫn "strict vs canonical string".

## INV/mục spec liên quan

5.1–5.5, INV-01 (schema/kiểu/enum), INV-04 (id pattern; uniqueness cross-file để P07), INV-05 (ngày, `created<=updated<=today`).

## Cách test (`_system/validator/tests/phase03_schema/`)

```text
[ ] valid/ : mọi *_state fixture hợp lệ → model parse OK.
[ ] invalid/E-SCHEMA__string_score.md : score="2" (string) → strict REJECT (không ép "2"→2).
[ ] invalid/E-SCHEMA__newcard_has_stability.md : log rỗng (chưa review) nhưng stability=1.2 → reject theo-log.
[ ] invalid/E-SCHEMA__review_no_stability.md : log không rỗng nhưng stability=null → reject.
[ ] invalid/E-SCHEMA__bad_date.md : updated < created → reject (INV-05).
[ ] invalid/E-SCHEMA__bad_enum.md : status="done" → reject.
[ ] strict chặn coercion: field int nhận 2.0(float) → reject.
```

## Cạm bẫy

- `strict=True` là điểm mấu chốt: validator phải **bắt lỗi**, không **âm thầm sửa** (ép `"1.0"`→`1.0` sẽ che lỗi + lệch hash — spec 16.1).
- Ràng buộc **theo "đã-review-chưa"** (log rỗng vs không) của Card là fix v2.6/F-A; quên thì item chưa review bị chặn oan.
- `*.schema.md` chỉ là tài liệu; **model pydantic thắng** khi lệch (spec 19).
