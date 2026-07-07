# Schema — `blueprint` (tính năng mandatory-curriculum-framework, CR-0011)

> **Chân lý schema nằm ở `validator/models.py` (class `Blueprint`, strict).** File này là bản mô tả
> người-đọc + hợp đồng máy-đọc `schema_fields`, được test `phase10/test_schemas_consistency.py` giữ
> khớp CHÍNH XÁC tập field của model. Đổi model mà quên cập nhật đây → test đỏ.

Front-matter có cấu trúc của `topics/<topic>/blueprint.md` — **khung giáo trình bắt buộc** (Topic_Blueprint):
danh sách Mandatory_Area (mảng kiến thức bắt buộc) sắp theo lộ trình zero→chuyên-gia, cùng trạng thái vòng
đời. `schema: blueprint`. `strict=True, extra="forbid"`: sai kiểu/enum hoặc field lạ → `E-SCHEMA`.

Ràng buộc CẤU TRÚC (model, → E-SCHEMA): `updated ≥ created`; `area.id` khớp `^ma-\S+$`; `order ≥ 1`;
`status ∈ {draft, approved}`; `mandatory` là bool. Ràng buộc NGỮ NGHĨA (Blueprint_Validator, mã riêng —
Task 3/4): `id` duy nhất (`E-BP-DUP-ID`), `order` hoán vị 1..N (`E-BP-ORDER`), `title` không rỗng
(`E-BP-EMPTY-TITLE`), `source_refs` trỏ file reference tồn tại (`E-BP-REF-BROKEN`), và (quan hệ với
curriculum) phủ đủ khi approved (`E-BP-AREA-UNCOVERED`), ánh xạ point→area tồn tại (`E-BP-AREA-REF-BROKEN`),
không điểm-ngoài-khung khi approved (`E-BP-POINT-OUTSIDE`).

## Field (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"blueprint"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema (INV-19) |
| `topic_id` | ✓ | str | topic sở hữu khung |
| `status` | ✓ | literal `draft`\|`approved` | vòng đời: draft (sửa được) / approved (chuẩn ràng buộc) |
| `created` | ✓ | date | ngày tạo |
| `updated` | ✓ | date | ngày cập nhật; **≥ `created`** |
| `areas` | – | list[MandatoryArea] | `{id: ma-*, order:int≥1, title, mandatory:bool, source_refs[]}` (mặc định `[]`) |

`MandatoryArea` (nested): `id`(ma-*), `order`(int≥1), `title`(str, Blueprint_Validator ép không rỗng),
`mandatory`(bool), `source_refs`(list[str], đường dẫn tương đối trong `reference/`).

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: Blueprint
  document_key: blueprint
  required: [schema, schema_version, topic_id, status, created, updated]
  optional: [areas]
```
