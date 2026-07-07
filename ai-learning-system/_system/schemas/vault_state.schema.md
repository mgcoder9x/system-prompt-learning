# Schema — `vault_state` (spec 5.4)

> **Chân lý schema ở `validator/models.py` (class `VaultState`, strict).** File mô tả + hợp đồng máy-đọc
> `schema_fields`; test giữ khớp CHÍNH XÁC với model. Đổi model mà quên cập nhật đây → test đỏ.

Con trỏ toàn vault + chính sách ngày. `schema: vault_state`. `strict=True, extra="forbid"`.

## Field (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"vault_state"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema |
| `utc_offset` | ✓ | str | offset địa phương, mẫu `^[+-]\d{2}:\d{2}$` (vd `+07:00`) |
| `date_policy` | – | enum | chỉ `"local_date"` (spec §5.4 — giá trị duy nhất; mặc định `"local_date"`) |
| `day_cutoff_hour` | – | int `0..23` | mốc cắt ngày (mặc định `4`); dùng cho `logical_today` khi lọc review |
| `current_topic` | – | str\|null | topic đang mở |
| `current_lesson` | – | str\|null | lesson đang mở |
| `export_policy` | – | enum | `private_full\|shareable_clean\|template_only` (mặc định `private_full`) |
| `open_session` | – | OpenSession | `{lesson_id?, started_at?, last_full_validate?}` (đều optional) |

Ràng buộc cứng (model): `utc_offset` đúng mẫu `[+-]HH:MM`; `day_cutoff_hour` trong `0..23`.

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: VaultState
  document_key: vault_state
  required: [schema, schema_version, utc_offset]
  optional: [date_policy, day_cutoff_hour, current_topic, current_lesson, export_policy, open_session]
```
