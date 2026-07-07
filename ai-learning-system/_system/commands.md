# Command Registry (spec 11A.3)

Nguồn sự thật của tập lệnh. Thêm/sửa/xóa lệnh PHẢI qua change request (spec 12), không sửa nóng.
Mọi ghi đều qua transaction; chỉ **mức validate** khác nhau (LIGHT trong phiên / FULL tại `/done` `/review` `/forget`, spec 10.8).
Lệnh có `backend` là **lệnh shell chạy được** (spec 10.5); test `phase10/test_commands_registry.py` kiểm khớp CLI thật.

| Lệnh | Việc | Ghi vào đâu |
|------|------|-------------|
| `/learn <chủ đề>` | Tạo/tiếp tục học một topic | `topics/...` (transaction) |
| `/review [topic\|all]` | Ôn câu tới hạn hôm nay, chấm FSRS | `lesson_state.md` (transaction-FULL) |
| `/resume` | Tiếp tục chỗ dở (`vault_state.current_lesson` + `next_action`) — MỞ phiên (CR-0003) | `vault_state.open_session` (transaction-LIGHT) |
| `/status` | Tổng quan: đang học gì, due hôm nay, mastery | chỉ đọc |
| `/schedule [n]` | Lịch ôn n ngày tới | chỉ đọc |
| `/ask <câu hỏi>` | Hỏi phụ trong lesson hiện tại | `lesson.md ## Hỏi phụ` |
| `/source <link\|text>` | Nạp tài liệu | `sources.md` status=raw |
| `/collect <topic> <slug> <nội dung>` | Ghi lát cắt tài liệu tham chiếu (dựng giáo trình) | `topics/<topic>/reference/<slug>.md` (transaction-LIGHT) |
| `/curriculum <topic> <points-json>` | Dựng giáo trình (điểm học + `teachable`); chế độ `--insert-at <pos> --point <json>` chèn điểm giữa chừng (R8) | `topics/<topic>/curriculum.md` (transaction-FULL) |
| `/next-lesson <topic>` | Sinh lesson kế cho `current_point` (nhảy bài) | `lessons/lesson-NNN` + `topic_state.lessons[]` + `curriculum` (transaction-FULL) |
| `/grade <topic> <submission> <file> <target> <verdict>` | Ghi bản ghi chấm bài thực hành (bài nộp ở `exam/` NGOÀI vault) | `topics/<topic>/exam_results.md` (transaction-LIGHT) |
| `/test [lesson]` | Chạy cổng "đã hiểu" (learned_gate) — BÁO CÁO, không tự đặt learned (CR-0002) | chỉ đọc |
| `/gaps` | Liệt kê `open_gaps` | chỉ đọc |
| `/skip` | Bỏ qua câu ôn đang hiện, không chấm | không đổi state |
| `/again` `/hard` `/good` `/easy` | Phím tắt chấm rating 1..4 khi đang ôn | `lesson_state.md` (transaction) |
| `/done` | Kết phiên: cập nhật state + sinh view + validate | transaction-FULL |
| `/system <đề xuất>` | Đề xuất sửa hệ thống — KHÔNG áp dụng ngay | `change_requests/pending/` |
| `/forget <lesson_id\|topic_id>` | Xoá có thẩm quyền (cần xác nhận) — ghi tombstone | transaction-FULL (10.3a) |
| `/fix [file]` | Auto-format cú pháp Markdown/YAML — CHỈ hình thức | transaction-LIGHT |
| `/validate` | Chạy validator thủ công, dán report nguyên văn | chỉ đọc |

Ghi chú:
- `/system` KHÔNG thực thi ngay — chỉ tạo change request (spec 12).
- `/fix` chỉ đụng hình thức (khoảng trắng/heading/fence/khóa YAML); TUYỆT ĐỐI không sinh nội dung ngữ nghĩa,
  không reflow giá trị string trong fenced YAML (đặc biệt `evidence.quote`). Sau `/fix` vẫn validate.
- `/done` là điểm "neo" transaction để mỗi buổi kết thúc ở trạng thái đã validate.
- Lệnh lạ / thiếu tham số → intent `unclear` → hỏi lại, không đoán.

## backends (máy đọc)

Ánh xạ lệnh → lệnh shell hiện thực (GĐ1). `null` = lệnh tầng-agent chưa có backend code riêng.

```yaml
backends:
  "/review": "session.py review"
  "/done": "session.py done"
  "/forget": "session.py forget"
  "/validate": "validate.py"
  "/learn": "session.py learn"
  "/schedule": "session.py schedule"
  "/resume": "session.py resume"
  "/status": "session.py status"
  "/ask": "session.py ask"
  "/source": "session.py source"
  "/collect": "session.py collect"
  "/curriculum": "session.py curriculum"
  "/next-lesson": "session.py next_lesson"
  "/grade": "session.py grade"
  "/test": "session.py test"
  "/gaps": "session.py gaps"
  "/skip": null
  "/fix": null
  "/system": null
```
