"""P07a tests — validate.py FULL --scope core (liên-file GĐ1).

Golden suite: 1 vault hợp lệ + mỗi INV hỏng 1 ca (spec 10.6).
Vault hợp lệ được "author" bằng chính views.regen_all → INV-09 khớp tự nhiên.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, time as dtime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V       # noqa: E402
import models as M         # noqa: E402
import views as VW         # noqa: E402
import fsrs_adapter as FA  # noqa: E402
from canonical import normalize_yaml_object  # noqa: E402

CFG = FA.load_config(ROOT / "fsrs_config.yaml")
OFF = "+07:00"
NOW = datetime(2026, 7, 1, 12, tzinfo=FA._parse_offset(OFF))  # >= mọi ngày fixture → INV-05 tất định
TOPIC = "docker"
LDIR = "lesson-001"
LID = f"{TOPIC}/{LDIR}"

LESSON_MD = """# Lesson

## Mục tiêu
x

## Sessions
### S
#### Question q1
"?"
#### Question q2
"??"
"""


def _fm(d: dict) -> str:
    return "---\n" + yaml.safe_dump(d, allow_unicode=True, sort_keys=False) + "---\n"


def fresh_item(rid="rv-001", prompt_ref="lesson.md#q1", created=date(2026, 6, 30)):
    return {
        "id": rid, "prompt_ref": prompt_ref, "fsrs_config_version": 1, "created": created,
        "card": {"state": "Learning", "step": 0, "stability": None, "difficulty": None,
                 "due_at_utc": "2026-06-30T03:00:00Z", "due_date": created,
                 "last_reviewed_at_utc": None},
        "log": [], "mastery_state": "new",
    }


def reviewed_item(rid="rv-001", prompt_ref="lesson.md#q1", created=date(2026, 6, 30),
                  events=None):
    events = events or [{"reviewed_at": "2026-06-30T20:00:00+07:00", "rating": 3}]
    created_dt = datetime.combine(created, dtime(0, 0), tzinfo=FA._parse_offset(OFF))
    card = FA.replay(created_dt, events, CFG, OFF)
    card = dict(card)
    card["due_date"] = date.fromisoformat(card["due_date"])
    ms = FA.derive_mastery(FA.replay(created_dt, events, CFG, OFF), events, CFG)
    return {"id": rid, "prompt_ref": prompt_ref, "fsrs_config_version": 1, "created": created,
            "card": card, "log": list(events), "mastery_state": ms}


def lesson_dict(lesson_id=LID, status="in_progress", items=None, scores=None):
    scores = scores or {ax: 0 for ax in VW.AXES}
    return {
        "schema": "lesson_state", "schema_version": 1, "lesson_id": lesson_id,
        "title": "Container", "status": status,
        "created": date(2026, 6, 30), "updated": date(2026, 6, 30),
        "objective": "x", "prerequisites": [], "sections_done": [], "sections_pending": [],
        "mastery": {ax: {"score": scores[ax], "evidence": []} for ax in VW.AXES},
        "open_gaps": [], "review_items": items if items is not None else [fresh_item()],
        "next_action": "", "last_session": None,
    }


def _parse_lesson(ls: dict):
    raw = yaml.safe_load(_fm(ls).split("---", 2)[1])
    return M.LessonState(**normalize_yaml_object(raw, str_fields=V._STR_FIELDS))


def build_vault(tmp: Path, ls: dict, *, folder=LDIR, vs_current_lesson=LID,
                ts_current_lesson=LID, ts_lessons=None, rs_items=None,
                rs_hash=None, as_hash=None, lesson_md=LESSON_MD):
    ld = tmp / "topics" / TOPIC / "lessons" / folder
    ld.mkdir(parents=True)
    vs = {"schema": "vault_state", "schema_version": 1, "utc_offset": OFF,
          "day_cutoff_hour": 4, "current_topic": TOPIC, "current_lesson": vs_current_lesson}
    (tmp / "vault_state.md").write_text(_fm(vs), encoding="utf-8")
    (ld / "lesson_state.md").write_text(_fm(ls), encoding="utf-8")
    (ld / "lesson.md").write_text(lesson_md, encoding="utf-8")

    # author topic_state từ view thật
    lm = _parse_lesson(ls)
    regen = VW.regen_all([lm])
    rs = regen["review_schedule"]
    asmt = regen["assessment"]
    ts = {
        "schema": "topic_state", "schema_version": 1, "topic_id": TOPIC, "title": "Docker",
        "current_lesson": ts_current_lesson, "has_draft_knowledge": False,
        "lessons": ts_lessons if ts_lessons is not None else [{"id": lm.lesson_id, "status": lm.status}],
        "created": date(2026, 6, 30), "updated": date(2026, 6, 30),
        "review_schedule": {
            "generated_from_hash": rs_hash or rs["generated_from_hash"],
            "items": rs["items"] if rs_items is None else rs_items,
        },
        "assessment": {**asmt, "generated_from_hash": as_hash or asmt["generated_from_hash"]},
    }
    (tmp / "topics" / TOPIC / "topic_state.md").write_text(_fm(ts), encoding="utf-8")


def run(tmp: Path):
    rep = V.Report()
    V.validate_full_core(ROOT, tmp, rep, now=NOW)
    return rep


def codes(rep):
    return {e["error_code"] for e in rep.errors}


# ---- valid --------------------------------------------------------------
def test_valid_core_fresh_passes(tmp_path):
    build_vault(tmp_path, lesson_dict())
    rep = run(tmp_path)
    assert rep.ok(), rep.errors


def test_valid_core_reviewed_passes(tmp_path):
    it = reviewed_item()
    ls = lesson_dict(status="needs_review", items=[it],
                     scores={ax: 2 for ax in VW.AXES})
    build_vault(tmp_path, ls)
    rep = run(tmp_path)
    assert rep.ok(), rep.errors


def test_deterministic(tmp_path):
    build_vault(tmp_path, lesson_dict())
    assert [e for e in run(tmp_path).errors] == [e for e in run(tmp_path).errors]


# ---- invalid: mỗi INV một ca -------------------------------------------
def test_ref_broken(tmp_path):
    build_vault(tmp_path, lesson_dict(items=[fresh_item(prompt_ref="lesson.md#q9")]))
    assert "E-REF-BROKEN" in codes(run(tmp_path))


def test_review_dup_prompt_ref(tmp_path):
    items = [fresh_item("rv-001", "lesson.md#q1"), fresh_item("rv-002", "lesson.md#q1")]
    build_vault(tmp_path, lesson_dict(items=items))
    assert "E-REVIEW-DUP" in codes(run(tmp_path))


def test_review_miscalc(tmp_path):
    it = fresh_item()
    it["card"]["due_date"] = date(2026, 7, 1)  # != created → seed sai
    build_vault(tmp_path, lesson_dict(items=[it]))
    assert "E-REVIEW-MISCALC" in codes(run(tmp_path))


def test_fresh_due_at_utc_projection_mismatch(tmp_path):
    """Thẻ mầm: due_at_utc chiếu local ra ngày khác due_date → E-REVIEW-MISCALC (coupling spec 8.3)."""
    it = fresh_item()
    it["card"]["due_at_utc"] = "2026-06-30T20:00:00Z"  # +07 → 2026-07-01, nhưng due_date=created=06-30
    build_vault(tmp_path, lesson_dict(items=[it]))
    assert "E-REVIEW-MISCALC" in codes(run(tmp_path))


def test_state_derived(tmp_path):
    it = reviewed_item()
    it["mastery_state"] = "mastered" if it["mastery_state"] != "mastered" else "in_review"
    build_vault(tmp_path, lesson_dict(status="needs_review", items=[it],
                                      scores={ax: 2 for ax in VW.AXES}))
    assert "E-STATE-DERIVED" in codes(run(tmp_path))


def test_view_stale(tmp_path):
    build_vault(tmp_path, lesson_dict(), rs_hash="sha256:BADBADBAD")
    assert "E-VIEW-STALE" in codes(run(tmp_path))


def test_view_mismatch(tmp_path):
    bogus = [{"lesson_id": LID, "item_id": "rv-999",
              "due_date": date(2026, 6, 30), "mastery_state": "new"}]
    build_vault(tmp_path, lesson_dict(), rs_items=bogus)
    assert "E-VIEW-MISMATCH" in codes(run(tmp_path))


def test_index_mismatch_folder(tmp_path):
    build_vault(tmp_path, lesson_dict(),
                ts_lessons=[{"id": "docker/ghost", "status": "in_progress"}])
    assert "E-INDEX-MISMATCH" in codes(run(tmp_path))


def test_index_mismatch_current_lesson(tmp_path):
    build_vault(tmp_path, lesson_dict(), ts_current_lesson="docker/other")
    assert "E-INDEX-MISMATCH" in codes(run(tmp_path))


def test_id_path_mismatch(tmp_path):
    build_vault(tmp_path, lesson_dict(lesson_id="docker/wrong-id"))
    assert "E-ID-PATH" in codes(run(tmp_path))


def test_abspath_flagged(tmp_path):
    ls = lesson_dict()
    ls["next_action"] = "xem C:\\Users\\toan\\note.md"
    build_vault(tmp_path, ls)
    assert "E-PORT-ABSPATH" in codes(run(tmp_path))


def test_ref_into_scratch(tmp_path):
    build_vault(tmp_path, lesson_dict(items=[fresh_item(prompt_ref="_scratch/tmp.md#q1")]))
    assert "E-REF-BROKEN" in codes(run(tmp_path))


def test_unknown_fsrs_config_version(tmp_path):
    """INV-24: fsrs_config_version của item không có trong config → E-SCHEMA-OUTDATED."""
    it = fresh_item()
    it["fsrs_config_version"] = 999
    build_vault(tmp_path, lesson_dict(items=[it]))
    assert "E-SCHEMA-OUTDATED" in codes(run(tmp_path))
