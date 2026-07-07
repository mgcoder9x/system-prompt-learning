# CR-0002 — `/test` là lệnh CHỈ-ĐỌC (báo cáo cổng), không tự ghi `learned`

```yaml
id: cr-0002
title: "Đổi phạm vi /test: 'lesson_state.md (transaction)' → 'chỉ đọc (báo cáo learned_gate)'"
status: approved
date_opened: 2026-07-03
date_decided: 2026-07-03
version_bump: null            # không đổi schema, chỉ đổi annotation registry lệnh
related_decisions: [DEC-025]
```

## 1. Ghi yêu cầu (§12 bước 1)

`commands.md` ghi `/test [lesson] → lesson_state.md (transaction)`. Khi hiện thực backend, quyết định
làm `/test` **CHỈ ĐỌC** (báo cáo trục nào đạt/thiếu cổng learned_gate), KHÔNG tự đặt `status: learned`.

## 2. Phân tích — vấn đề giải quyết (§12 bước 2)

Người dùng cần biết "đã đủ điều kiện đánh dấu learned chưa" mà KHÔNG vô tình nâng trạng thái.

## 3. CONFLICT CHECK với `_system/rules/` (§12 bước 3)

- Không mâu thuẫn luật nào trong `rules/`.
- KHÔNG phá bất biến: `/test` read-only → không tạo transition → INV-06/07 không bị ảnh hưởng.
  Việc đặt `learned` vẫn phải qua transaction-FULL nơi INV-07/22 làm cổng thật (giữ nguyên).
- Trùng lặp: không.

## 4. Đánh giá rủi ro (§12 bước 4)

- Rủi ro của phương án CŨ (tự ghi learned): nâng `learned` dựa trên điểm rubric chủ quan (Class D, §0.3)
  như tác dụng phụ → dễ "đã hiểu" oan. Read-only loại rủi ro này.
- Read-only không giảm portability, không làm AI khó tiếp tục.

## 5. Đề xuất đã tinh chỉnh (§12 bước 5)

`/test [lesson]` = CHỈ ĐỌC: chạy `_check_gate_and_evidence` trên bản sao lesson (giả định `status=learned`)
→ báo `gate_pass` + chi tiết từng trục (score/threshold/meets) + danh sách lỗi chặn (E-GATE-FAIL/
E-ASSESS-NOEVIDENCE/E-ASSESS-FAKEQUOTE). KHÔNG ghi. Việc chuyển `learned` để luồng dạy + `/done` làm.

## 6. Quyết định (§12 bước 6–7)

`approved`. Áp: cập nhật `commands.md` (cột "Ghi vào đâu" của `/test` → "chỉ đọc"; backend `session.py test`)
+ ghi `changelog.md`. Không bump VERSION (không đổi schema).
