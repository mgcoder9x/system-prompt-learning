# Review Rules — Ánh xạ chấm điểm & nhịp ôn (spec 8.1, 8.4, 8.5)

Nguồn sự thật cho **cách chấm một lượt ôn**. Đổi bảng này PHẢI qua change request (spec 12).
Bảng máy-đọc-được dưới đây được validator/test kiểm khớp với hằng số code
`fsrs_adapter.MAP_GRADE_TO_RATING` (chống trôi docs↔code).

## Ánh xạ grade → rating (spec 8.1)

Người chấm dùng rubric rời rạc `0..3` (quan sát được); hệ thống ánh xạ **cố định** sang FSRS rating `1..4`:

| grade | Ý nghĩa | rating FSRS |
|---|---|---|
| 0 | Quên / sai bản chất | 1 = Again |
| 1 | Nhớ mơ hồ / sai một phần | 2 = Hard |
| 2 | Đúng nhưng chưa trôi chảy | 3 = Good |
| 3 | Đúng, trôi chảy, tự giải thích | 4 = Easy |

### grade_to_rating (máy đọc)

```yaml
grade_to_rating:
  0: 1   # Again
  1: 2   # Hard
  2: 3   # Good
  3: 4   # Easy
```

`grade` ngoài `0..3` → `E-REVIEW-BADGRADE` (không tạo transaction).

## Nhịp ôn (spec 8.5)

- **"Cần ôn hôm nay"** = mọi item tới hạn, kể cả `mastered`, sắp theo `priority(mastery_state)` rồi
  `(due_date asc, due_at_utc asc, lesson_id asc, item_id asc)`. `priority`: `need_redo=0 < in_review=1 < mastered=2`.
- Item `Learning/Relearning` tới hạn theo `due_at_utc <= now_utc`; `Review` theo `due_date <= logical_today`.
- `logical_today = (now_local - day_cutoff_hour giờ).date()` (mặc định cutoff 4h). Chỉ áp cho lọc review-card,
  KHÔNG áp cho `created/updated` (dùng ngày lịch thật, giữ INV-05).
- `/skip`: không gọi review, không ghi log, giữ nguyên card.
- Mỗi `prompt_ref` chỉ một review item (`E-REVIEW-DUP`).

## Chấm một lượt (spec 8.4)

`rating = grade_to_rating[grade]` → replay toàn bộ `log` từ card `Learning`/log rỗng tại `created`
(py-fsrs không có `New`, v2.6/F-A) → cập nhật `card` + append `log` → `mastery_state = derive_mastery(card, log)`.
Mọi datetime vào FSRS phải là UTC-aware; `reviewed_at` lưu ở offset địa phương để audit.


## Ghi buổi ôn tập (CR-0006)

Mỗi buổi ÔN = thêm một block `### Session <ngày> — ôn tập` vào `lesson.md › ## Sessions`:
`#### Question <qid>` / `#### Bạn trả lời <qid>` / `#### AI phản hồi` (+ `#### Evidence ev-*` nếu có chấm rubric).
**KHÔNG tạo file .md riêng mỗi buổi ôn** — tránh trùng lặp + xung đột INV-25; `/resume` và `/status` đọc
section `## Sessions` buổi GẦN NHẤT (spec §14). Nhịp: hỏi MỘT câu/lượt; tương tác xong câu 1 mới sang câu 2.
`/review` (CLI) lo chấm FSRS + lịch; transcript hỏi-đáp của buổi ôn ghi ở `## Sessions`.
