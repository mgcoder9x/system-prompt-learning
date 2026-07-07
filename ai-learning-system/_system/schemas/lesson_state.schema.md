# Schema — `lesson_state` (spec 5.1)

> **Chân lý schema nằm ở `validator/models.py` (class `LessonState`, strict).** File này là bản mô tả
> người-đọc + hợp đồng máy-đọc `schema_fields`, được test `phase10/test_schemas_consistency.py` giữ
> khớp CHÍNH XÁC tập field (tên + bắt buộc/tuỳ chọn) của model. Đổi model mà quên cập nhật đây → test đỏ.

Front-matter có cấu trúc của `lesson_state.md` — trạng thái + review items (phần MÁY KIỂM của một lesson).
`schema: lesson_state`. `strict=True, extra="forbid"`: sai kiểu/enum hoặc field lạ đều `E-SCHEMA`.

## Field (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"lesson_state"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema (INV-19/24) |
| `lesson_id` | ✓ | str | id lesson; phải khớp đường dẫn (INV-02) |
| `title` | ✓ | str | tiêu đề |
| `status` | ✓ | enum | `not_started\|in_progress\|learned\|needs_review` |
| `created` | ✓ | date | ngày tạo |
| `updated` | ✓ | date | ngày cập nhật; **≥ `created`** (model) và **≤ `today`** (validator, INV-05) |
| `objective` | ✓ | str | mục tiêu bài |
| `mastery` | ✓ | Mastery | 5 trục `concept/explain/apply/critique/teachback`, mỗi trục `{score 0..3, evidence: [str]}` |
| `prerequisites` | – | list[str] | tiên quyết (mặc định `[]`) |
| `sections_done` | – | list[str] | phần đã học |
| `sections_pending` | – | list[str] | phần còn lại |
| `open_gaps` | – | list[OpenGap] | `{id: gap-*, desc, detected: date}` |
| `review_items` | – | list[ReviewItem] | xem `review_item.schema.md` |
| `next_action` | – | str | việc kế (mặc định `""`) |
| `last_session` | – | date\|null | phiên gần nhất |

Ràng buộc cứng: `created ≤ updated` (model) và `updated ≤ today` (validator, INV-05 — today = ngày lịch thật theo utc_offset); `open_gaps[].id` khớp `^gap-\S+$`.

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: LessonState
  document_key: lesson_state
  required: [schema, schema_version, lesson_id, title, status, created, updated, objective, mastery]
  optional: [prerequisites, sections_done, sections_pending, open_gaps, review_items, next_action, last_session]
```
