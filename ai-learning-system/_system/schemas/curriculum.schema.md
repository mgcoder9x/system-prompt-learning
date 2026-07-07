# Schema — `curriculum` (tính năng curriculum-driven-learning, CR-0007)

> **Chân lý schema nằm ở `validator/models.py` (class `Curriculum`, strict).** File này là bản mô tả
> người-đọc + hợp đồng máy-đọc `schema_fields`, được test `phase10/test_schemas_consistency.py` giữ
> khớp CHÍNH XÁC tập field của model. Đổi model mà quên cập nhật đây → test đỏ.

Front-matter có cấu trúc của `topics/<topic>/curriculum.md` — **giáo trình** một topic: danh sách điểm cần
học (Curriculum_Point) theo thứ tự, con trỏ tiến độ, cờ được-phép-dạy. `schema: curriculum`.
`strict=True, extra="forbid"`: sai kiểu/enum hoặc field lạ → `E-SCHEMA`.

Ràng buộc CẤU TRÚC (model, → E-SCHEMA): `updated ≥ created`; `point.id` khớp `^cp-\S+$`; `order ≥ 1`;
`status ∈ {not_started,in_progress,done}`. Ràng buộc NGỮ NGHĨA (Curriculum_Validator, mã riêng — Task 3):
`id` duy nhất (`E-CURR-DUP-ID`), `order` hoán vị 1..N (`E-CURR-ORDER`), `objective` không rỗng
(`E-CURR-EMPTY-OBJECTIVE`), `current_point` trỏ point tồn tại (`E-CURR-POINTER`), `lesson_id` trỏ lesson
thật (`E-CURR-LESSON-LINK`), `source_refs` trỏ file reference tồn tại (`E-CURR-REF-BROKEN`).

## Field (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"curriculum"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema (INV-19) |
| `topic_id` | ✓ | str | topic sở hữu giáo trình |
| `current_point` | ✓ | str | con trỏ tiến độ (id một Curriculum_Point) |
| `created` | ✓ | date | ngày tạo |
| `updated` | ✓ | date | ngày cập nhật; **≥ `created`** |
| `teachable` | – | bool | được-phép-dạy (mặc định `false`; chỉ `true` khi Curriculum_Validator PASS) |
| `points` | – | list[CurriculumPoint] | `{id: cp-*, order:int≥1, objective, status, lesson_id?, source_refs[]}` (mặc định `[]`) |

`CurriculumPoint` (nested): `id`(cp-*), `order`(int≥1), `objective`(str), `status`(not_started|in_progress|done),
`lesson_id`(str|null, ánh xạ lesson), `source_refs`(list[str], đường dẫn tương đối trong `reference/`).

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: Curriculum
  document_key: curriculum
  required: [schema, schema_version, topic_id, current_point, created, updated]
  optional: [teachable, points]
```
