# P10 — Tầng Agent (Prompts, Commands, Rules)

**Mục tiêu:** viết các tạo tác prompt để một phiên AI vận hành hệ thống: routing, lệnh, dạy, chấm — luôn gọi validator.
**Phụ thuộc:** P06 + P07a/P07b (validator chạy được), P08 (transaction), P09 (views).
**Giai đoạn MVP:** xuyên suốt (dùng được từ cuối GĐ1, hoàn thiện ở GĐ2).

## Xây gì (`_system/prompts/` + `_system/rules/` + `_system/commands.md`)

- `system_prompt.md` — chép/khớp khung spec mục 18 (kiến trúc, phân lớp, routing, ghi transaction, boot sequence, draft, dạy, ôn).
- `router_prompt.md` — phân loại intent (spec 11) + map lệnh → intent + phạm vi ghi.
- `system_change_prompt.md` — quy trình change request + conflict check (spec 12).
- `commands.md` — registry đầy đủ 14 lệnh (spec 11A.2): cú pháp, intent, phạm vi ghi, cần xác nhận không, LIGHT/FULL.
- `rules/review_rules.md` — bảng grade 0..3 → rating 1..4 (spec 8.1) + tham chiếu fsrs_config.
- `rules/teaching_rules.md` — rubric 5 trục + **≥3 ví dụ neo/trục** (spec 9.5 calibration) + learned_gate (9.3).
- `rules/{validation,memory,anti_drift,claim}_rules.md` — trỏ về INV/mục tương ứng.

## INV/mục spec liên quan

11 (routing), 11A (commands), 11B/11B.1/11B.2 (daily/boot/open_session), 8.1, 9.2/9.3/9.5, 12, 13, 14, 18.

## Cách test (kịch bản, không phải pytest — "walkthrough gate")

```text
[ ] /learn Docker: hỏi ≤3 câu → tạo topic+lesson-001 → transaction PASS (validator xanh) → vào lesson.
[ ] Phiên học: hỏi 1 câu/lượt; ghi lesson.md ở LIGHT; không validate nặng giữa chừng.
[ ] /done: chấm rubric + evidence verbatim → learned_gate → regen view → FULL validate → dán report PASS.
[ ] /review: lấy item tới hạn theo 8.5 (Review dùng due_date, Learning dùng due_at_utc) → chấm → FULL cho item đổi FSRS.
[ ] /status sau khi bỏ /done: cảnh báo open_session chưa đóng (11B.2).
[ ] /resume: chỉ nạp *_state + lesson_notes + session gần nhất (boot sequence 11B.1).
[ ] /system: KHÔNG áp ngay → tạo change request.
[ ] AI thử tự nói "đã valid" mà chưa chạy validator → vi phạm luật (kiểm bằng review thủ công prompt).
[ ] STALE-CONTEXT: AI đọc file (hash A) vào context → user sửa tay file (hash B) → lệnh ghi phải truyền
    expected_read_hash=A vào transaction → BEGIN bắt lệch → `E-STALE-CONTEXT`, AI đọc lại + sinh lại, KHÔNG ghi đè bản B.
```

## Cạm bẫy

- Prompt phải ép AI **dán report validator nguyên văn** (spec 10.5); cấm tự nhận PASS.
- Rubric không có ví dụ neo → chấm lệch giữa phiên (spec 9.5); phải viết đủ ví dụ.
- Đây là tầng KHÔNG có "đúng tuyệt đối" — validator ở dưới mới là chốt chặn.
