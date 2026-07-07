# P07b — Validator FULL-SEMANTIC (claim / evidence / gate) — GĐ2

**Mục tiêu:** đắp tầng ngữ nghĩa kiểm được: cổng "đã hiểu", evidence verbatim, phân lớp claim, draft/knowledge-map.
**Phụ thuộc:** P07a (core đã xanh), P04b (AST semantic: claims/evidence/answer-block), P02 (`normalize_for_match`).
**Giai đoạn MVP:** **GĐ2**.

## INV thuộc P07b (semantic)

- **Cổng:** INV-07 (`status: learned` ⇒ `learned_gate(mastery)` đúng + đủ evidence).
- **Evidence:** INV-22 (mỗi trục đạt ngưỡng có evidence tồn tại, `axis` khớp, đủ field `axis/timestamp/quote/ai_assessment`), **INV-22b** (`normalize_for_match(quote) ⊆ transcript` block `#### Bạn trả lời <qid>`) → `E-ASSESS-FAKEQUOTE`.
- **Claim:** INV-12 (B confirmed có anchor confirmed), INV-13 (không dùng nguồn raw/rejected), INV-14 (C confirmed: tiền đề A/B confirmed, không D/không draft), INV-15 (đủ `id/class/status/text`; draft thiếu `draft_reason`→`E-CLAIM-DRAFTREASON`), INV-23 (claim đúng vùng `## Claims`).
- **Draft/map:** INV-26 (draft KHÔNG vào `## Knowledge Map`; `has_draft_knowledge` view đúng) → `E-DRAFT-IN-MAP`.

## Trạng thái hiện thực (chia 2 cụm để mỗi bước xanh, không để code vỡ)

- **Cụm 1 — cổng/evidence/verbatim (INV-07/22/22b): ĐÃ XONG.** `validate.py`: `_GATE` (concept/explain/apply/teachback≥2, critique≥1), `_check_gate_and_evidence` (E-GATE-FAIL / E-ASSESS-NOEVIDENCE / E-ASSESS-FAKEQUOTE dùng `normalize_for_match`), `validate_full_semantic` (core + semantic, parse lại bằng report nháp để không nhân đôi lỗi core). CLI `--scope full` đã nối (bỏ E-NOTIMPL). 6 test `phase07b_semantic/test_gate_evidence.py` (cách ly từng mã lỗi + dung sai verbatim + end-to-end demo PASS). 136/136 toàn bộ PASS.
- **Cụm 2a — claim cấu trúc + tiền đề (INV-15/14): ĐÃ XONG.** `validate.py`: `_collect_topic_claims` (gom claim từ `topic.md` + `lesson_notes.md` mỗi lesson) + `_check_claims` (INV-15: đủ id/class/status/text → thiếu class `E-CLAIM-UNCLASSED`, draft thiếu reason `E-CLAIM-DRAFTREASON`; INV-14: C confirmed phải có tiền đề A/B confirmed → `E-CLAIM-WEAKBASE`). 9 test `test_claims.py`. 145/145 PASS.
- **Cụm 2b — claim nguồn/vùng/draft-map (INV-12/13/23/26): ĐÃ XONG.**
  - **Fix gốc trước:** mở rộng model `Source` (`trust/scope/added/anchors`) + thêm `SourceAnchor` (spec 5.3) — trước đó `_Strict extra='forbid'` khiến `sources.md` đúng spec fail schema (latent bug P03).
  - INV-12 (`E-CLAIM-NOSRC`): B confirmed cần ≥1 anchor nguồn confirmed + quote không rỗng. INV-13 (`E-SRC-RAWUSED`): source_ref trỏ nguồn raw/rejected.
  - INV-23 (`E-CLAIM-LOC`): `find_claims_fences` — fence 'claims:' ngoài '## Claims' (topic.md/lesson_notes.md) hoặc bất kỳ trong lesson.md. INV-26 (`E-DRAFT-IN-MAP`): draft-id trong '## Knowledge Map' + `has_draft_knowledge` khớp thực tế.
  - Test: `test_claim_sources.py` (8), `test_claim_loc_draftmap.py` (7).

**⇒ P07b HOÀN TẤT: toàn bộ INV-07/12/13/14/15/22/22b/23/26. Validator giờ phủ INV-01..26. 160/160 test PASS.**

## Cách test — GOLDEN SUITE SEMANTIC (`_system/validator/tests/phase07b_semantic/`)

```text
[ ] valid_vault_full/ (core + claims/evidence hợp lệ + learned qua gate) → FULL PASS.
[ ] invalid/E-GATE-FAIL__learned_low_score/
[ ] invalid/E-ASSESS-NOEVIDENCE__gate_no_ev/
[ ] invalid/E-ASSESS-FAKEQUOTE__quote_not_in_transcript/
[ ] invalid/E-ASSESS-NOEVIDENCE__evidence_missing_ai_assessment/  (thiếu field cấu trúc)
[ ] invalid/E-CLAIM-NOSRC__confirmed_B_no_anchor/
[ ] invalid/E-CLAIM-WEAKBASE__C_from_draft/
[ ] invalid/E-CLAIM-DRAFTREASON__draft_no_reason/
[ ] invalid/E-CLAIM-LOC__claim_outside_claims_section/
[ ] invalid/E-SRC-RAWUSED__anchor_to_raw/
[ ] invalid/E-DRAFT-IN-MAP__draft_in_knowledge_map/
[ ] invalid/E-DRAFT-IN-MAP__has_draft_flag_wrong/   (has_draft_knowledge view sai)
[ ] Chạy 2 lần trên valid_vault_full → report giống hệt.
```

## Cạm bẫy

- INV-22b so **sau `normalize_for_match`** (P02), không so raw (báo oan) nhưng KHÔNG lowercase/bỏ dấu (spec 9.6).
- Golden suite (P07a + P07b) là điều kiện tin validator: chưa xanh 100% thì **chưa được tin bất kỳ PASS nào** (spec 10.6).
- Verbatim check cần transcript block `#### Bạn trả lời <qid>` (P04 `extract_answer_blocks`).
