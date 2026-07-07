# P04b — Markdown AST SEMANTIC (claims / evidence / answer-block) — GĐ2

**Mục tiêu:** trích nội dung ngữ nghĩa để P07b enforce claim/evidence/verbatim và để tính `has_draft_knowledge`.
**Phụ thuộc:** P04a (core AST), P02 (`normalize_yaml_object`, `normalize_for_match`).
**Giai đoạn MVP:** **GĐ2**.

## Xây gì

`_system/validator/md_ast.py` (phần semantic):

- `extract_claims(md)->[ClaimDict]` — mọi claim dưới `## Claims` (dùng `extract_yaml_after_heading` của P04a); trả list claim đã `normalize_yaml_object`.
- `extract_evidence(md)->[EvidenceDict]` — mọi `#### Evidence <ev-id>` + yaml đầy đủ (axis/timestamp/quote/ai_assessment) cho INV-22.
- `extract_answer_blocks(md)->{qid: text}` — text dưới `#### Bạn trả lời <qid>` (transcript verbatim cho INV-22b).
- `count_draft_claims(topic_files)->int` — đếm claim `status: draft` trong topic.md + lesson_notes.md của topic (nuôi `has_draft_knowledge`, INV-26).

## INV/mục spec liên quan

5.5, 19, INV-22 (evidence), INV-22b (answer-block verbatim), INV-23 (vùng claim), INV-26 (`has_draft_knowledge`). Phục vụ **P07b** và phần `has_draft_knowledge` của **P09**.

## Cách test (`_system/validator/tests/phase04b_semantic/`) — ĐÃ XANH (6 test)

```text
[x] extract_claims: file nhiều claim (confirmed + draft) → trả đủ, đúng field, status đúng.
[x] extract_evidence: nhiều evidence → trích đủ số lượng, đúng axis/quote.
[x] extract_answer_blocks: map qid→text đúng; block rỗng → text rỗng (không crash).
    ĐÃ KIỂM CHỨNG: q1 chỉ chứa lời người học, KHÔNG lẫn text '#### AI phản hồi' (an toàn INV-22b).
[x] count_draft_claims: 1 draft → 1; đổi confirmed → 0; list rỗng → 0.
[x] Claim đặt ngoài "## Claims" → extract_claims trả [] (không extract nhầm; chuẩn bị INV-23 ở P07b).
[x] Không section / không yaml → [] / {} (robust, không crash).
```

## Trạng thái hiện thực
Đã thêm vào `md_ast.py`: `extract_claims`, `extract_evidence`, `extract_answer_blocks` (dùng `token.map` cắt verbatim), `count_draft_claims`. Tầng TRÍCH thuần — không normalize, không áp luật lớp (dành P07b). 130/130 test toàn bộ PASS.

## Cạm bẫy

- `extract_answer_blocks` phải lấy **text thô của người học** (chưa normalize) để P07b tự `normalize_for_match` cả quote lẫn transcript đồng nhất (spec 9.6).
- `count_draft_claims` chỉ đếm trong vùng `## Claims`; claim ngoài vùng là lỗi INV-23, không tính.
