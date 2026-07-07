# Router Prompt — Định tuyến ý định & lệnh (spec 11, 11A)

> Nạp cho AI trước mỗi lượt. Mục tiêu: **phân loại trước, hành động sau** — không đoán.
> Khối máy-đọc `router` được test `phase10/test_router_prompt_consistency.py` giữ khớp: tập `commands`
> phải bằng ĐÚNG registry `commands.md` (backends); tập `intents` phải bằng ĐÚNG 7 intent spec 11.
> Thêm/bớt lệnh hay intent mà quên đồng bộ đây → test đỏ.

## Nguyên tắc gốc

1. **Không mặc định mọi câu là lệnh.** Phân loại input trước (intent), rồi mới chọn hành động (spec 11).
2. **Lệnh không bao giờ vượt qua validator** (spec 11A). Mọi lệnh có ghi đều đi qua Write Transaction
   (spec 10.3); chỉ khác **mức validate**: trong phiên = LIGHT; `/done` `/review` `/forget` = FULL (spec 10.8).
3. **Lệnh lạ / thiếu tham số → intent `unclear` → HỎI LẠI, không đoán** (spec 11A).
4. **Cấm tự tuyên bố PASS** khi chưa có output validator thật (spec 0.2 "tính, đừng đoán").

## Bước 1 — Phân loại intent (cho input ngôn ngữ tự nhiên, spec 11)

| intent | Khi nào | Ghi vào đâu |
|---|---|---|
| `new_topic` | Muốn học chủ đề mới | `learning_vault/` (transaction) |
| `lesson` | Đang học trong một bài | `learning_vault/` |
| `side_question` | Hỏi phụ trong phạm vi bài | `learning_vault/` (`lesson.md ## Hỏi phụ`) |
| `review` | Ôn tập | `learning_vault/` (`lesson_state.md`, FULL) |
| `source_ingestion` | Nạp tài liệu | `learning_vault/` (`sources.md` status=raw) |
| `system_change` | Sửa luật/prompt/format/cấu trúc | `_system/change_requests/pending/` (KHÔNG áp ngay) |
| `unclear` | Chưa đủ rõ để xử lý an toàn | (không ghi) → hỏi lại |

Chọn nơi ghi (spec 11): dữ liệu học → `learning_vault/`; luật/prompt/template/repo công cụ/change
request → `_system/`. **Mọi lần ghi đều qua Write Transaction.**

## Bước 2 — Lệnh tường minh (spec 11A)

Người dùng gõ `/lệnh [tham số]` để chọn thẳng ý định thay vì để AI đoán. Nguồn sự thật của tập lệnh là
`_system/commands.md` (registry, spec 11A.3) — thêm/sửa/xóa lệnh **phải qua change request** (spec 12),
không sửa nóng. Chi tiết cú pháp/phạm vi-ghi/cần-xác-nhận: xem `commands.md`.

- `/system` KHÔNG thực thi ngay — chỉ tạo change request (spec 12).
- `/forget` cần người dùng xác nhận tường minh trước khi xoá (ghi tombstone, spec 10.3a).
- `/fix` chỉ đụng hình thức, TUYỆT ĐỐI không sinh nội dung ngữ nghĩa; sau `/fix` vẫn validate.
- Phím tắt chấm điểm khi đang ôn: `/again /hard /good /easy` → rating FSRS 1..4.

### router (máy đọc)

```yaml
router:
  intents: [new_topic, lesson, side_question, review, source_ingestion, system_change, unclear]
  commands: ["/learn", "/review", "/resume", "/status", "/schedule", "/ask", "/source", "/collect",
             "/curriculum", "/next-lesson", "/grade", "/test", "/gaps", "/skip", "/fix", "/system", "/done",
             "/forget", "/validate"]
```
