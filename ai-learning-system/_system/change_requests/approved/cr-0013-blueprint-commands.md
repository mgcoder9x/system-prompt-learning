# CR-0013 — Lệnh blueprint (build/edit/approve/amend) + curriculum nhận `area_refs`

```yaml
id: cr-0013
title: "Đăng ký lệnh blueprint vào registry/router + curriculum nhận area_refs"
status: approved
date_opened: 2026-07-07
date_decided: 2026-07-07
version_bump: null   # thêm lệnh, không đổi schema-version
related: [spec mandatory-curriculum-framework R2/R4/R5/R7, CR-0011, CR-0012, CR-0008 (tiền lệ đăng ký lệnh)]
recommendation: "Thêm 1 lệnh blueprint (đa chế độ qua cờ) + curriculum nhận area_refs; drift-guard registry↔CLI↔router"
```

## 1. Ghi yêu cầu (§12 bước 1)

Cần năng lực: dựng blueprint (draft), sửa blueprint draft, duyệt (draft→approved), sửa approved có kiểm
soát; và curriculum phải khai được `area_refs` cho từng point.

## 2. Phân tích (§12 bước 2)

- Theo tiền lệ DEC-063/069 (`--check`, `--insert-at`): dùng MỘT tên lệnh `blueprint` + các cờ chế độ
  (`--edit`, `--approve`, `--amend --confirm`) thay vì nhiều tên lệnh → giữ drift-guard bất biến.
- `area_refs` KHÔNG thêm lệnh riêng — mở rộng `cmd_curriculum`/`cmd_curriculum_insert` nhận `area_refs` trong
  JSON điểm học (tránh ceremony).
- Đăng ký đồng bộ 5 nơi: `CLI_COMMANDS`, parser, dispatch, `commands.md` (bảng + backends), `router_prompt.md`
  — 3 drift-guard (`test_commands_registry`, `test_router_prompt_consistency`, ...) phải XANH.

## 3. Đề xuất (§12 bước 3)

Tên hiển thị đề xuất: `/blueprint` (backend `blueprint`) với cờ `--edit / --approve / --amend / --confirm`.
Kiểm blueprint gộp vào `/validate` (read-only, như curriculum `--check` DEC-063) — KHÔNG thêm lệnh riêng.

## 4. Rủi ro (§12 bước 4)

Thấp–trung. Rủi ro: drift registry↔CLI↔router → 3 drift-guard bắt. Cờ `--confirm` phải bắt buộc cho amend
approved (nếu lỏng → phá R4.3).

## 5. Đề xuất (§12 bước 5)

Áp theo Task 5 + Task 6 (tasks.md), sau khi validator (Task 3/4) xanh. RED-first mỗi hành vi lệnh.

## 6. Quyết định (§12 bước 6–7)

`pending` — chờ owner "Duyệt". Khi duyệt: áp + changelog + ghi DEC.
