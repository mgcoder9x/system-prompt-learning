# CR-0007 — Schema mới `curriculum` + `exam_results` (giáo trình + bản ghi chấm bài)

```yaml
id: cr-0007
title: "Thêm 2 schema dữ liệu học: curriculum (giáo trình nhiều điểm) + exam_results (bản ghi chấm exam)"
status: approved
date_opened: 2026-07-05
date_decided: 2026-07-05
version_bump: null   # schema_version mỗi file mới = 1; KHÔNG đổi file cũ → không bump VERSION hệ
related: [spec curriculum-driven-learning R3/R9/R11, DEC-055, DEC-008 (drift-guard schema)]
recommendation: "THÊM 2 schema qua model pydantic + schemas/*.schema.md + drift-guard (đồng nhất cơ chế hiện có)"
```

## 1. Ghi yêu cầu (§12 bước 1)

Cần một artifact **giáo trình** máy-đọc (nhiều điểm học, thứ tự, trạng thái, ánh xạ lesson, truy vết nguồn) và một **bản ghi chấm bài exam** (gắn bài nộp ↔ topic/điểm học). Cả hai là dữ liệu học → thuộc `learning_vault/`.

## 2. Phân tích (§12 bước 2)

- Hệ chưa có schema cho "giáo trình" — hiện chỉ có `topic.md ## Lộ trình` (light-touch, không cấu trúc cứng, DEC-050). Multi-lesson cần cấu trúc kiểm-được.
- `topic_state.lessons[]` VẪN là nguồn sự thật index bài (INV-25); `curriculum.points[].lesson_id` chỉ là **tham chiếu** được validate khớp → KHÔNG tạo nguồn-thứ-2.
- Chấm exam là Class D (chất lượng do người/AI); chỉ **ref-integrity** của bản ghi là Class A.

## 3. Đề xuất schema (§12 bước 3)

**`curriculum` (`topics/<topic>/curriculum.md` front-matter):** `schema, schema_version=1, topic_id, teachable(bool), current_point(str), points[]{id, order:int, objective, status∈{not_started,in_progress,done}, lesson_id?(str|null), source_refs[](str, đường dẫn tương đối trong reference/)}, created, updated`.

**`exam_results` (`topics/<topic>/exam_results.md` front-matter):** `schema, schema_version=1, topic_id, results[]{submission_id, ref(tương đối tới ../../exam/... NGOÀI vault), target(topic|curriculum_point), graded_at, verdict(text Class D)}`.

Thêm: `schemas/curriculum.schema.md` + `schemas/exam_results.schema.md` (khối `schema_fields` máy-đọc) + model pydantic trong `models.py` + drift-guard test (đối chiếu `model_fields`, như DEC-008).

## 4. Rủi ro (§12 bước 4)

Thấp–trung. Không đổi file/schema cũ → không hồi quy schema hiện có. Rủi ro chính: field lệch model↔schemas → drift-guard test bắt. `curriculum.md`/`exam_results.md` là tên file mới, KHÔNG trùng `_SYSTEM_DATA_NAMES` mở rộng? → cần thêm 2 tên này vào danh sách dữ-liệu-học của INV-18 để chống lạc vào `_system/` (kiểm khi áp).

## 5. Đề xuất (§12 bước 5)

Áp 2 schema + drift-guard theo Task 2 (tasks.md). RED-first: viết test drift-guard đỏ trước, rồi thêm model.

## 6. Quyết định (§12 bước 6–7)

`pending` — chờ owner "Duyệt". Khi duyệt: áp Task 2, move approved + changelog + ghi DEC.
