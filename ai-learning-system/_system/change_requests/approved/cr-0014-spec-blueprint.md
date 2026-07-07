# CR-0014 — Mở rộng spec gốc: Topic_Blueprint + Blueprint_Validator (v2.7 → v2.8)

```yaml
id: cr-0014
title: "Mở rộng PROMPT_LEARNING_SYSTEM.md §3.5: Topic_Blueprint + Blueprint_Validator + 7 mã E-BP-* + vòng đời approve"
status: approved
date_opened: 2026-07-07
date_decided: 2026-07-07
version_bump: "v2.7 -> v2.8"   # tài liệu spec; _system/VERSION giữ = 1 (schema dữ liệu additive)
related: [spec mandatory-curriculum-framework toàn bộ, CR-0009 (tiền lệ mở rộng spec v2.6→v2.7), CR-0011..0013]
recommendation: "Áp SAU khi code XANH (spec phản ánh cái kiểm-được, không hứa trước — tiền lệ CR-0009 §5)"
```

## 1. Ghi yêu cầu (§12 bước 1)

Spec gốc hiện (v2.7) mô tả Curriculum + Curriculum_Validator nhưng CHƯA có khái niệm khung bắt buộc. Cần mở
rộng §3.5 để spec phản ánh tầng Topic_Blueprint đã hiện thực.

## 2. Phân tích (§12 bước 2)

- Chỉ THÊM khái niệm (tương thích ngược): Topic_Blueprint (Mandatory_Area, status draft/approved),
  Blueprint_Validator (7 mã E-BP-*), quan hệ phủ (Coverage_Map qua curriculum.area_refs), vòng đời approve.
- KHÔNG bump `_system/VERSION` (schema dữ liệu blueprint schema_version=1 additive, không migration — tách
  semver tài liệu vs schema dữ liệu, DEV-004/DEV-006).
- Áp SAU khi toàn bộ code + test XANH (spec phản ánh hành vi kiểm-được — tiền lệ CR-0009).

## 3. Đề xuất (§12 bước 3)

Mở rộng §3.5: định nghĩa Topic_Blueprint + Mandatory_Area + Blueprint_Status; Blueprint_Validator + 7 mã
(`E-BP-DUP-ID/EMPTY-TITLE/ORDER/AREA-UNCOVERED/AREA-REF-BROKEN/POINT-OUTSIDE/REF-BROKEN`); quy tắc phủ
approved-gated; vòng đời draft→approved→amend. Cập nhật tiêu đề spec v2.7→v2.8.

## 4. Rủi ro (§12 bước 4)

Thấp. Thuần tài liệu spec (không code). Rủi ro: prose lệch code → giữ nguyên tắc "áp sau khi code xanh" để
spec khớp hành vi thật.

## 5. Đề xuất (§12 bước 5)

Áp theo Task 8 (tasks.md), CUỐI cùng, sau khi Task 1–7 xanh.

## 6. Quyết định (§12 bước 6–7)

`pending` — chờ owner "Duyệt". Khi duyệt: áp + changelog + ghi DEC.
