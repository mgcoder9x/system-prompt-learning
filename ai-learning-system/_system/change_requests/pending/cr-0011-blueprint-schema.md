# CR-0011 — Schema mới `blueprint` (Topic_Blueprint — khung giáo trình bắt buộc)

```yaml
id: cr-0011
title: "Thêm schema dữ liệu học blueprint (Topic_Blueprint: danh sách Mandatory_Area zero→chuyên-gia)"
status: pending
date_opened: 2026-07-07
date_decided: null
version_bump: null   # schema_version file mới = 1; KHÔNG đổi file cũ → không bump VERSION hệ
related: [spec mandatory-curriculum-framework R1/R6/R7, CR-0007 (tiền lệ schema), DEC-008 (drift-guard schema)]
recommendation: "THÊM schema blueprint qua model pydantic + schemas/blueprint.schema.md + drift-guard (đồng nhất cơ chế hiện có)"
```

## 1. Ghi yêu cầu (§12 bước 1)

Cần một artifact **khung sườn bắt buộc** máy-đọc cho mỗi topic: danh sách `Mandatory_Area` (mảng kiến thức
bắt buộc) sắp theo lộ trình zero→chuyên-gia, có trạng thái vòng đời (draft/approved). Là dữ liệu học →
thuộc `learning_vault/topics/<topic>/blueprint.md`.

## 2. Phân tích (§12 bước 2)

- Hệ chưa có khái niệm "mảng bắt buộc" — validator chỉ kiểm curriculum đúng cấu trúc, KHÔNG kiểm "phủ đủ
  mảng bắt buộc". Blueprint lấp đúng khoảng đó (Class A).
- Blueprint là artifact ĐỘC LẬP với curriculum; quan hệ phủ đặt ở phía curriculum (CR-0012 `area_refs`) để
  không khóa cứng khi blueprint approved (QĐ-1 design.md).
- Cùng cơ chế schema hiện có: model pydantic strict + `schemas/*.schema.md` + drift-guard (DEC-008).

## 3. Đề xuất schema (§12 bước 3)

**`blueprint` (`topics/<topic>/blueprint.md` front-matter):** `schema, schema_version=1, topic_id,
status∈{draft,approved}, areas[]{id(^ma-\S+$), order:int≥1, title(str), mandatory(bool), source_refs[](str,
đường dẫn tương đối trong reference/)}, created, updated(≥created)`.

Thêm: `schemas/blueprint.schema.md` (khối `schema_fields` máy-đọc) + model `Blueprint`+`MandatoryArea` trong
`models.py` + drift-guard test (`MODEL_BY_SCHEMA += 1`, như DEC-008). Đăng ký `blueprint` vào `_SCHEMA_MODELS`;
thêm `blueprint.md` vào `_SYSTEM_DATA_NAMES` (INV-18 — chống lạc vào `_system/`).

Ràng buộc CẤU TRÚC ở model (→ E-SCHEMA): id pattern, order≥1, status Literal, mandatory bool, updated≥created.
Ràng buộc NGỮ NGHĨA ở Blueprint_Validator (mã E-BP-* riêng — CR triển khai qua Task 3/4, không cần CR mã lỗi
vì là enforcement schema đã duyệt, tiền lệ DEC-034/058).

## 4. Rủi ro (§12 bước 4)

Thấp. Không đổi file/schema cũ → không hồi quy schema hiện có. Rủi ro chính: field lệch model↔schema.md →
drift-guard test bắt. Kiểm khi áp: `blueprint.md` thêm vào `_SYSTEM_DATA_NAMES` (INV-18).

## 5. Đề xuất (§12 bước 5)

Áp schema + drift-guard theo Task 2 (tasks.md). RED-first: viết test drift-guard đỏ trước, rồi thêm model.

## 6. Quyết định (§12 bước 6–7)

`pending` — chờ owner "Duyệt". Khi duyệt: áp Task 2, move approved + changelog + ghi DEC.
