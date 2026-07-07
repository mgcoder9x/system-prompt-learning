# Schema — `review_item` (spec 6.2)

> **Chân lý schema ở `validator/models.py` (class `ReviewItem`, strict).** File mô tả + hợp đồng máy-đọc
> `schema_fields`; test giữ khớp CHÍNH XÁC với model. Đổi model mà quên cập nhật đây → test đỏ.

Một item ôn tập, **nhúng** trong `lesson_state.review_items` (KHÔNG phải document độc lập → không có field
`schema`). Hai tầng trạng thái không mâu thuẫn: `card.state` do FSRS quản, `mastery_state` là lớp phủ tính thuần.

## Field (bám `models.py`)

| Field | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `id` | ✓ | str `^rv-\S+$` | id review item |
| `prompt_ref` | ✓ | str | trỏ câu ôn nguồn; không trùng (INV-10) |
| `fsrs_config_version` | ✓ | int | phiên bản cấu hình FSRS đã dùng |
| `created` | ✓ | date | ngày tạo |
| `card` | ✓ | Card | trạng thái FSRS (xem dưới) |
| `mastery_state` | ✓ | enum | `new\|in_review\|need_redo\|mastered` |
| `log` | – | list[LogEvent] | `{reviewed_at: str, rating: int 1..4}`; mặc định `[]` |

### `Card` (FSRS, v2.6/F-A — không có `New`)

| Field | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `state` | ✓ | enum | `Learning\|Review\|Relearning` |
| `step` | ✓ | int | bước học/ôn |
| `due_at_utc` | ✓ | str | UTC canonical `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` |
| `due_date` | ✓ | date | trục chuẩn so lịch (v2.6/F-B) |
| `stability` | – | float\|null | null khi chưa review |
| `difficulty` | – | float\|null | null khi chưa review |
| `last_reviewed_at_utc` | – | str\|null | null khi chưa review |

## Bất biến liên-field (model `_check_log_vs_card`)

- `log` rỗng ⇒ `stability = difficulty = last_reviewed_at_utc = null` **và** `mastery_state = new`.
- `log` không rỗng ⇒ `stability` và `difficulty` **không null** **và** `mastery_state ≠ new`.
  ("đã-review-chưa" xét theo `log`, KHÔNG theo `state` — v2.6/F-A.)

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: ReviewItem
  document_key: null            # nhúng trong lesson_state, không có field `schema`
  required: [id, prompt_ref, fsrs_config_version, created, card, mastery_state]
  optional: [log]
```
