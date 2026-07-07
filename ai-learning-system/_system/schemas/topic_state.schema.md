# Schema — `topic_state` (spec 5.2)

> **Chân lý schema ở `validator/models.py` (class `TopicState`, strict).** File mô tả + hợp đồng máy-đọc
> `schema_fields`; test giữ khớp CHÍNH XÁC với model. Đổi model mà quên cập nhật đây → test đỏ.

Trạng thái topic + index lesson + hai VIEW sinh lại được (review_schedule, assessment).
`schema: topic_state`. `strict=True, extra="forbid"`.

## Field (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"topic_state"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema |
| `topic_id` | ✓ | str | id topic |
| `title` | ✓ | str | tiêu đề |
| `created` | ✓ | date | ngày tạo |
| `updated` | ✓ | date | ngày cập nhật; **≥ `created`** (model) và **≤ `today`** (validator, INV-05) |
| `review_schedule` | ✓ | ReviewScheduleView | `{generated_from_hash, items: [{lesson_id, item_id, due_date, mastery_state}]}` (INV-09) |
| `assessment` | ✓ | AssessmentView | `{generated_from_hash, concept_avg, explain_avg, apply_avg, critique_avg, teachback_avg}` (INV-09) |
| `current_lesson` | – | str\|null | lesson đang học |
| `has_draft_knowledge` | – | bool | có claim draft? (mặc định `false`, INV-26) |
| `lessons` | – | list[LessonIndexEntry] | index `{id, status}`; id không trùng (INV-04) |

Ràng buộc cứng: `created ≤ updated` (model) và `updated ≤ today` (validator, INV-05 — today = ngày lịch thật theo utc_offset); `lessons[].id` duy nhất (INV-04).
Hai view mang `generated_from_hash` để INV-09 kiểm khớp nguồn (không được lệch/stale).

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: TopicState
  document_key: topic_state
  required: [schema, schema_version, topic_id, title, created, updated, review_schedule, assessment]
  optional: [current_lesson, has_draft_knowledge, lessons]
```
