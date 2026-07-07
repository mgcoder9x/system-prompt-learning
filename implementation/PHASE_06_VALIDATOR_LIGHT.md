# P06 — Validator LIGHT (cú pháp/schema/file đơn)

**Mục tiêu:** `validate.py --level light` — kiểm nhanh cục bộ trong phiên học, không đụng liên-file (spec 10.8).
**Phụ thuộc:** P03 (models), P04a (AST-core cho lesson.md), P05 (IO).
**Giai đoạn MVP:** GĐ1.

## Xây gì

`_system/validator/validate.py` (CLI khung + LIGHT):

- CLI: `validate.py --system <p> --vault <p> [--level light|full] [--json]` (spec 10.1). Mặc định `full`.
- LIGHT theo loại file (spec 10.8):
  - `*_state.md`: parse front-matter → `normalize_yaml_object` → pydantic model của file đó (INV-01/05 mức file); KHÔNG ref chéo, KHÔNG replay, KHÔNG regen view.
  - `lesson.md`: AST — có `## Mục tiêu`, `## Sessions`; `#### Question <qid>` không trùng; evidence block đúng cú pháp (heading cấp 4 + fenced yaml có đủ **`axis`/`timestamp`/`quote`/`ai_assessment`**, spec 5.5); `evidence id` không trùng; scan abspath.
  - `_scratch/`: chỉ scan abspath.
- Report JSON + bảng người đọc; exit 0/1; gom mọi lỗi (không dừng ở lỗi đầu).

## INV/mục spec liên quan

10.8 (định nghĩa LIGHT), 10.1 (CLI), một phần INV-01/05/16 ở mức file.

## Cách test (`_system/validator/tests/phase06_light/`)

```text
[ ] valid/ lesson.md + lesson_state.md hợp lệ → LIGHT PASS (exit 0).
[ ] invalid/E-SCHEMA__*.md (từ P03) → LIGHT bắt đúng.
[ ] invalid/dup_qid.md : 2 #### Question q1 → lỗi.
[ ] invalid/bad_evidence_block.md : #### Evidence thiếu fenced yaml → lỗi cấu trúc.
[ ] invalid/evidence_missing_field.md : evidence yaml thiếu ai_assessment → LIGHT bắt (đủ 4 field cấu trúc).
[ ] invalid/abspath_in_lesson.md → E-PORT-ABSPATH.
[ ] LIGHT KHÔNG chạy replay/hash: 1 vault có view stale nhưng LIGHT vẫn PASS (chứng minh phạm vi hẹp).
[ ] --json xuất đúng schema {error_code,file,field,message} + warnings.
```

## Cạm bẫy

- LIGHT phải **thật sự nhẹ**: không được lỡ chạy ref chéo/replay (sẽ chậm + phá mục tiêu UX phiên học).
- Report phải máy-đọc-được (JSON) để agent dán nguyên văn (spec 10.1/10.5).
