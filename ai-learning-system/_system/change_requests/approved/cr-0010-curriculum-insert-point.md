# CR-0010 — Chèn điểm học giữa chừng giáo trình (R8)

```yaml
id: cr-0010
title: "Thêm chế độ /curriculum --insert-at <pos> --point <json>: chèn Curriculum_Point giữa chừng"
status: approved
date_opened: 2026-07-06
date_decided: 2026-07-06
version_bump: null
related: [spec curriculum-driven-learning R8, CR-0008 (5 lệnh), CR-0009 (spec v2.7 §3.5), DEC-063 (--check là cờ trên /curriculum)]
recommendation: "THÊM cờ --insert-at + --point trên backend /curriculum (KHÔNG thêm tên lệnh mới → drift-guard bất biến, đúng tiền lệ --check). Backend cmd_curriculum_insert riêng; dispatch route theo cờ. RED-first."
```

## 1. Ghi yêu cầu (§12 bước 1)

R8 (đã duyệt trong requirements): người học đang học một giáo trình, thấy thiếu → muốn **chèn một điểm học vào vị trí xác định** mà KHÔNG dựng lại từ đầu, giữ nguyên id/tiến độ điểm cũ.

## 2. Phân tích (§12 bước 2)

- Chèn là thao tác GHI cấu trúc `curriculum.md` → phải qua Write_Transaction-FULL (validator gate E-CURR-*), như `cmd_curriculum`.
- KHÔNG thêm tên lệnh mới: dùng **cờ** `--insert-at <pos>` + `--point <json 1 object>` trên backend `/curriculum` (đúng tiền lệ `/schedule --days`, `/curriculum --check` gộp — DEC-063). Dispatch: có `--insert-at` → `cmd_curriculum_insert`; không → `cmd_curriculum` (build). Drift-guard (CLI_COMMANDS↔commands.md↔router) KHÔNG đổi vì tên lệnh `/curriculum` giữ nguyên.
- Ngữ nghĩa (R8.1/3/4/7): chèn tại `pos` (1..N+1), point mới nhận `order=pos`, các point `order>=pos` dịch +1 (giữ hoán vị 1..N+1 cho E-CURR-ORDER); id mới = `cp-{max_suffix+1}` (duy nhất, ổn định — KHÔNG tái dùng số theo order); `current_point` (tham chiếu id) + status các point cũ GIỮ NGUYÊN; vị trí ngoài [1..N+1] hoặc curriculum chưa tồn tại → từ chối.
- R8.2/8.5/8.6: transaction-FULL tự re-validate toàn curriculum (E-CURR-*); cấu trúc sai → ABORT rollback (R8.5). "Đủ sâu/rộng" là Class D (không mã máy) — nhất quán ranh giới hệ thống.

## 3. Conflict check (§12 bước 3)

Không trùng tên lệnh. Không đổi schema (point mới dùng cùng schema `curriculum`, schema_version giữ 1). Tương thích ngược: giáo trình không dùng chế độ chèn không đổi gì.

## 4. Rủi ro (§12 bước 4)

Thấp–trung. Rủi ro: renumber order sai → E-CURR-ORDER (transaction gate bắt, rollback). RED-first bắt buộc cho renumber + id-unique + reject vị-trí-xấu.

## 5. Đề xuất (§12 bước 5)

Thêm `cmd_curriculum_insert` + 2 cờ parser + nhánh dispatch, RED-first. Cập nhật `commands.md` (chú thích chế độ chèn trên dòng `/curriculum`) + `HUONG_DAN.md` + spec §3.5 (một câu về chèn giữa chừng). Changelog CR-0010 khi áp xong. Ghi DEC.

## 6. Quyết định (§12 bước 6–7) — ĐÃ DUYỆT

`approved` 2026-07-06 (owner qua tín hiệu "duyệt theo khuyến nghị từng bước"). Triển khai RED-first: cờ `--insert-at`+`--point` trên `/curriculum`, backend `cmd_curriculum_insert`, dispatch route theo cờ. Changelog + HUONG_DAN + spec §3.5 khi áp xong. Ghi DEC-069.
