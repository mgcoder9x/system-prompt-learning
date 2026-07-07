# P04a — Markdown AST CORE (heading / fence / question / evidence-syntax) — GĐ1

**Mục tiêu:** hạ tầng parse AST đủ cho LIGHT (P06) và cấu trúc lesson.md — KHÔNG cần ngữ nghĩa claim.
**Phụ thuộc:** P00, P02 (`normalize_yaml_object`).
**Giai đoạn MVP:** **GĐ1** (P06 LIGHT cần cái này ngay).

## Xây gì

`_system/validator/md_ast.py` (phần core):

- `parse(md_text)->tokens` — token stream/AST bằng `markdown-it-py`.
- `find_headings(tokens)->[(level, text, pos)]` — **bỏ qua node `fence`** (code block) khi liệt kê heading.
- `extract_yaml_after_heading(tokens, heading_pred)->dict|None` — spec 5.5/19:
  heading khớp token tiêu đề chuẩn hoá → **fence `yaml` ĐẦU TIÊN, bỏ Paragraph chen giữa, DỪNG ở heading kế cùng/cao cấp** → `yaml.safe_load` → **`normalize_yaml_object(raw, schema)` (P02)**. Không thấy fence → lỗi cấu trúc.
- `extract_questions(md)->[qid]` — mọi heading `#### Question <qid>`; phát hiện trùng `qid`.
- `check_evidence_block_syntax(md)->[errors]` — chỉ CÚ PHÁP (cho LIGHT): mỗi `#### Evidence <ev-id>` phải có fenced `yaml` liền sau (theo luật "fence đầu tiên") đủ field `axis/timestamp/quote/ai_assessment`; `ev-id` không trùng. KHÔNG kiểm ngữ nghĩa (verbatim/axis-score) — đó là P04b/P07b.

## INV/mục spec liên quan

19 (parser AST, token tiêu đề cho phép), 5.5 (định dạng), 14A; phục vụ **P06 LIGHT** và cấu trúc chung.

## Cách test (`_system/validator/tests/phase04a_ast/`)

```text
[ ] Heading trong ```code fence``` KHÔNG bị nhận là heading thật.
[ ] Prose chen giữa: "## X\n\nDưới đây:\n\n```yaml..." → vẫn lấy được yaml.
[ ] Thiếu fence trước heading kế → lỗi cấu trúc.
[ ] extract_questions: 2 "#### Question q1" → phát hiện trùng.
[ ] check_evidence_block_syntax: thiếu ai_assessment → báo lỗi; ev-id trùng → báo lỗi; cấp sai (###) → không nhận.
[ ] normalize_yaml_object áp đúng: timestamp/date trong evidence yaml giữ type trước pydantic.
```

## Cạm bẫy

- KHÔNG "fence phải ngay sát heading" — LLM chèn câu dẫn; dùng "fence đầu tiên trước heading kế" (spec 19).
- Khớp **text tiêu đề chuẩn hoá** trên node heading là được phép; cấm regex dò field trên prose (spec 5.5).
