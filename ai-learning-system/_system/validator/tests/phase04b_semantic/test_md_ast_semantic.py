"""P04b tests — AST semantic: claims / evidence / answer-block (spec 5.5, GĐ2).

Tầng trích thuần: kiểm trích ĐỦ và ĐÚNG, KHÔNG áp luật lớp (đó là P07b).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

NOTES = """# Notes

## Claims

```yaml
claims:
  - id: clm-001
    class: B
    status: confirmed
    text: "Container chia sẻ kernel host."
    source_refs: ["src-003#a2"]
    premise_refs: []
    draft_reason: null
  - id: clm-002
    class: D
    status: draft
    text: "Có lẽ container nhẹ hơn VM đáng kể."
    source_refs: []
    premise_refs: []
    draft_reason: "chưa đo benchmark"
```

## Knowledge Map
- clm-001
"""

LESSON = """# Lesson

## Sessions

### Session 2026-06-30
#### Question q1
"Vì sao container khác máy ảo?"

#### Bạn trả lời q1
Container chia sẻ kernel nên nhẹ hơn máy ảo.

#### AI phản hồi
Tốt.

#### Evidence ev-20260630-001

```yaml
axis: explain
timestamp: 2026-06-30
quote: "Container chia sẻ kernel nên nhẹ hơn máy ảo."
ai_assessment: "giải thích đúng cơ chế"
```

#### Question q2
"Câu hai?"
#### Bạn trả lời q2
"""


# ---- 1. extract_claims: confirmed + draft, đủ field, đúng status ------
def test_extract_claims():
    claims = A.extract_claims(NOTES)
    assert len(claims) == 2
    by_id = {c["id"]: c for c in claims}
    assert by_id["clm-001"]["status"] == "confirmed" and by_id["clm-001"]["class"] == "B"
    assert by_id["clm-002"]["status"] == "draft"
    assert by_id["clm-002"]["draft_reason"] == "chưa đo benchmark"


# ---- 2. extract_evidence: đúng số lượng + axis/quote ------------------
def test_extract_evidence():
    evs = A.extract_evidence(LESSON)
    assert len(evs) == 1
    ev = evs[0]
    assert ev["id"] == "ev-20260630-001"
    assert ev["axis"] == "explain"
    assert ev["quote"] == "Container chia sẻ kernel nên nhẹ hơn máy ảo."


# ---- 3. extract_answer_blocks: qid→text; block rỗng → '' -------------
def test_extract_answer_blocks():
    ans = A.extract_answer_blocks(LESSON)
    assert set(ans) == {"q1", "q2"}
    assert "Container chia sẻ kernel nên nhẹ hơn máy ảo." in ans["q1"]
    assert ans["q2"].strip() == ""  # block rỗng, không crash


# ---- 4. count_draft_claims: 1 draft → 1; bỏ đi → 0 -------------------
def test_count_draft_claims():
    assert A.count_draft_claims([NOTES]) == 1
    no_draft = NOTES.replace("status: draft", "status: confirmed").replace(
        'draft_reason: "chưa đo benchmark"', "draft_reason: null")
    assert A.count_draft_claims([no_draft]) == 0
    assert A.count_draft_claims([]) == 0


# ---- 5. claim NGOÀI '## Claims' → KHÔNG bị trích nhầm (chuẩn bị INV-23)
def test_claim_outside_claims_section_not_extracted():
    md = """# X

## Ghi chú linh tinh

```yaml
claims:
  - id: clm-999
    class: A
    status: confirmed
    text: "claim đặt sai chỗ"
```
"""
    assert A.extract_claims(md) == []  # không có '## Claims' → không trích


# ---- 6. không có section/không yaml → [] (robust) --------------------
def test_no_claims_section_returns_empty():
    assert A.extract_claims("# chỉ có tiêu đề\n\nvài dòng prose") == []
    assert A.extract_evidence("# trống") == []
    assert A.extract_answer_blocks("# trống") == {}
