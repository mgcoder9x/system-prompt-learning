# P12 — Pilot End-to-End & Kiểm Chéo Đa Phiên

**Mục tiêu:** chứng minh cả hệ thống vận hành thật trên một topic nhỏ, và một phiên AI khác tiếp quản đúng trạng thái (spec 20.12–13).
**Phụ thuộc:** tất cả các phase trước xanh.
**Giai đoạn MVP:** nghiệm thu cuối GĐ2.

## Xây gì / làm gì

1. Tạo vault thật: `learning_vault/` + `vault_state.md` (utc_offset "+07:00", day_cutoff_hour 4).
2. `/learn docker` → topic `docker`, `lesson-001` "Container là gì" (theo template 14A).
3. Chạy trọn nhịp hằng ngày (spec 11B): `/status → /learn → (học hỏi-đáp) → /done`.
4. Buổi 2: `/status → /review → /resume → /done` (có item FSRS tới hạn).
5. Đưa nguồn: `/source <link>` → xử lý tới `confirmed` → nâng 1 claim draft→confirmed vào `## Knowledge Map`.
6. `/forget` thử một lesson rác → kiểm tombstone + INV-11 tha.

## Nghiệm thu (Definition of Done)

```text
[ ] Sau mỗi lệnh ghi: validate.py FULL (hoặc LIGHT trong phiên) → PASS, report dán nguyên văn.
[ ] Đóng "phiên AI 1". Mở "phiên AI 2" (model/context mới) chỉ đọc _system/ + learning_vault/:
    - Đọc đúng vault_state → biết đang ở đâu.
    - /status ra đúng: topic/lesson hiện tại, số câu tới hạn, cảnh báo open_session nếu có.
    - Tiếp tục /resume đúng next_action mà KHÔNG hỏi lại từ đầu.  ← đây là bài test "stateless handoff".
[ ] Copy learning_vault/ sang thư mục khác (giả lập máy khác); trên máy đó `uv sync --frozen` (dựng env từ lock)
    rồi `python validate.py --system _system --vault learning_vault --level full` → vẫn PASS
    (chứng minh portability + không đường dẫn tuyệt đối, INV-16).
[ ] Chạy validate 2 lần liên tiếp không sửa gì → report giống hệt (deterministic).
[ ] Cố tình làm hỏng 1 thứ: sửa tay `due_date` của 1 review item (hoặc `stability`) → FULL bắt đúng `E-REVIEW-MISCALC`.
    (LƯU Ý v2.6/F-B: sửa `due_at_utc` của thẻ `Review` KHÔNG bị bắt — nó không nằm trong so khớp; phải sửa `due_date`/`stability`/`last_reviewed_at_utc` để test đúng.)
```

## Cạm bẫy

- Đây là lúc lộ ra các giả định ngầm chưa test ở phase đơn lẻ (vd tương tác day_cutoff × review × created).
- Nếu handoff phiên-2 phải hỏi lại → nghĩa là trạng thái chưa đủ "self-describing"; quay lại bổ sung `next_action`/notes, KHÔNG vá bằng cách cho AI đoán.
- Ghi lại mọi lỗi phát sinh thành golden fixture mới cho P07a/P07b (regression), rồi mới sửa.
