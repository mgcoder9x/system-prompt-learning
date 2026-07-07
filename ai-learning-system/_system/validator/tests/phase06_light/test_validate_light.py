"""P06 tests — validate.py mức LIGHT (spec 10.8). Dựng vault tạm, chạy validate_light."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402

VAULT_STATE = """---
schema: vault_state
schema_version: 1
utc_offset: "+07:00"
day_cutoff_hour: 4
current_topic: docker
current_lesson: docker/lesson-001
---
"""

LESSON_STATE = """---
schema: lesson_state
schema_version: 1
lesson_id: docker/lesson-001
title: Container la gi
status: in_progress
created: 2026-06-30
updated: 2026-06-30
objective: Hieu container
prerequisites: []
sections_done: []
sections_pending: []
mastery:
  concept: {score: 0, evidence: []}
  explain: {score: 0, evidence: []}
  apply: {score: 0, evidence: []}
  critique: {score: 0, evidence: []}
  teachback: {score: 0, evidence: []}
open_gaps: []
review_items:
  - id: rv-001
    prompt_ref: lesson.md#q1
    fsrs_config_version: 1
    created: 2026-06-30
    card:
      state: Learning
      step: 0
      stability: null
      difficulty: null
      due_at_utc: "2026-06-30T03:00:00Z"
      due_date: 2026-06-30
      last_reviewed_at_utc: null
    log: []
    mastery_state: new
next_action: ""
last_session: null
---
"""

LESSON_MD = """# Lesson 001

## Mục tiêu
Hiểu container.

## Sessions
### Session 2026-06-30
#### Question q1
"Vì sao?"
#### Bạn trả lời q1
> vì phụ thuộc môi trường
#### Evidence ev-1
```yaml
axis: explain
timestamp: 2026-06-30
quote: "vì phụ thuộc môi trường"
ai_assessment: "đúng ý"
```
"""

TOPIC_STATE = """---
schema: topic_state
schema_version: 1
topic_id: docker
title: Docker
current_lesson: docker/lesson-001
has_draft_knowledge: false
lessons:
  - id: docker/lesson-001
    status: in_progress
created: 2026-06-30
updated: 2026-06-30
review_schedule:
  generated_from_hash: "sha256:PENDING"
  items: []
assessment:
  generated_from_hash: "sha256:PENDING"
  concept_avg: 0.0
  explain_avg: 0.0
  apply_avg: 0.0
  critique_avg: 0.0
  teachback_avg: 0.0
---
"""


def build(tmp, lesson_state=LESSON_STATE, lesson_md=LESSON_MD, vault_state=VAULT_STATE):
    ld = tmp / "topics" / "docker" / "lessons" / "lesson-001"
    ld.mkdir(parents=True)
    (tmp / "vault_state.md").write_text(vault_state, encoding="utf-8")
    (tmp / "topics" / "docker" / "topic_state.md").write_text(TOPIC_STATE, encoding="utf-8")
    (ld / "lesson_state.md").write_text(lesson_state, encoding="utf-8")
    (ld / "lesson.md").write_text(lesson_md, encoding="utf-8")


def run(tmp):
    rep = V.Report()
    V.validate_light(tmp, None, rep)
    return rep


def codes(rep):
    return {e["error_code"] for e in rep.errors}


def test_valid_vault_passes(tmp_path):
    build(tmp_path)
    rep = run(tmp_path)
    assert rep.ok(), rep.errors  # topic_state giờ có model, LIGHT vẫn PASS (không kiểm hash view)


def test_light_accepts_pending_view_hash(tmp_path):
    """LIGHT không kiểm hash view: topic_state với generated_from_hash='PENDING' vẫn PASS."""
    build(tmp_path)
    assert run(tmp_path).ok()


def test_bad_status_enum(tmp_path):
    build(tmp_path, lesson_state=LESSON_STATE.replace("status: in_progress", "status: done"))
    assert "E-SCHEMA" in codes(run(tmp_path))


def test_unknown_schema(tmp_path):
    """spec §10.6: file *_state.md với 'schema' không nhận diện → E-SCHEMA-UNKNOWN (nhánh trước-đây thiếu test)."""
    build(tmp_path, lesson_state=LESSON_STATE.replace("schema: lesson_state", "schema: bogus_schema"))
    assert "E-SCHEMA-UNKNOWN" in codes(run(tmp_path))


def test_broken_yaml_frontmatter(tmp_path):
    """spec §10.6: front-matter YAML hỏng cú pháp (quote không đóng) → E-SCHEMA-YAML (nhánh trước-đây thiếu test)."""
    build(tmp_path, lesson_state=LESSON_STATE.replace("title: Container la gi", 'title: "unterminated'))
    assert "E-SCHEMA-YAML" in codes(run(tmp_path))


def test_newitem_with_stability(tmp_path):
    bad = LESSON_STATE.replace("stability: null", "stability: 1.2", 1)
    build(tmp_path, lesson_state=bad)
    assert "E-SCHEMA" in codes(run(tmp_path))


def test_missing_required_heading(tmp_path):
    build(tmp_path, lesson_md=LESSON_MD.replace("## Mục tiêu\nHiểu container.\n\n", ""))
    assert "E-LESSON-HEADING" in codes(run(tmp_path))


def test_dup_qid(tmp_path):
    dup = LESSON_MD.replace('#### Bạn trả lời q1', '#### Question q1\n"lại q1"\n#### Bạn trả lời q1')
    build(tmp_path, lesson_md=dup)
    assert "E-QUESTION" in codes(run(tmp_path))


def test_evidence_missing_field(tmp_path):
    bad = LESSON_MD.replace('ai_assessment: "đúng ý"\n', "")
    build(tmp_path, lesson_md=bad)
    assert "E-EVIDENCE" in codes(run(tmp_path))


def test_abspath_in_lesson(tmp_path):
    bad = LESSON_MD + "\nĐường dẫn C:\\Users\\toan\\x\n"
    build(tmp_path, lesson_md=bad)
    assert "E-PORT-ABSPATH" in codes(run(tmp_path))


def test_light_skips_replay_and_views(tmp_path):
    """LIGHT KHÔNG chạy replay/hash: lesson_state hợp lệ cú pháp vẫn PASS dù chưa có view topic."""
    build(tmp_path)
    assert run(tmp_path).ok()


def _second_item(rid, prompt_ref):
    return f"""  - id: {rid}
    prompt_ref: {prompt_ref}
    fsrs_config_version: 1
    created: 2026-06-30
    card:
      state: Learning
      step: 0
      stability: null
      difficulty: null
      due_at_utc: "2026-06-30T03:00:00Z"
      due_date: 2026-06-30
      last_reviewed_at_utc: null
    log: []
    mastery_state: new
"""


def test_dup_prompt_ref_is_review_dup(tmp_path):
    """INV-10 tầng validator: hai item cùng prompt_ref → E-REVIEW-DUP (không phải E-SCHEMA)."""
    ls = LESSON_STATE.replace("next_action:", _second_item("rv-002", "lesson.md#q1") + "next_action:")
    build(tmp_path, lesson_state=ls)
    c = codes(run(tmp_path))
    assert "E-REVIEW-DUP" in c and "E-SCHEMA" not in c


def test_dup_rv_id_is_id_dup(tmp_path):
    """INV-04 tầng validator: rv-id trùng trong lesson → E-ID-DUP."""
    ls = LESSON_STATE.replace("next_action:", _second_item("rv-001", "lesson.md#q2") + "next_action:")
    build(tmp_path, lesson_state=ls)
    assert "E-ID-DUP" in codes(run(tmp_path))
