# CR-0008 — 5 lệnh mới cho vòng học theo giáo trình (registry + router)

```yaml
id: cr-0008
title: "Thêm lệnh: collect / curriculum (+ --check) / next-lesson / grade"
status: approved
date_opened: 2026-07-05
date_decided: 2026-07-05
version_bump: null
related: [spec curriculum-driven-learning R4/R6/R7/R9, DEC-055, CR-0007 (schema), DEC-058..061 (validator layer)]
recommendation: "THÊM lệnh vào commands.md + CLI_COMMANDS + parser + router_prompt; drift-guard giữ khớp. Triển khai INCREMENTAL, RED-first."
```

## 1. Ghi yêu cầu (§12 bước 1)

Cần lệnh để: (a) nạp lát cắt tài liệu vào `reference/`; (b) dựng giáo trình; (c) kiểm giáo trình; (d) sinh bài kế theo giáo trình; (e) chấm bài exam.

## 2. Phân tích (§12 bước 2)

`/learn` chỉ tạo lesson-001 (DEC-014). Vòng "giáo trình nhiều bài" cần các động từ mới, KHÔNG nhồi vào `/learn`. Tên lệnh (ĐÃ CHỐT khi duyệt):

| Lệnh (display) | Backend (identifier) | Mức TX | Vai trò |
|---|---|---|---|
| `/collect` | `session.py collect` | LIGHT | Ghi lát cắt tài liệu → `topics/<topic>/reference/<slug>.md` |
| `/curriculum` | `session.py curriculum` | FULL | Dựng `curriculum.md`; chỉ `teachable=true` khi Curriculum_Validator PASS |
| `/curriculum --check` | (cùng backend, cờ read-only) | read-only | In báo cáo PASS/FAIL giáo trình |
| `/next-lesson` | `session.py next_lesson` | FULL | Tạo `lesson-NNN` cho `current_point`; cập nhật `lessons[]` (INV-25) |
| `/grade` | `session.py grade` | LIGHT | Ghi entry `exam_results.md` |

## 3. Conflict check (§12 bước 3)

Tên không trùng lệnh hiện có. Quy ước: **display key có gạch nối** (`/next-lesson`) nhưng **backend là identifier gạch dưới** (`next_lesson`) để thoả drift-guard `hasattr(session, f"cmd_{name}")` (Python identifier). `curriculum --check` là CỜ trên cùng backend (như `/schedule --days`). Router + drift-guard `test_commands_registry`/`test_router_prompt_consistency` cập nhật đồng bộ mỗi lần thêm lệnh — nếu lệch → test đỏ.

## 4. Rủi ro (§12 bước 4)

Trung. Lệnh GHI phải qua Write_Transaction + validator (LIGHT trong phiên / FULL cho next-lesson vì đụng INV-25 index). `next-lesson` RED-first bắt buộc. `collect` KHÔNG tự-fetch mạng — AI (chat) lấy nội dung, backend ghi tất định (như cmd_learn/cmd_source).

## 5. Đề xuất (§12 bước 5)

Áp INCREMENTAL, RED-first, mỗi lệnh một increment: `collect` → `curriculum` (+--check) → `next-lesson` → `grade`. Registry (commands.md + router + CLI) cập nhật ĐỒNG BỘ mỗi lần thêm một lệnh (giữ drift-guard xanh liên tục). Changelog CR-0008 ghi khi ĐỦ 5 lệnh áp xong (Task 9).

## 6. Quyết định (§12 bước 6–7) — ĐÃ DUYỆT

`approved` 2026-07-05 (owner qua tín hiệu "duyệt theo khuyến nghị từng bước"). Tên lệnh giữ nguyên đề xuất (English, khớp quy ước HUONG_DAN). Triển khai bắt đầu từ `collect`. Changelog + cập nhật `HUONG_DAN.md` khi đủ 5 lệnh. Mỗi lệnh ghi DEC riêng.
