# Schema — `sources` (spec 5.3)

> **Chân lý schema ở `validator/models.py` (class `Sources`, strict).** File mô tả + hợp đồng máy-đọc
> `schema_fields`; test giữ khớp CHÍNH XÁC với model. Đổi model mà quên cập nhật đây → test đỏ.

Danh mục nguồn của một topic + các anchor trích dẫn. `schema: sources`. `strict=True, extra="forbid"`.
Chỉ nguồn `status: confirmed` mới được làm anchor cho claim lớp B (INV-12/13).

## Field top-level (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"sources"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema |
| `topic_id` | ✓ | str | topic sở hữu |
| `sources` | – | list[Source] | danh sách nguồn (mặc định `[]`); id không trùng (INV-04) |

### `Source` (phần tử của `sources`)

| Field | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `id` | ✓ | str `^src-\S+$` | id nguồn |
| `kind` | ✓ | enum | `doc\|link\|repo\|book\|note\|question` |
| `ref` | ✓ | str | tham chiếu (đường dẫn/URL/mô tả) |
| `status` | ✓ | enum | `raw\|processing\|confirmed\|rejected` |
| `trust` | – | enum | `unknown\|low\|medium\|high` (mặc định `unknown`) |
| `scope` | – | str | phạm vi (mặc định `""`) |
| `added` | – | date\|null | ngày thêm |
| `anchors` | – | list[SourceAnchor] | `{id, locator="", quote, summary="", content_hash?}` |

Ràng buộc cứng (model): `sources[].id` duy nhất (INV-04); mỗi `id` khớp `^src-\S+$`; `anchor.quote` bắt buộc.

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: Sources
  document_key: sources
  required: [schema, schema_version, topic_id]
  optional: [sources]
```
