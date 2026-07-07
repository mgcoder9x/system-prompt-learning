# P11 — Tối Ưu Hiệu Năng & Migration (GĐ3)

**Mục tiêu:** tăng tốc FULL-validate khi vault lớn + đường di trú version — KHÔNG đổi tiêu chí đúng/sai.
**Phụ thuộc:** P07a+P07b (FULL), P08 (transaction).
**Giai đoạn MVP:** GĐ3 (có thể hoãn nếu vault còn nhỏ).

## Xây gì

- `_system/validator/cache.py` (spec 10.9a) — **cache replay phi-thẩm-quyền**:
  key = `sha256(fsrs_config_version + created + initial_card_or_null + canonical_json(log))`, value = card replay.
  (Phải gồm `created` — vì log rỗng thì card New phụ thuộc `created`; và `initial_card` — vì item import replay từ baseline seed, spec 8.5.)
  Đặt ở `_system/.cache/` (validator bỏ qua như `.tx`, INV-20). **KHÔNG** lưu snapshot trong `lesson_state.md`.
  Mất cache → chỉ chậm, không sai (luôn tái dựng từ New/initial_card + log).
- `_system/validator/diff.py` (spec 10.9b) — **validate vi sai**:
  đồ thị phụ thuộc lesson↔prereq↔topic_state; FULL chỉ chạy trên tập bị ảnh hưởng.
  FULL toàn vault ở mốc lớn: `/validate`, trước Git commit, khi đổi VERSION/fsrs_config_version.
- `_system/migrations/vN_to_vN+1.py` (spec 10.3b/10.7) — migration **trong transaction-FULL**:
  BEGIN backup toàn vault → STAGE biến đổi → REGEN → VALIDATE bằng schema **version đích** → PASS commit + tăng `schema_version`, FAIL abort giữ nguyên.

## INV/mục spec liên quan

10.7 (migration), 10.9a (cache), 10.9b (vi sai), INV-19 (semver), 10.3b.

## Cách test (`_system/validator/tests/phase11/`)

```text
[ ] Cache hit == full replay: với log không đổi, kết quả cache trùng replay từ New (byte-for-byte card).
[ ] Cache invalidate: thêm 1 lượt vào log → key đổi → replay lại, không dùng card cũ.
[ ] Xoá sạch _system/.cache → FULL vẫn PASS (chỉ chậm) → chứng minh cache phi-thẩm-quyền.
[ ] Validate vi sai == FULL toàn vault trên tập bị ảnh hưởng (so report trùng nhau).
[ ] Thiếu 1 file phụ thuộc trong đồ thị → vi sai phải mở rộng phạm vi, không bỏ sót (test dựng ca này).
[ ] Migration PASS: v1→v2 fixture → vault đổi + schema_version=2 + validate version đích PASS.
[ ] Migration FAIL: biến đổi tạo dữ liệu sai → abort → vault v1 NGUYÊN VẸN (transaction rollback).
[ ] E-SCHEMA-OUTDATED (vault v1, system v2) và E-SCHEMA-AHEAD (vault v3, system v2) trả đúng.
```

## Cạm bẫy

- Cache là **phím tắt**, KHÔNG phải chân lý — validator không bao giờ tin cache thay cho replay khi nghi ngờ (spec 10.9a).
- Vi sai chỉ **thu hẹp phạm vi**, không đổi tiêu chí; tính sai tập ảnh hưởng = bỏ sót lỗi → khi nghi ngờ chạy FULL toàn vault.
- Migration KHÔNG được sửa file thật trực tiếp — phải qua transaction (spec 10.3b).
