"""P07b-2b tests — INV-23 (E-CLAIM-LOC) + INV-26 (E-DRAFT-IN-MAP)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402

CLAIMS_FENCE = """```yaml
claims:
  - id: clm-001
    class: B
    status: confirmed
    text: "t"
```
"""


def _topic(tmp_path):
    td = tmp_path / "topics" / "docker"
    (td / "lessons" / "lesson-001").mkdir(parents=True)
    return td


def _loc_codes(tmp_path, td):
    rep = V.Report()
    V._check_claim_location(td, tmp_path, rep)
    return [e["error_code"] for e in rep.errors]


# ---- INV-23: claim dưới '## Claims' của topic.md → hợp lệ ------------
def test_loc_claims_in_section_ok(tmp_path):
    td = _topic(tmp_path)
    (td / "topic.md").write_text(f"# Docker\n\n## Claims\n\n{CLAIMS_FENCE}\n", encoding="utf-8")
    assert _loc_codes(tmp_path, td) == []


# ---- INV-23: claim dưới heading khác trong topic.md → E-CLAIM-LOC ----
def test_loc_claims_wrong_heading(tmp_path):
    td = _topic(tmp_path)
    (td / "topic.md").write_text(f"# Docker\n\n## Ghi chú\n\n{CLAIMS_FENCE}\n", encoding="utf-8")
    assert "E-CLAIM-LOC" in _loc_codes(tmp_path, td)


# ---- INV-23: claim trong lesson.md (cấm) → E-CLAIM-LOC --------------
def test_loc_claims_in_lesson_body(tmp_path):
    td = _topic(tmp_path)
    (td / "lessons" / "lesson-001" / "lesson.md").write_text(
        f"# L\n\n## Claims\n\n{CLAIMS_FENCE}\n", encoding="utf-8")
    assert "E-CLAIM-LOC" in _loc_codes(tmp_path, td)


# ---- INV-23: claim trong lesson_notes.md dưới '## Claims' → hợp lệ ---
def test_loc_claims_in_notes_ok(tmp_path):
    td = _topic(tmp_path)
    (td / "lessons" / "lesson-001" / "lesson_notes.md").write_text(
        f"# Notes\n\n## Claims\n\n{CLAIMS_FENCE}\n", encoding="utf-8")
    assert _loc_codes(tmp_path, td) == []


# ---- INV-26: draft claim trong '## Knowledge Map' → E-DRAFT-IN-MAP ---
def test_draft_in_knowledge_map(tmp_path):
    td = _topic(tmp_path)
    (td / "topic.md").write_text(
        "# Docker\n\n## Knowledge Map\n- clm-draft: điều chưa nguồn hoá\n", encoding="utf-8")
    collected = [({"id": "clm-draft", "status": "draft"}, Path("topics/docker/topic.md"))]
    rep = V.Report()
    V._check_draft_map(td, tmp_path, collected, rep)
    assert "E-DRAFT-IN-MAP" in [e["error_code"] for e in rep.errors]


def _write_topic_state(td, has_draft: bool):
    fm = f"""---
schema: topic_state
schema_version: 1
topic_id: docker
title: Docker
has_draft_knowledge: {str(has_draft).lower()}
created: 2026-06-30
updated: 2026-06-30
review_schedule:
  generated_from_hash: "sha256:x"
  items: []
assessment:
  generated_from_hash: "sha256:y"
  concept_avg: 0.0
  explain_avg: 0.0
  apply_avg: 0.0
  critique_avg: 0.0
  teachback_avg: 0.0
---
"""
    (td / "topic_state.md").write_text(fm, encoding="utf-8")


# ---- INV-26: has_draft_knowledge sai so thực tế → E-DRAFT-IN-MAP -----
def test_has_draft_flag_wrong(tmp_path):
    td = _topic(tmp_path)
    _write_topic_state(td, has_draft=False)  # cờ nói KHÔNG draft
    collected = [({"id": "clm-d", "status": "draft"}, Path("x"))]  # thực tế CÓ draft
    rep = V.Report()
    V._check_draft_map(td, tmp_path, collected, rep)
    assert "E-DRAFT-IN-MAP" in [e["error_code"] for e in rep.errors]


# ---- INV-26: cờ khớp thực tế → sạch ---------------------------------
def test_has_draft_flag_correct(tmp_path):
    td = _topic(tmp_path)
    _write_topic_state(td, has_draft=False)
    rep = V.Report()
    V._check_draft_map(td, tmp_path, [], rep)  # không draft, cờ false → khớp
    assert [e["error_code"] for e in rep.errors] == []


# ---- INV-26 (nhất quán): draft claim THIẾU id vẫn tính actual=True ---
def test_has_draft_consistency_draft_without_id(tmp_path):
    """Bên-sinh (count_draft_claims) đếm mọi status=draft; bên-kiểm phải khớp,
    kể cả claim draft thiếu id — nếu không sẽ có mismatch E-DRAFT-IN-MAP giả."""
    td = _topic(tmp_path)
    _write_topic_state(td, has_draft=False)  # cờ false
    collected = [({"status": "draft", "class": "D", "text": "t"}, Path("x"))]  # draft, KHÔNG id
    rep = V.Report()
    V._check_draft_map(td, tmp_path, collected, rep)
    assert "E-DRAFT-IN-MAP" in [e["error_code"] for e in rep.errors]
