"""P09 (bổ sung) — has_draft_knowledge trong regen_all(stage='full') (spec mục 4, INV-26).

Khép INV-26 hai chiều: validator đã KIỂM field; nay bên SINH view tính đúng từ claim texts.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import views as VW  # noqa: E402

DRAFT_NOTES = """# Notes

## Claims

```yaml
claims:
  - id: clm-1
    class: D
    status: draft
    text: "chưa nguồn hoá"
    draft_reason: "chưa đo"
```
"""

CONFIRMED_NOTES = """# Notes

## Claims

```yaml
claims:
  - id: clm-1
    class: B
    status: confirmed
    text: "đã nguồn hoá"
    source_refs: ["src-1#a1"]
```
"""


def test_full_stage_true_when_draft():
    v = VW.regen_all([], stage="full", claim_texts=[DRAFT_NOTES])
    assert v["has_draft_knowledge"] is True


def test_full_stage_false_when_only_confirmed():
    v = VW.regen_all([], stage="full", claim_texts=[CONFIRMED_NOTES])
    assert v["has_draft_knowledge"] is False


def test_full_stage_false_when_no_claims():
    assert VW.regen_all([], stage="full", claim_texts=None)["has_draft_knowledge"] is False
    assert VW.regen_all([], stage="full")["has_draft_knowledge"] is False


def test_core_stage_omits_field():
    v = VW.regen_all([], stage="core")
    assert "has_draft_knowledge" not in v  # GĐ1 không sinh field này


def test_helper_direct():
    assert VW.build_has_draft_knowledge([DRAFT_NOTES]) is True
    assert VW.build_has_draft_knowledge([CONFIRMED_NOTES, CONFIRMED_NOTES]) is False
    assert VW.build_has_draft_knowledge([]) is False
