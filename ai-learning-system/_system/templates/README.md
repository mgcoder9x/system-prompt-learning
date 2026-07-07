# templates/ — Khung scaffold topic & lesson (spec §2 layout, §3, §5)

Khung để lệnh `/learn` (intent `new_topic`) tạo topic/lesson mới **nhất quán** và **hợp-lệ validator**.

## Vì sao đuôi `.template.md` (quyết định — xem decisions/DEC-013)

File template có cấu trúc GIỐNG file dữ liệu (`topic_state`, `lesson_state`, `lesson`, `sources`,
`lesson_notes`) nhưng KHÔNG phải dữ liệu học — chúng nằm trong `_system/`. Nếu đặt đúng tên
`lesson_state.md`... sẽ trùng `_SYSTEM_DATA_NAMES` → validator báo **E-MIX-DATA (INV-18)** ngay trên chính
hệ thống. Dùng đuôi `.template.md` (giống `.schema.md`) để: (1) không trùng tên dữ liệu → không báo oan;
(2) INV-18 VẪN quét được `templates/` nên nếu ai lỡ để file dữ liệu THẬT ở đây vẫn bị bắt (defense-in-depth).

## Placeholder (thay khi instantiate)

```yaml
placeholders:
  - "<<TOPIC_ID>>"      # slug topic, vd: docker
  - "<<TOPIC_TITLE>>"   # tiêu đề topic
  - "<<LESSON_ID>>"     # <topic>/lesson-NNN, vd: docker/lesson-001
  - "<<LESSON_TITLE>>"  # tiêu đề lesson
  - "<<OBJECTIVE>>"     # mục tiêu lesson
  - "<<CREATED>>"       # ngày tạo ISO (YYYY-MM-DD)
```

## Quy tắc instantiate (bản chất, để không tạo vault sai)

- Topic mới KHỞI TẠO RỖNG: `lessons: []`, hai view rỗng với `generated_from_hash` = hash canonical của
  list rỗng (đã bake, test đối chiếu với `views.py`). Thêm lesson/review item ĐẦU TIÊN → transaction-FULL
  **REGEN** view bằng `views.py` (KHÔNG sửa hash tay) + cập nhật index `lessons` (INV-25).
- Lesson mới: `status: not_started`, `review_items: []`, mastery 5 trục = 0. `lesson.template.md` giữ đủ
  heading bắt buộc (`## Mục tiêu`, `## Sessions`).
- Mọi thao tác tạo đều qua Write Transaction (spec §10.3), validate trước khi commit.
