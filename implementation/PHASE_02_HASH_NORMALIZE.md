# P02 — Canonical Hash & Chuẩn Hoá

**Mục tiêu:** cung cấp hàm băm tất định + chuẩn hoá dữ liệu, để view-hash (INV-09) và verbatim-check (INV-22b) không lệch giữa máy.
**Phụ thuộc:** P00.
**Giai đoạn MVP:** GĐ1 (hash + normalize_yaml_object) + GĐ2 (normalize_for_match).

## Ranh giới trách nhiệm (chốt để không đá nhau với P03 strict)

- **`normalize_yaml_object`** chạy **trước pydantic**, GIỮ NGUYÊN type đúng theo schema (date vẫn là `date`, datetime-canonical vẫn là `str` vì file quote sẵn) — KHÔNG stringify. Nó chỉ hoà giải "bất ngờ implicit typing" của YAML để pydantic strict không vấp (xem dưới).
- **`canonical_hash`** stringify `date`→`"YYYY-MM-DD"` / datetime→UTC-canonical **chỉ ngay trước khi dump JSON** (qua `_to_jsonable`), KHÔNG đụng object dùng cho pydantic.
- ⇒ pydantic thấy **typed object** (strict OK), hash thấy **string** (tất định). Hết mâu thuẫn "date vs YYYY-MM-DD".

## Xây gì

`_system/validator/canonical.py` — thuần hàm:

- `canonical_hash(data)->str` — spec 4:
  `sha256(json.dumps(_to_jsonable(data), sort_keys=True, separators=(',',':'), ensure_ascii=False).encode('utf-8')).hexdigest()`.
  `_to_jsonable`: `date`→`isoformat()"YYYY-MM-DD"`; datetime→UTC-canonical `YYYY-MM-DDTHH:MM:SSZ`; float→**cấm** (miền băm không có float, spec 4) → raise nếu gặp float thô.
- `normalize_yaml_object(raw:dict, schema)->dict` — spec 16.1/19, **dùng cho front-matter VÀ mọi fenced YAML** (claims, evidence, sources anchors):
  hoà giải output YAML implicit typing về đúng type schema mà KHÔNG lossy-coerce: giữ `date` là `date`;
  giá trị bị YAML ép bool ngoài ý muốn (`yes/no/on/off`) khi schema muốn str → giữ nguyên giá trị gốc/để pydantic strict báo lỗi;
  KHÔNG tự ép `"2"`→`2`. Scalar sai kiểu → để pydantic strict bắt.
- `normalize_for_match(s:str)->str` — spec 9.6 (dùng ở INV-22b):
  1. Unicode **NFC**. 2. Nháy/gạch: `" " „ ‟ → "`, `' ' → '`, `– — → -`.
  3. Strip Markdown inline delimiter (**bold/italic/code-span**) bằng **markdown-it-py inline parse → lấy text token**
     (KHÔNG regex xoá `*`/`_` bừa, giữ `__init__`, `C++`, `a_b`). 4. Gộp whitespace → 1 space, trim.
  **KHÔNG** lowercase, **KHÔNG** bỏ dấu câu, **KHÔNG** bỏ dấu tiếng Việt.

## INV/mục spec liên quan

4 (canonical JSON, miền băm), 9.6 (normalize_for_match), INV-09, INV-22b. `normalize_yaml_object` phục vụ P03/P04/P07.

## Cách test (`_system/validator/tests/phase02_hash/`)

```text
[ ] canonical_hash ổn định: cùng object → cùng hash qua 100 lần / 2 tiến trình.
[ ] Tiếng Việt: object chứa "đ" → hash KHÔNG đổi khi ensure_ascii=False; khác hash nếu lỡ để ensure_ascii=True (test chốt).
[ ] Thứ tự key khác nhau, cùng nội dung → cùng hash (sort_keys).
[ ] _to_jsonable: date obj và "YYYY-MM-DD" string cho cùng hash; gặp float thô → raise.
[ ] normalize_yaml_object: front-matter `created: 2026-06-30`(date) giữ là date; `flag: yes` không tự thành True nếu schema muốn str.
[ ] normalize_yaml_object áp cho evidence yaml: `timestamp: 2026-06-30`(date) giữ đúng type trước pydantic.
[ ] normalize_for_match MATCH: "chia sẻ **kernel**" ⊆ "chia sẻ kernel"; nháy cong “abc”↔"abc"; nhiều space↔1 space.
[ ] normalize_for_match KHÔNG match sai: "má" ≠ "ma" (giữ dấu); "a_b" giữ nguyên.
```

## Cạm bẫy

- Đừng hash **text file thô** (dễ false-stale do khoảng trắng/comment) — chỉ hash **object đã normalize** đúng miền băm (spec 4).
- normalize_for_match quá tay (lowercase/bỏ dấu) sẽ **mở lại lỗ bịa** mà INV-22b cần bịt (spec 9.6) — chỉ tha khác biệt hình thức.
- Stringify date **chỉ ở `canonical_hash`**, đừng stringify sớm làm pydantic strict (P03) reject.
