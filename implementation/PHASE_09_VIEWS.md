# P09 — Sinh View (review_schedule / assessment / has_draft_knowledge)

**Mục tiêu:** sinh view tất định từ nguồn sự thật, đúng miền băm, để INV-09 kiểm được. Wire vào REGEN của transaction-FULL.
**Phụ thuộc:** P01 (mastery_state), P02 (canonical hash), P03 (models). `compute_has_draft_knowledge` thêm phụ thuộc **P04b** (count_draft_claims).
**Giai đoạn MVP:** **GĐ1**: `build_review_schedule` + `build_assessment` (chỉ cần mastery từ lesson_state, KHÔNG cần claim). **GĐ2**: `compute_has_draft_knowledge` (cần claim parser P04b).

## Xây gì

`_system/validator/views.py`:

- `build_review_schedule(topic)->dict` — **GĐ1** — spec 7: gom review_items, sắp `(due_date, due_at_utc, lesson_id, item_id)`;
  miền băm spec 4 (v2.6/F-B) = đúng 4 field `{lesson_id,item_id,due_date,mastery_state}` (KHÔNG có due_at_utc); `generated_from_hash=canonical_hash(data)`.
- `build_assessment(topic)->dict` — **GĐ1** — spec 4: chỉ lesson `status in {learned,needs_review}`; miền băm `{lesson_id,status,mastery{trục:score}}`; avg 5 trục làm tròn 1 chữ số.
- `compute_has_draft_knowledge(topic)->bool` — **GĐ2** (cần P04b `count_draft_claims`) — spec 4: `count_draft_claims(topic) > 0`.
- `regen_all(topic, stage)->TopicViews` — gọi trong bước REGEN (P08) trước VALIDATE. `stage=core` (GĐ1) chỉ regen review_schedule+assessment; `stage=full` (GĐ2) thêm has_draft_knowledge.

## INV/mục spec liên quan

4 (miền băm + canonical), 7 (thuật toán sinh), INV-09 (regen + deep-compare + hash), INV-26 (`has_draft_knowledge` view).

## Cách test (`_system/validator/tests/phase09_views/`)

```text
[ ] build_review_schedule: input cố định → items sắp đúng thứ tự khóa; hash khớp giá trị vàng.
[ ] Đổi field NGOÀI miền băm (vd difficulty) → hash KHÔNG đổi (đúng ý: view lịch chỉ phụ thuộc due+state).
[ ] Đổi due_date của 1 item → hash ĐỔI → phát hiện stale.
[ ] E-VIEW-MISMATCH: sửa tay items[] nhưng giữ hash cũ → regen deep-compare bắt được.
[ ] build_assessment: chỉ tính lesson learned/needs_review; avg đúng, làm tròn 1 số.
[ ] has_draft_knowledge: topic có 1 claim draft → true; xoá claim đó → false.
[ ] Determinism: regen 2 lần cùng input → cùng object + cùng hash.
```

## Cạm bẫy

- Loại tuyệt đối field view (`generated_from_hash`, `review_schedule`, `assessment`) khỏi `data` để không tự tham chiếu vòng (spec 4).
- INV-09 = **deep-compare object TRƯỚC, rồi hash** — hash một mình không đủ.
- `has_draft_knowledge` là view → FULL-regen tự set, AI không sửa tay (spec vá v2.4 #10).
