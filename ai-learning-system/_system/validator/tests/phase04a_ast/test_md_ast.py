"""P04a tests — AST core (spec 19, 5.5, 14A)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

EVID_OK = """# Lesson
## Mục tiêu
x
## Sessions
### Session 2026-06-30
#### Question q1
"Vì sao?"
#### Bạn trả lời q1
> vì đóng gói phụ thuộc

Dưới đây là bằng chứng:

#### Evidence ev-1
```yaml
axis: explain
timestamp: 2026-06-30
quote: "vì đóng gói phụ thuộc"
ai_assessment: "đúng ý"
```
"""


def test_heading_in_codefence_ignored():
    md = "# Real\n\n```text\n## Fake heading\n```\n\n## Actual\n"
    texts = [h.text for h in A.find_headings(A.parse(md))]
    assert "Actual" in texts and "Fake heading" not in texts


def test_prose_between_heading_and_fence():
    # câu dẫn chen giữa heading và fence → vẫn lấy được yaml
    errs = A.check_evidence_block_syntax(EVID_OK)
    assert errs == [], errs


def test_evidence_missing_field():
    md = EVID_OK.replace('ai_assessment: "đúng ý"\n', "")
    errs = A.check_evidence_block_syntax(md)
    assert any("E-EVIDENCE-FIELD" in e for e in errs)


def test_evidence_missing_yaml():
    md = "## Sessions\n#### Evidence ev-1\n\nkhông có yaml\n\n## Kế\n"
    errs = A.check_evidence_block_syntax(md)
    assert any("E-EVIDENCE-NOYAML" in e for e in errs)


def test_evidence_wrong_level():
    md = "## Sessions\n### Evidence ev-1\n```yaml\naxis: explain\ntimestamp: 2026-06-30\nquote: x\nai_assessment: y\n```\n"
    errs = A.check_evidence_block_syntax(md)
    assert any("E-EVIDENCE-LEVEL" in e for e in errs)


def test_dup_question():
    md = "## Sessions\n#### Question q1\na\n#### Question q1\nb\n"
    qids, errs = A.extract_questions(md)
    assert qids == ["q1", "q1"] and any("E-DUP-QID" in e for e in errs)


def test_has_heading_required():
    assert A.has_heading(EVID_OK, "Mục tiêu")
    assert A.has_heading(EVID_OK, "Sessions")


def test_extract_yaml_under_claims():
    md = "## Claims\n\nnói chút:\n\n```yaml\nclaims:\n  - id: clm-001\n    class: B\n    status: draft\n    text: t\n    draft_reason: chưa nguồn\n```\n"
    data = A.extract_yaml_under_heading(md, "Claims", level=2)
    assert data["claims"][0]["id"] == "clm-001"
