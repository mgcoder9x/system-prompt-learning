# CR-0012 — Mở rộng schema `curriculum`: thêm `CurriculumPoint.area_refs` (Coverage_Map)

```yaml
id: cr-0012
title: "Thêm field CurriculumPoint.area_refs (ánh xạ điểm học → Mandatory_Area) — Coverage_Map"
status: pending
date_opened: 2026-07-07
date_decided: null
version_bump: null   # additive optional field, default []; schema_version curriculum giữ = 1
related: [spec mandatory-curriculum-framework R3/R5, CR-0011 (blueprint schema), CR-0007 (curriculum schema gốc)]
recommendation: "THÊM area_refs: list[str] = [] vào CurriculumPoint (tương thích ngược tuyệt đối)"
```

## 1. Ghi yêu cầu (§12 bước 1)

Cần biểu diễn quan hệ **phủ**: mỗi `Curriculum_Point` có thể ánh xạ tới một/nhiều `Mandatory_Area` của
blueprint. Coverage_Map = tập id area mà các point phủ.

## 2. Phân tích (§12 bước 2)

- QĐ-1 (design.md): đặt mapping ở phía **curriculum** (bên editable) chứ không phải blueprint (bên khóa khi
  approved — R4.3). Nếu để ở blueprint thì mỗi lần sửa curriculum phải sửa blueprint approved → xung đột.
- `CurriculumPoint` hiện có: `id, order, objective, status, lesson_id, source_refs` (đã đọc models.py:297).
  Thêm `area_refs: list[str] = []`. Default `[]` → curriculum cũ đọc vẫn hợp lệ (model strict extra=forbid
  nhưng field MỚI có default → không phá parse file cũ; file cũ không có key này vẫn OK).
- Ràng buộc "area_refs trỏ area tồn tại" là NGỮ NGHĨA → Blueprint_Validator (`E-BP-AREA-REF-BROKEN`), không
  nhét vào model (giữ mã lỗi phân biệt, cùng triết lý CurriculumPoint).

## 3. Đề xuất schema (§12 bước 3)

`CurriculumPoint.area_refs: list[str] = []`. Cập nhật `schemas/curriculum.schema.md` (thêm `area_refs` vào
mô tả CurriculumPoint) + drift-guard `test_schemas_consistency.py` giữ khớp.

## 4. Rủi ro (§12 bước 4)

Thấp–TRUNG (đụng tính năng curriculum-driven-learning ĐÃ HOÀN TẤT). Giảm thiểu: field optional default `[]`;
RED-first ca mới; chạy TOÀN BỘ suite curriculum cũ sau khi thêm để khẳng định 0 hồi quy.

## 5. Đề xuất (§12 bước 5)

Áp theo Task 2.2 (cùng lúc thêm model blueprint). RED-first drift-guard.

## 6. Quyết định (§12 bước 6–7)

`pending` — chờ owner "Duyệt". Khi duyệt: áp + changelog + ghi DEC.
