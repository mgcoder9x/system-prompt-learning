"""P10-agent — templates/ sinh ra vault HỢP-LỆ (test golden, không bịa hash).

- lesson_state.template + topic_state.template sau khi thay placeholder → parse đúng model pydantic.
- Hash view rỗng trong topic_template == hash THẬT do views.py sinh (không phải số gõ tay).
- lesson.template có đủ heading bắt buộc (## Mục tiêu, ## Sessions).
- Dựng vault empty-topic TỪ template → FULL validate PASS (end-to-end).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A   # noqa: E402
import models as M   # noqa: E402
import views as VW   # noqa: E402
import validate as V  # noqa: E402

TPL = ROOT / "templates"

SUBST = {
    "<<TOPIC_ID>>": "demo",
    "<<TOPIC_TITLE>>": "Demo Topic",
    "<<LESSON_ID>>": "demo/lesson-001",
    "<<LESSON_TITLE>>": "Bài demo",
    "<<OBJECTIVE>>": "Hiểu khái niệm demo",
    "<<CREATED>>": "2026-07-03",
}


def _fill(text: str) -> str:
    for k, v in SUBST.items():
        text = text.replace(k, v)
    return text


def _frontmatter(text: str) -> dict:
    t = _fill(text)
    assert t.startswith("---"), "template thiếu front-matter"
    body = t.split("---", 2)[1]  # giữa cặp --- đầu tiên
    return yaml.safe_load(body)


# ---- schema-level: template parse đúng model ------------------------
def test_lesson_state_template_valid():
    data = _frontmatter((TPL / "lesson_template" / "lesson_state.template.md").read_text(encoding="utf-8"))
    ls = M.LessonState(**data)  # raise nếu sai schema
    assert ls.status == "not_started" and ls.review_items == []


def test_sources_template_valid():
    data = _frontmatter((TPL / "topic_template" / "sources.template.md").read_text(encoding="utf-8"))
    assert M.Sources(**data).sources == []


def test_topic_state_template_valid_and_hash_is_real():
    data = _frontmatter((TPL / "topic_template" / "topic_state.template.md").read_text(encoding="utf-8"))
    ts = M.TopicState(**data)
    real_rs = VW.build_review_schedule([])["generated_from_hash"]
    real_as = VW.build_assessment([])["generated_from_hash"]
    assert ts.review_schedule.generated_from_hash == real_rs, "hash review_schedule KHÔNG khớp views.py (bịa?)"
    assert ts.assessment.generated_from_hash == real_as, "hash assessment KHÔNG khớp views.py (bịa?)"


def test_lesson_template_has_required_headings():
    text = _fill((TPL / "lesson_template" / "lesson.template.md").read_text(encoding="utf-8"))
    assert A.has_heading(text, "Mục tiêu") and A.has_heading(text, "Sessions")


# ---- end-to-end: vault empty-topic từ template → FULL validate PASS -
_VAULT_STATE = """---
schema: vault_state
schema_version: 1
utc_offset: "+07:00"
day_cutoff_hour: 4
current_topic: demo
current_lesson: null
export_policy: private_full
open_session:
  lesson_id: null
  started_at: null
  last_full_validate: null
---

# Vault State
"""


def test_empty_topic_vault_from_template_full_validates(tmp_path):
    (tmp_path / "vault_state.md").write_text(_VAULT_STATE, encoding="utf-8")
    tdir = tmp_path / "topics" / "demo"
    tdir.mkdir(parents=True)
    ts = _fill((TPL / "topic_template" / "topic_state.template.md").read_text(encoding="utf-8"))
    (tdir / "topic_state.md").write_text(ts, encoding="utf-8")
    rep = V.Report()
    # now = ngày CREATED của template (2026-07-03) → INV-05 tất định, không lệ đồng hồ tường
    V.validate_full_core(ROOT, tmp_path, rep, now=datetime(2026, 7, 3, 12, tzinfo=timezone.utc))
    assert rep.ok(), f"vault từ template KHÔNG PASS FULL: {rep.errors}"
