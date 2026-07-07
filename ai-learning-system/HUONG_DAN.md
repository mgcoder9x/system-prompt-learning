# Hướng dẫn sử dụng — Cho NGƯỜI HỌC

Đây là hệ thống học tập do **AI dạy** + **bộ máy đảm bảo** (validator/lịch ôn FSRS). Bạn học bằng cách
**trò chuyện với một AI** (đã đọc `START_HERE.md`); AI vừa dạy vừa gõ lệnh để lưu. Bạn KHÔNG cần nhớ lệnh —
cứ nói bằng lời; phần dưới liệt kê lệnh (tiếng Anh) chỉ để tham khảo/gõ nhanh.

> Lệnh giữ nguyên **tiếng Anh** (chuẩn hoá). Bạn có thể nói tiếng Việt ("học Docker", "ôn tập") — AI tự ánh xạ.

## Dùng hằng ngày (nói với AI)

| Bạn muốn | Nói / gõ | Điều xảy ra |
|---|---|---|
| Học chủ đề mới | "học Docker" hoặc `/learn Docker` | Tạo topic + **lộ trình điểm cần học** (`topic.md`) + bài học đầu + **hỏi câu 1** |
| Trả lời câu hỏi | (trả lời bình thường) | AI chấm, phản hồi, rồi **sang câu tiếp theo** (một câu/lượt) |
| Ôn tập | "ôn tập" hoặc `/review` | Lấy câu **tới hạn hôm nay** (lịch FSRS), hỏi để ôn; buổi ôn ghi vào `## Sessions` của bài |
| Xem đang ở đâu | `/status` | Topic/bài hiện tại + số câu cần ôn hôm nay + gợi ý bước kế |
| Xem lịch ôn | `/schedule 7` | Các câu tới hạn trong 7 ngày tới |
| Điểm chưa chắc | `/gaps` | Danh sách `open_gaps` (chỗ còn mơ hồ) |
| Tiếp buổi dở | `/resume` | Mở lại bài đang học + gợi ý việc kế (`next_action`) |
| Kết thúc buổi | `/done` | Chốt trạng thái + sinh view + **validate** (chỉ "học xong" khi qua cổng hiểu) |
| Nạp tài liệu | `/source <link>` | Lưu nguồn (chưa xác thực) để AI xử lý thành dẫn chứng |
| Hỏi phụ | `/ask <câu hỏi>` | Ghi câu hỏi phụ vào bài hiện tại |
| Kiểm cổng "đã hiểu" | `/test` | Báo cáo bài đã đạt ngưỡng hiểu chưa (không tự đánh dấu) |
| Xoá có thẩm quyền | `/forget <lesson\|topic>` | Xoá (cần xác nhận) — ghi tombstone, không mất dấu vết |
| Tự kiểm tính đúng | `/validate` | Chạy validator, xem báo cáo (bạn là phòng tuyến cuối) |

Lệnh khác (ít dùng): `/skip` (bỏ qua câu ôn, không chấm), `/again /hard /good /easy` (phím tắt chấm 0–3 khi ôn),
`/fix` (tự sửa định dạng — CHƯA bật), `/system` (đề xuất sửa hệ thống → chỉ tạo yêu cầu, không áp ngay).

## Học theo giáo trình — chủ đề dài, nhiều bài

Với chủ đề lớn (ví dụ Docker), thay vì một bài, bạn có thể để AI dựng **giáo trình** (danh sách điểm cần học,
học tuần tự) rồi sinh nhiều bài bám theo. Vòng này KHÔNG bắt buộc — chỉ dùng khi muốn học bài bản.

| Bạn muốn | Nói / gõ | Điều xảy ra |
|---|---|---|
| Nạp tài liệu tham chiếu | "thu tài liệu này" hoặc `/collect` | AI lưu lát cắt tài liệu vào `reference/` của chủ đề (đầu vào để dựng giáo trình) |
| Dựng giáo trình | "lập giáo trình Docker" hoặc `/curriculum` | Tạo `curriculum.md` — các **điểm cần học** theo thứ tự; chỉ "được-phép-dạy" khi giáo trình hợp lệ |
| Chèn điểm giữa chừng | "thêm một điểm học vào giữa" hoặc `/curriculum --insert-at` | Chèn điểm mới vào vị trí bạn muốn, giữ nguyên các điểm cũ + tiến độ đã học (R8) |
| Kiểm giáo trình | `/curriculum --check` | Báo cáo giáo trình PASS/FAIL (chỉ đọc, không đổi gì) |
| Học bài kế | "bài tiếp theo" hoặc `/next-lesson` | Sinh bài mới cho **điểm đang học**; học xong (`/done`) đạt cổng hiểu → giáo trình **tự tiến** sang điểm kế |
| Chấm bài thực hành | `/grade` | Ghi kết quả chấm cho bài bạn nộp ở thư mục `exam/` (bài nộp có thể là **code**) |

> Bài thực hành bạn nộp (kể cả code) đặt ở thư mục `exam/` nằm **ngoài** `learning_vault/` — để kho học của bạn
> luôn sạch (chỉ ghi chú, không lẫn mã nguồn). Hệ chỉ lưu **bản ghi chấm** (điểm/nhận xét) trong kho.

## Dữ liệu của bạn nằm ở đâu (mở đọc được — markdown thuần)

- `learning_vault/topics/<chủ đề>/topic.md` — **Lộ trình** điểm cần học + **Knowledge Map** (kiến thức đã chốt).
- `.../lessons/lesson-XXX/lesson.md` — bài dạy + **`## Sessions`** (nhật ký hỏi-đáp mỗi buổi dạy/ôn).
- `.../lesson_state.md` — tiến độ + thẻ ôn FSRS (máy quản, đừng sửa tay).
- `learning_vault/vault_state.md` — con trỏ "đang học gì".

## Hệ đảm bảo gì / KHÔNG gì (nói thật)

- **Đảm bảo tuyệt đối (máy):** cấu trúc/ngày/lịch ôn/tham chiếu/toàn vẹn — sửa bậy sẽ bị báo lỗi, không hỏng âm thầm. Copy đi máy khác vẫn chạy.
- **KHÔNG đảm bảo:** "bạn đã hiểu thật chưa" + chất lượng dạy — cái đó tuỳ AI dạy + chính bạn tự đọc lại. Đây là công cụ hỗ trợ, không thay việc học.

## commands (máy đọc)

```yaml
commands: ["/learn", "/review", "/resume", "/status", "/schedule", "/ask", "/source",
           "/collect", "/curriculum", "/next-lesson", "/grade",
           "/test", "/gaps", "/skip", "/again", "/hard", "/good", "/easy",
           "/done", "/system", "/forget", "/fix", "/validate"]
```
