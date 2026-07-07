"""validate.py — validator CLI (spec mục 10.1, 10.8, 10.2).

P06: mức LIGHT (cú pháp/schema/file đơn).
P07a: mức FULL --scope core (liên-file: ref/id/replay/mastery/view/index — GĐ1).
CLI: validate.py --system <p> --vault <p> [--level light|full] [--scope core|full] [--file <path>] [--json]
Exit 0 = PASS, 1 = có lỗi.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, time as _dtime, timezone
from pathlib import Path

import yaml

import models as M
import md_ast as A
import vault_io as VIO
import views as VW
import fsrs_adapter as FA
import canonical as C
from canonical import normalize_yaml_object

# field YAML lẽ ra là string (quoted) nhưng phòng khi implicit-typed
_STR_FIELDS = {"due_at_utc", "last_reviewed_at_utc", "reviewed_at", "started_at",
               "last_full_validate", "ref"}
_SCHEMA_MODELS = {
    "lesson_state": M.LessonState,
    "vault_state": M.VaultState,
    "topic_state": M.TopicState,
    "sources": M.Sources,
    "curriculum": M.Curriculum,        # CR-0007/Task 3: parse curriculum.md qua model (sai cấu trúc → E-SCHEMA)
    "exam_results": M.ExamResults,     # CR-0007/Task 8
    "blueprint": M.Blueprint,          # CR-0011: parse blueprint.md qua model (sai cấu trúc → E-SCHEMA)
}
_PENDING_SCHEMAS: set[str] = set()  # tất cả schema GĐ1 đã có model (P03 mở rộng xong)
_REQUIRED_LESSON_HEADINGS = ["Mục tiêu", "Sessions"]


class Report:
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[str] = []

    def err(self, code, file, msg, field=""):
        self.errors.append({"error_code": code, "file": str(file), "field": field, "message": msg})

    def ok(self) -> bool:
        return not self.errors

    def dump(self, as_json: bool):
        if as_json:
            print(json.dumps({"pass": self.ok(), "errors": self.errors, "warnings": self.warnings},
                             ensure_ascii=False, indent=2))
        else:
            for w in self.warnings:
                print("  [warn]", w)
            if self.ok():
                print("PASS — không có lỗi.")
            else:
                print(f"FAIL — {len(self.errors)} lỗi:")
                for e in self.errors:
                    loc = f" @{e['field']}" if e["field"] else ""
                    print(f"  [{e['error_code']}] {e['file']}{loc}: {e['message']}")


def extract_review_states(text: str) -> dict:
    """Map rv.id → mastery_state từ front-matter lesson_state (thuần, không cần model).
    Dùng cho baseline INV-11 (so backup ↔ staged trong transaction)."""
    fm, _ = VIO.split_frontmatter(text)
    if fm is None:
        return {}
    try:
        raw = yaml.safe_load(fm) or {}
    except yaml.YAMLError:
        return {}
    return {rv["id"]: rv.get("mastery_state")
            for rv in raw.get("review_items", []) if isinstance(rv, dict) and "id" in rv}


def check_review_not_lost(baseline: dict, after: dict, tombstoned_ids, rep: Report, file=""):
    """INV-11 (spec 10.3a): item in_review/need_redo biến mất phải có tombstone hợp lệ, nếu không → E-REVIEW-LOST.
    baseline/after: map rv.id→mastery_state (baseline = backup của tx, after = staged)."""
    protected = {"in_review", "need_redo"}
    tomb = set(tombstoned_ids or ())
    for rid, ms in baseline.items():
        if rid not in after and ms in protected and rid not in tomb:
            rep.err("E-REVIEW-LOST", file,
                    f"review item {rid!r} ({ms}) biến mất không có tombstone hợp lệ (INV-11)")


# INV-06: cạnh chuyển status lesson hợp lệ (spec 6.1). Item mastery_state là hàm thuần → INV-21, KHÔNG áp cạnh.
_VALID_STATUS_EDGES = {
    ("not_started", "in_progress"),
    ("in_progress", "learned"),
    ("in_progress", "needs_review"),
    ("needs_review", "in_progress"),
    ("learned", "needs_review"),
}


def extract_lesson_status(text: str) -> str | None:
    """status từ front-matter lesson_state (thuần). None nếu không phải lesson_state / không parse được.
    Dùng baseline↔after INV-06 (diff trong transaction)."""
    fm, _ = VIO.split_frontmatter(text)
    if fm is None:
        return None
    try:
        raw = yaml.safe_load(fm) or {}
    except yaml.YAMLError:
        return None
    if raw.get("schema") != "lesson_state":
        return None
    return raw.get("status")


def check_status_transition(before, after, rep: Report, file=""):
    """INV-06 (spec 6.1): chuyển status lesson phải là cạnh hợp lệ. Chỉ gọi khi CÓ baseline (transaction).
    Giữ nguyên → OK; cạnh hợp lệ → OK; khác → E-STATE-ILLEGAL. before/after None (không xác định) → bỏ qua."""
    if before is None or after is None or before == after:
        return
    if (before, after) not in _VALID_STATUS_EDGES:
        rep.err("E-STATE-ILLEGAL", file,
                f"chuyển status {before!r} → {after!r} không hợp lệ (INV-06, mục 6.1)")


def _check_lesson_local_ids(lesson, rel, rep: Report):
    """INV-10 (prompt_ref duy nhất → E-REVIEW-DUP) + INV-04 (rv/gap id duy nhất trong lesson → E-ID-DUP).
    Tách khỏi model để phát đúng mã lỗi (spec 8.5/10.6); dùng chung LIGHT + FULL."""
    prefs = [rv.prompt_ref for rv in lesson.review_items]
    dup_pref = sorted({p for p in prefs if prefs.count(p) > 1})
    if dup_pref:
        rep.err("E-REVIEW-DUP", rel, f"prompt_ref trùng: {dup_pref} (INV-10)")
    for label, ids in (("rv", [rv.id for rv in lesson.review_items]),
                       ("gap", [g.id for g in lesson.open_gaps])):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup:
            rep.err("E-ID-DUP", rel, f"{label}-id trùng trong lesson: {dup} (INV-04)")


def _validate_state_file(path: Path, vault_root: Path, rep: Report):
    text = VIO.read_text(path)
    if VIO.scan_abspath(text):
        rep.err("E-PORT-ABSPATH", path.relative_to(vault_root), "chứa đường dẫn tuyệt đối")
    fm, _ = VIO.split_frontmatter(text)
    if fm is None:
        return None
    try:
        raw = yaml.safe_load(fm) or {}
    except yaml.YAMLError as e:
        rep.err("E-SCHEMA-YAML", path.relative_to(vault_root), f"front-matter YAML hỏng: {e}")
        return None
    schema = raw.get("schema")
    if schema in _PENDING_SCHEMAS:
        rep.warnings.append(f"W-NO-MODEL: {path.relative_to(vault_root)} schema '{schema}' chưa có model (P03 mở rộng)")
        return schema
    model = _SCHEMA_MODELS.get(schema)
    if model is None:
        rep.err("E-SCHEMA-UNKNOWN", path.relative_to(vault_root), f"schema không nhận diện: {schema!r}")
        return schema
    data = normalize_yaml_object(raw, str_fields=_STR_FIELDS)
    try:
        inst = model(**data)
    except Exception as e:  # pydantic ValidationError
        rep.err("E-SCHEMA", path.relative_to(vault_root), str(e).splitlines()[0] if str(e) else repr(e))
        return schema
    if schema == "lesson_state":
        _check_lesson_local_ids(inst, path.relative_to(vault_root), rep)
    return schema


def _validate_lesson_body(path: Path, vault_root: Path, rep: Report):
    text = VIO.read_text(path)
    rel = path.relative_to(vault_root)
    if VIO.scan_abspath(text):
        rep.err("E-PORT-ABSPATH", rel, "chứa đường dẫn tuyệt đối")
    for h in _REQUIRED_LESSON_HEADINGS:
        if not A.has_heading(text, h):
            rep.err("E-LESSON-HEADING", rel, f"thiếu heading bắt buộc '## {h}'")
    _, qerrs = A.extract_questions(text)
    for e in qerrs:
        rep.err("E-QUESTION", rel, e)
    for e in A.check_evidence_block_syntax(text):
        rep.err("E-EVIDENCE", rel, e)


def _emit_io_encoding(e, vault_root, rep: Report):
    """Chuyển EIoEncoding (đọc non-UTF-8) → report error E-IO-ENCODING (spec §10.4/§19).
    Đặt ở BIÊN validator: mọi read site lồng nhau raise EIoEncoding đều được gom về đây → KHÔNG crash."""
    p = getattr(e, "path", None)
    rel = p
    try:
        if p is not None:
            rel = Path(p).relative_to(vault_root).as_posix()
    except (ValueError, TypeError):
        rel = p
    rel_s = str(rel or "")
    # dedupe theo file: core + semantic có thể cùng đọc 1 file lỗi → chỉ báo 1 lần (report tất định, không nhiễu)
    if any(err["error_code"] == "E-IO-ENCODING" and err["file"] == rel_s for err in rep.errors):
        return
    rep.err("E-IO-ENCODING", rel_s, str(e))


def validate_light(vault_root: Path, only_file: Path | None, rep: Report):
    """Biên: bọc EIoEncoding → E-IO-ENCODING (không để non-UTF-8 crash validator)."""
    try:
        _validate_light_impl(vault_root, only_file, rep)
    except VIO.EIoEncoding as e:
        _emit_io_encoding(e, vault_root, rep)


def _validate_light_impl(vault_root: Path, only_file: Path | None, rep: Report):
    files, warns = VIO.discover_md(vault_root)
    rep.warnings.extend(warns)
    targets = [only_file] if only_file else files
    for p in targets:
        p = Path(p)
        if p.name == "lesson.md":
            _validate_lesson_body(p, vault_root, rep)
        elif p.name.endswith("_state.md") or p.name == "sources.md":
            _validate_state_file(p, vault_root, rep)
        else:
            # topic.md, lesson_notes.md... LIGHT chỉ quét abspath
            t = VIO.read_text(p)
            if VIO.scan_abspath(t):
                rep.err("E-PORT-ABSPATH", p.relative_to(vault_root), "chứa đường dẫn tuyệt đối")


# ========================================================================
# FULL --scope core (P07a) — liên-file GĐ1
# ========================================================================
def _parse_state_model(path: Path, vault_root: Path, rep: Report):
    """Đọc + model một *_state/sources file. Trả (schema, model|None)."""
    text = VIO.read_text(path)
    rel = path.relative_to(vault_root)
    if VIO.scan_abspath(text):
        rep.err("E-PORT-ABSPATH", rel, "chứa đường dẫn tuyệt đối")
    fm, _ = VIO.split_frontmatter(text)
    if fm is None:
        rep.err("E-SCHEMA", rel, "thiếu front-matter YAML")
        return None, None
    try:
        raw = yaml.safe_load(fm) or {}
    except yaml.YAMLError as e:
        rep.err("E-SCHEMA-YAML", rel, f"front-matter YAML hỏng: {e}")
        return None, None
    schema = raw.get("schema")
    model = _SCHEMA_MODELS.get(schema)
    if model is None:
        rep.err("E-SCHEMA-UNKNOWN", rel, f"schema không nhận diện: {schema!r}")
        return schema, None
    data = normalize_yaml_object(raw, str_fields=_STR_FIELDS)
    try:
        return schema, model(**data)
    except Exception as e:  # pydantic ValidationError
        rep.err("E-SCHEMA", rel, str(e).splitlines()[0] if str(e) else repr(e))
        return schema, None


def _card_to_dict(c) -> dict:
    """Card model → dict cùng dạng fsrs_adapter.card_to_dict (due_date là chuỗi)."""
    return {
        "state": c.state, "step": c.step,
        "stability": c.stability, "difficulty": c.difficulty,
        "due_at_utc": c.due_at_utc, "due_date": c.due_date.isoformat(),
        "last_reviewed_at_utc": c.last_reviewed_at_utc,
    }


def _check_prompt_refs(lesson, lesson_dir: Path, vault_root: Path, rep: Report):
    """INV-03: prompt_ref 'lesson.md#q1' phải trỏ heading '#### Question q1' tồn tại.
    INV-20: không trỏ vào vùng phi-thẩm-quyền (_scratch/.tx)."""
    rel = (lesson_dir / "lesson_state.md").relative_to(vault_root)
    for rv in lesson.review_items:
        ref = rv.prompt_ref
        if "#" not in ref:
            rep.err("E-REF-BROKEN", rel, f"{rv.id}: prompt_ref {ref!r} thiếu anchor '#'")
            continue
        fname, anchor = ref.split("#", 1)
        if set(Path(fname).parts) & {"_scratch", ".tx"}:
            rep.err("E-REF-BROKEN", rel, f"{rv.id}: prompt_ref trỏ vùng phi-thẩm-quyền {fname!r} (INV-20)")
            continue
        target = lesson_dir / fname
        if not target.is_file():
            rep.err("E-REF-BROKEN", rel, f"{rv.id}: prompt_ref trỏ file không tồn tại {fname!r}")
            continue
        qids, _ = A.extract_questions(VIO.read_text(target))
        if anchor not in qids:
            rep.err("E-REF-BROKEN", rel, f"{rv.id}: không thấy Question {anchor!r} trong {fname}")


def _check_replay(lesson, lesson_dir: Path, vault_root: Path, cfg: dict, utc_offset: str, rep: Report):
    """INV-08 (replay khớp card) + INV-21 (mastery_state khớp derive_mastery)."""
    rel = (lesson_dir / "lesson_state.md").relative_to(vault_root)
    tz = FA._parse_offset(utc_offset)
    known_cfg_version = cfg.get("fsrs_config_version")
    for rv in lesson.review_items:
        if rv.fsrs_config_version != known_cfg_version:  # INV-24
            rep.err("E-SCHEMA-OUTDATED", rel,
                    f"{rv.id}: fsrs_config_version {rv.fsrs_config_version} không có trong config "
                    f"(hiện {known_cfg_version})")
        stored = _card_to_dict(rv.card)
        log = [{"reviewed_at": e.reviewed_at, "rating": e.rating} for e in rv.log]
        if not log:
            # thẻ mầm chưa review: model đã ép nulls; kiểm state/step + coupling due_at_utc↔due_date↔created.
            # KHÔNG replay được giờ-trong-ngày của created (chỉ lưu ngày) → không so due_at_utc tuyệt đối,
            # nhưng VẪN ràng due_date = hình chiếu local của due_at_utc (spec 8.3) để hai field không lệch nhau.
            if rv.card.state != "Learning" or rv.card.step != 0:
                rep.err("E-REVIEW-MISCALC", rel, f"{rv.id}: item chưa review phải state=Learning/step=0")
            due_dt = datetime.strptime(rv.card.due_at_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if FA.due_date_local(due_dt, utc_offset) != rv.card.due_date:
                rep.err("E-REVIEW-MISCALC", rel,
                        f"{rv.id}: due_date {rv.card.due_date} != hình chiếu local của due_at_utc")
            if rv.card.due_date != rv.created:
                rep.err("E-REVIEW-MISCALC", rel,
                        f"{rv.id}: due_date {rv.card.due_date} != created {rv.created}")
        else:
            # seed due không ảnh hưởng kết quả replay (card mới stability=None) → dùng nửa đêm local.
            created_at = datetime.combine(rv.created, _dtime(0, 0), tzinfo=tz)
            replayed = FA.replay(created_at, log, cfg, utc_offset)
            if not FA.cards_equal(replayed, stored):
                rep.err("E-REVIEW-MISCALC", rel, f"{rv.id}: replay log không khớp card đã lưu")
        expected = FA.derive_mastery(stored, log, cfg)
        if expected != rv.mastery_state:
            rep.err("E-STATE-DERIVED", rel,
                    f"{rv.id}: mastery_state {rv.mastery_state!r} != derive_mastery {expected!r}")


def _check_topic_uniqueness(lesson_models, topic_dir: Path, vault_root: Path, rep: Report):
    """INV-04: rv-*/gap-* duy nhất trong phạm vi topic (cross-lesson)."""
    rel = topic_dir.relative_to(vault_root)
    for label, getter in (("rv", lambda L: [r.id for r in L.review_items]),
                          ("gap", lambda L: [g.id for g in L.open_gaps])):
        ids = [i for L, _ in lesson_models for i in getter(L)]
        dups = sorted({x for x in ids if ids.count(x) > 1})
        if dups:
            rep.err("E-ID-DUP", rel, f"{label}-id trùng cross-lesson trong topic: {dups}")


def _check_index(topic_state, folder_ids, lesson_models, vault_state, ts_rel, rep: Report):
    """INV-25: index lessons ↔ folder, status ↔ lesson_state, current_lesson ↔ vault_state."""
    index_ids = [e.id for e in topic_state.lessons]
    if sorted(index_ids) != sorted(folder_ids):
        rep.err("E-INDEX-MISMATCH", ts_rel,
                f"lessons index {sorted(index_ids)} != thư mục lessons/ {sorted(folder_ids)}")
    status_by_id = {L.lesson_id: L.status for L, _ in lesson_models}
    for e in topic_state.lessons:
        if e.id in status_by_id and e.status != status_by_id[e.id]:
            rep.err("E-INDEX-MISMATCH", ts_rel,
                    f"{e.id}: index status {e.status!r} != lesson_state {status_by_id[e.id]!r}")
    if vault_state is not None and vault_state.current_topic == topic_state.topic_id:
        if topic_state.current_lesson != vault_state.current_lesson:
            rep.err("E-INDEX-MISMATCH", ts_rel,
                    f"current_lesson {topic_state.current_lesson!r} != "
                    f"vault_state.current_lesson {vault_state.current_lesson!r}")


def _check_views(topic_state, lessons, ts_rel, rep: Report):
    """INV-09: deep-compare nội dung view TRƯỚC, rồi so hash (spec 4)."""
    regen = VW.regen_all(lessons, stage="core")

    rs = topic_state.review_schedule
    reg_rs = regen["review_schedule"]
    stored_items = [{"lesson_id": it.lesson_id, "item_id": it.item_id,
                     "due_date": it.due_date, "mastery_state": it.mastery_state}
                    for it in rs.items]
    if C.canonical_json(stored_items) != C.canonical_json(reg_rs["items"]):
        rep.err("E-VIEW-MISMATCH", ts_rel, "review_schedule.items khác object sinh lại", "review_schedule")
    elif rs.generated_from_hash != reg_rs["generated_from_hash"]:
        rep.err("E-VIEW-STALE", ts_rel, "review_schedule.generated_from_hash lệch nguồn", "review_schedule")

    asv = topic_state.assessment
    reg_as = regen["assessment"]
    content_ok = all(abs(getattr(asv, f"{ax}_avg") - reg_as[f"{ax}_avg"]) < 1e-9 for ax in VW.AXES)
    if not content_ok:
        rep.err("E-VIEW-MISMATCH", ts_rel, "assessment avg khác object sinh lại", "assessment")
    elif asv.generated_from_hash != reg_as["generated_from_hash"]:
        rep.err("E-VIEW-STALE", ts_rel, "assessment.generated_from_hash lệch nguồn", "assessment")


def _collect_all_lesson_ids(vault_root: Path) -> set:
    """Tập lesson_id THẬT trong vault: mọi topics/<topic>/lessons/<name>/ có lesson_state.md
    → '<topic>/<name>'. Dùng cho INV-03 (kiểm tồn tại prerequisites/current_lesson)."""
    ids: set = set()
    topics = vault_root / "topics"
    if not topics.is_dir():
        return ids
    for td in topics.iterdir():
        if not td.is_dir() or td.name.startswith((".", "_")):
            continue
        ldir = td / "lessons"
        if ldir.is_dir():
            for ld in ldir.iterdir():
                if ld.is_dir() and (ld / "lesson_state.md").is_file():
                    ids.add(f"{td.name}/{ld.name}")
    return ids


def _today_local(now, utc_offset: str):
    """today = ngày lịch THẬT theo utc_offset (spec §5.4/§8.5 dòng 559: INV-05 dùng ngày lịch thật,
    KHÔNG áp day_cutoff — mốc đó chỉ cho lọc 'ôn hôm nay'; hai mốc tách biệt, không trộn).
    now=None → đồng hồ thật (audit standalone); now aware bơm vào → tất định (transaction/test)."""
    if now is None:
        now = datetime.now(timezone.utc)
    return now.astimezone(FA._parse_offset(utc_offset)).date()


def _check_updated_not_future(model, rel, today_local, rep: Report):
    """INV-05 phần THỜI GIAN: `updated <= today`. Phần cấu trúc `created <= updated` đã ở model (thuần,
    parse-time). Phần này cần utc_offset + mốc now (cross-document) → thuộc validator, KHÔNG nhét vào
    model (giữ model tất định, không đồng hồ). today_local=None → bỏ qua (caller chưa cấp mốc)."""
    if today_local is None:
        return
    updated = getattr(model, "updated", None)
    if updated is not None and updated > today_local:
        rep.err("E-SCHEMA", rel,
                f"updated {updated} > today {today_local} (INV-05: created <= updated <= today)")


def _check_source_added_not_future(src_model, rel, today_local, rep: Report):
    """CR-0004: `sources[].added <= today` — mở rộng nguyên tắc toàn-vẹn-thời-gian của INV-05 sang nguồn
    (một dấu-thời-gian không-thể-tương-lai). Song song _check_updated_not_future: phần THỜI GIAN ở validator
    (cần utc_offset + mốc now cross-context), tái dùng _today_local. added=None → bỏ qua (Optional, spec §5.3);
    today_local=None → bỏ qua (caller chưa cấp mốc)."""
    if today_local is None or src_model is None:
        return
    for s in src_model.sources:
        if s.added is not None and s.added > today_local:
            rep.err("E-SCHEMA", rel,
                    f"source {s.id}: added {s.added} > today {today_local} (CR-0004: added <= today)")


def _check_curriculum(topic_dir: Path, vault_root: Path, rep: Report, all_lesson_ids: set):
    """Curriculum_Validator (Task 3) — ràng buộc NGỮ NGHĨA của curriculum.md mà model KHÔNG bắt.
    Model (M.Curriculum) đã lo cấu trúc (id pattern, order>=1, status Literal, updated>=created) → E-SCHEMA.
    Đây kiểm (mỗi loại một mã phân biệt, design R10.1):
      - id trùng giữa point            → E-CURR-DUP-ID
      - order không phải hoán vị 1..N  → E-CURR-ORDER
      - objective rỗng sau strip       → E-CURR-EMPTY-OBJECTIVE
    curriculum là TÙY CHỌN: không có file → không kiểm. `all_lesson_ids` để dành mã POINTER/LESSON-LINK
    (increment sau). 'Đủ sâu/rộng/chính xác nội dung' KHÔNG kiểm ở đây (Class D)."""
    cpath = topic_dir / "curriculum.md"
    if not cpath.is_file():
        return
    _, cur = _parse_state_model(cpath, vault_root, rep)  # sai cấu trúc → E-SCHEMA (đã phát)
    if cur is None:
        return
    rel = cpath.relative_to(vault_root)
    points = cur.points
    # E-CURR-DUP-ID: id duy nhất trong phạm vi curriculum
    ids = [p.id for p in points]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        rep.err("E-CURR-DUP-ID", rel, f"Curriculum_Point id trùng: {d!r}")
    # E-CURR-ORDER: order phải là hoán vị liên tục 1..N (không trùng, không hở)
    if sorted(p.order for p in points) != list(range(1, len(points) + 1)):
        rep.err("E-CURR-ORDER", rel,
                f"order phải là hoán vị 1..{len(points)} (không trùng/không hở), gặp {sorted(p.order for p in points)}")
    # E-CURR-EMPTY-OBJECTIVE: objective không rỗng
    for p in points:
        if not (p.objective or "").strip():
            rep.err("E-CURR-EMPTY-OBJECTIVE", rel, f"Curriculum_Point {p.id!r} có objective rỗng")
    # E-CURR-POINTER: current_point phải trỏ một Curriculum_Point tồn tại (INV-03, không dangling)
    if cur.current_point not in ids:
        rep.err("E-CURR-POINTER", rel,
                f"current_point {cur.current_point!r} không trỏ Curriculum_Point nào tồn tại (INV-03)")
    # E-CURR-LESSON-LINK: lesson_id (nếu có) phải trỏ lesson THẬT trên đĩa (INV-25; nguồn sự thật index = topic_state.lessons[])
    for p in points:
        if p.lesson_id and p.lesson_id not in all_lesson_ids:
            rep.err("E-CURR-LESSON-LINK", rel,
                    f"Curriculum_Point {p.id!r}: lesson_id {p.lesson_id!r} không trỏ lesson tồn tại (INV-25)")
    # E-CURR-REF-BROKEN: mỗi source_ref phải trỏ file TỒN TẠI (tương đối topic_dir; lát cắt reference/)
    # (đường dẫn tuyệt đối đã bị E-PORT-ABSPATH chặn ở _parse_state_model)
    for p in points:
        for ref in p.source_refs:
            if not (topic_dir / ref).is_file():
                rep.err("E-CURR-REF-BROKEN", rel,
                        f"Curriculum_Point {p.id!r}: source_ref {ref!r} không trỏ file tồn tại")


def _check_exam_results(topic_dir: Path, vault_root: Path, rep: Report, real_vault_root: Path | None = None):
    """Exam ref-integrity (Class A — E-EXAM-REF-BROKEN). exam_results.md (bản ghi CHẤM, metadata, TRONG
    vault) phải trỏ: (1) `ref` = bài nộp TỒN TẠI trong exam/ NGOÀI vault (đường dẫn tương đối, phải dùng
    '..' để ra khỏi vault — hợp lệ theo thiết kế); (2) `target` = topic hiện tại HOẶC một Curriculum_Point
    tồn tại. `verdict` là Class D (KHÔNG kiểm nội dung). exam_results.md TÙY CHỌN. Enforcement của schema
    exam_results (CR-0007) — như Task 3 (đọc-kiểm), không phải lệnh ghi.

    real_vault_root (DEC-073): khi validate chạy trên OVERLAY của transaction (vault_root = thư mục TEMP,
    KHÔNG có sibling exam/), truyền vào vault root THẬT trên đĩa để resolve ref bài nộp + exam/ về đúng vị
    trí thật. `ref` là tương đối topic_dir nên phải resolve từ topic dir THẬT (base/topics/<name>), không
    phải topic dir overlay. Mặc định None = standalone → dùng chính vault_root (hành vi cũ, layout-agnostic,
    KHÔNG dùng __file__ → giữ portability INV-16)."""
    epath = topic_dir / "exam_results.md"
    if not epath.is_file():
        return
    _, er = _parse_state_model(epath, vault_root, rep)  # sai cấu trúc → E-SCHEMA (đã phát); abspath → E-PORT-ABSPATH
    if er is None:
        return
    rel = epath.relative_to(vault_root)
    # target hợp lệ = tên topic HOẶC một Curriculum_Point tồn tại (đọc curriculum.md nếu có; lỗi của nó do _check_curriculum lo)
    valid_targets = {topic_dir.name}
    cpath = topic_dir / "curriculum.md"
    if cpath.is_file():
        _, cur = _parse_state_model(cpath, vault_root, Report())
        if cur is not None:
            valid_targets |= {p.id for p in cur.points}
    # Base THẬT để resolve ref (exam/ là sibling NGOÀI vault → không có trong overlay temp).
    base_vault = real_vault_root or vault_root
    real_topic = base_vault / topic_dir.relative_to(vault_root)  # topic dir thật (== topic_dir khi standalone)
    exam_root = (base_vault.parent / "exam").resolve()
    for r in er.results:
        rp = (real_topic / r.ref).resolve()
        under_exam = rp == exam_root or exam_root in rp.parents
        if not (under_exam and rp.exists()):
            rep.err("E-EXAM-REF-BROKEN", rel,
                    f"exam {r.submission_id!r}: ref {r.ref!r} không trỏ bài nộp tồn tại trong exam/")
        if r.target not in valid_targets:
            rep.err("E-EXAM-REF-BROKEN", rel,
                    f"exam {r.submission_id!r}: target {r.target!r} không phải topic/Curriculum_Point tồn tại")


def _validate_topic(topic_dir: Path, vault_root: Path, vault_state, cfg: dict,
                    utc_offset: str, rep: Report, all_lesson_ids: set, today_local=None,
                    real_vault_root: Path | None = None):
    ts_path = topic_dir / "topic_state.md"
    topic_state = None
    if ts_path.is_file():
        _, topic_state = _parse_state_model(ts_path, vault_root, rep)
        if topic_state is not None:  # INV-05 (updated<=today) cho topic_state
            _check_updated_not_future(topic_state, ts_path.relative_to(vault_root), today_local, rep)
    else:
        rep.err("E-INDEX-MISMATCH", topic_dir.relative_to(vault_root), "thiếu topic_state.md")

    src_path = topic_dir / "sources.md"
    if src_path.is_file():
        _, src_model = _parse_state_model(src_path, vault_root, rep)
        _check_source_added_not_future(src_model, src_path.relative_to(vault_root), today_local, rep)  # CR-0004

    lessons_dir = topic_dir / "lessons"
    lesson_models: list[tuple] = []
    folder_ids: list[str] = []
    if lessons_dir.is_dir():
        for ld in sorted(p for p in lessons_dir.iterdir() if p.is_dir()):
            expected_id = f"{topic_dir.name}/{ld.name}"
            folder_ids.append(expected_id)
            lp = ld / "lesson_state.md"
            if not lp.is_file():
                rep.err("E-INDEX-MISMATCH", ld.relative_to(vault_root), "thiếu lesson_state.md")
                continue
            _, lm = _parse_state_model(lp, vault_root, rep)
            body = ld / "lesson.md"
            if body.is_file():
                _validate_lesson_body(body, vault_root, rep)
            if lm is None:
                continue
            lesson_models.append((lm, ld))
            _check_updated_not_future(lm, lp.relative_to(vault_root), today_local, rep)  # INV-05 updated<=today
            if lm.lesson_id != expected_id:  # INV-02
                rep.err("E-ID-PATH", lp.relative_to(vault_root),
                        f"lesson_id {lm.lesson_id!r} != đường dẫn {expected_id!r}")
            _check_lesson_local_ids(lm, lp.relative_to(vault_root), rep)  # INV-10/04 (in-lesson)
            _check_prompt_refs(lm, ld, vault_root, rep)          # INV-03/20
            _check_replay(lm, ld, vault_root, cfg, utc_offset, rep)  # INV-08/21
            for pre in lm.prerequisites:                          # INV-03: prerequisite tồn tại
                if pre not in all_lesson_ids:
                    rep.err("E-REF-BROKEN", lp.relative_to(vault_root),
                            f"prerequisite {pre!r} không trỏ tới lesson tồn tại (INV-03)")

    _check_topic_uniqueness(lesson_models, topic_dir, vault_root, rep)  # INV-04
    if topic_state is not None:
        ts_rel = ts_path.relative_to(vault_root)
        if topic_state.current_lesson and topic_state.current_lesson not in all_lesson_ids:  # INV-03
            rep.err("E-REF-BROKEN", ts_rel,
                    f"current_lesson {topic_state.current_lesson!r} không trỏ tới lesson tồn tại (INV-03)")
        _check_index(topic_state, folder_ids, lesson_models, vault_state, ts_rel, rep)  # INV-25
        _check_views(topic_state, [L for L, _ in lesson_models], ts_rel, rep)           # INV-09
    _check_curriculum(topic_dir, vault_root, rep, all_lesson_ids)  # Task 3: E-CURR-* (curriculum.md tùy chọn)
    _check_exam_results(topic_dir, vault_root, rep, real_vault_root)  # Task 8.1/DEC-073: E-EXAM-REF-BROKEN (exam_results.md tùy chọn)


# --- INV-17/18: tách bạch hai gốc (E-MIX-*) -----------------------------
_VAULT_FORBIDDEN_DIRS = {".git", "node_modules", ".venv", "venv", "site-packages",
                         "__pycache__", ".idea", ".vscode", "dist", "build", "target", ".pytest_cache"}
_VAULT_FORBIDDEN_EXT = {".py", ".pyc", ".pyo", ".js", ".mjs", ".ts", ".jar", ".class",
                        ".exe", ".dll", ".so", ".o", ".a", ".bin", ".whl", ".egg"}
_VAULT_FORBIDDEN_NAMES = {"package.json", "package-lock.json", "yarn.lock", "requirements.txt",
                          "pyproject.toml", "cargo.toml", "cargo.lock", "go.mod", "go.sum",
                          "pom.xml", "gemfile", "gemfile.lock", "uv.lock"}
_SYSTEM_DATA_NAMES = {"vault_state.md", "topic_state.md", "lesson_state.md", "sources.md",
                      "lesson.md", "lesson_notes.md", "topic.md",
                      "curriculum.md", "exam_results.md",  # CR-0007 (data-file mới)
                      "blueprint.md"}  # CR-0011 (Topic_Blueprint data-file)
_SYSTEM_SKIP_DIRS = {"validator", ".venv", "venv", "__pycache__", ".pytest_cache",
                     ".cache", ".tx", "repo_lab", ".git"}


def _check_no_code_in_vault(vault_root: Path, rep: Report):
    """INV-17: learning_vault/ chỉ chứa dữ liệu học portable (markdown), KHÔNG repo/dependency/code.
    Bỏ vùng transient _scratch/.tx (INV-20). Vi phạm → E-MIX-CODE."""
    for dirpath, dirnames, filenames in os.walk(vault_root):
        dirnames[:] = sorted(d for d in dirnames if d not in {"_scratch", ".tx"})  # sort: descent tất định
        rel_dir = Path(dirpath).relative_to(vault_root)
        for d in list(dirnames):
            if d in _VAULT_FORBIDDEN_DIRS:
                rep.err("E-MIX-CODE", (rel_dir / d).as_posix(),
                        f"thư mục code/dependency trong vault: {d!r} (INV-17)")
                dirnames.remove(d)  # không cần lội vào
        for fn in sorted(filenames):  # sort: thứ tự lỗi tất định cross-machine (os.walk trả theo FS)
            if Path(fn).suffix.lower() in _VAULT_FORBIDDEN_EXT or fn.lower() in _VAULT_FORBIDDEN_NAMES:
                rep.err("E-MIX-CODE", (rel_dir / fn).as_posix(),
                        f"file code/dependency trong vault: {(rel_dir / fn).as_posix()} (INV-17)")


def _check_no_data_in_system(system_root: Path, rep: Report):
    """INV-18: _system/ KHÔNG chứa dữ liệu học/cá nhân (file *_state.md, lesson/topic md, thư mục topics/).
    Bỏ vùng công cụ (validator/.venv/repo_lab/cache/.tx...). Vi phạm → E-MIX-DATA."""
    for dirpath, dirnames, filenames in os.walk(system_root):
        dirnames[:] = sorted(d for d in dirnames if d not in _SYSTEM_SKIP_DIRS)  # sort: descent tất định
        rel_dir = Path(dirpath).relative_to(system_root)
        for d in list(dirnames):
            if d == "topics":
                rep.err("E-MIX-DATA", (rel_dir / d).as_posix(),
                        "thư mục dữ liệu học 'topics/' trong _system (INV-18)")
                dirnames.remove(d)
        for fn in sorted(filenames):  # sort: thứ tự lỗi tất định cross-machine
            if fn.lower() in _SYSTEM_DATA_NAMES:
                rep.err("E-MIX-DATA", (rel_dir / fn).as_posix(),
                        f"file dữ liệu học trong _system: {(rel_dir / fn).as_posix()} (INV-18)")


def _read_system_version(system_root: Path):
    """Đọc _system/VERSION (số nguyên schema version của hệ thống). None nếu thiếu/hỏng."""
    p = Path(system_root) / "VERSION"
    if not p.is_file():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _check_schema_version(vault_state, system_root: Path, rep: Report):
    """INV-19: vault_state.schema_version tương thích _system/VERSION.
    Dùng SỐ NGUYÊN (nhất quán model + migration vN→vN+1 mục 10.7; spec ghi 'semver' là dòng
    tự mâu thuẫn cần dọn). vault < system → E-SCHEMA-OUTDATED (cần migration);
    vault > system → E-SCHEMA-AHEAD (chặn ghi bằng luật cũ)."""
    sysver = _read_system_version(system_root)
    if sysver is None:
        rep.err("E-SCHEMA-CONFIG", "VERSION", "thiếu/hỏng _system/VERSION (INV-19)")
        return
    v = vault_state.schema_version
    if v < sysver:
        rep.err("E-SCHEMA-OUTDATED", "vault_state.md",
                f"vault schema_version {v} < system {sysver} — cần migration (INV-19)")
    elif v > sysver:
        rep.err("E-SCHEMA-AHEAD", "vault_state.md",
                f"vault schema_version {v} > system {sysver} — vault mới hơn hệ thống (INV-19)")


def validate_full_core(system_root: Path, vault_root: Path, rep: Report, now=None,
                       real_vault_root: Path | None = None):
    """Biên: bọc EIoEncoding → E-IO-ENCODING (không để non-UTF-8 crash validator).
    real_vault_root (DEC-073): vault root THẬT khi validate chạy trên overlay transaction (xem
    _check_exam_results). None = standalone."""
    try:
        _validate_full_core_impl(system_root, vault_root, rep, now=now, real_vault_root=real_vault_root)
    except VIO.EIoEncoding as e:
        _emit_io_encoding(e, vault_root, rep)


def _validate_full_core_impl(system_root: Path, vault_root: Path, rep: Report, now=None,
                             real_vault_root: Path | None = None):
    _, warns = VIO.discover_md(vault_root)
    rep.warnings.extend(warns)
    _check_no_code_in_vault(vault_root, rep)       # INV-17
    _check_no_data_in_system(Path(system_root), rep)  # INV-18

    vs_path = vault_root / "vault_state.md"
    vault_state = None
    if vs_path.is_file():
        _, vault_state = _parse_state_model(vs_path, vault_root, rep)
    else:
        rep.err("E-SCHEMA", "vault_state.md", "thiếu vault_state.md ở gốc vault")
    all_lesson_ids = _collect_all_lesson_ids(vault_root)
    if vault_state is not None:
        _check_schema_version(vault_state, system_root, rep)  # INV-19
        if vault_state.current_lesson and vault_state.current_lesson not in all_lesson_ids:  # INV-03
            rep.err("E-REF-BROKEN", "vault_state.md",
                    f"current_lesson {vault_state.current_lesson!r} không trỏ tới lesson tồn tại (INV-03)")
        os_lesson = vault_state.open_session.lesson_id  # INV-03 ('mọi tham chiếu'): open_session không dangling
        if os_lesson and os_lesson not in all_lesson_ids:
            rep.err("E-REF-BROKEN", "vault_state.md",
                    f"open_session.lesson_id {os_lesson!r} không trỏ tới lesson tồn tại (INV-03)")
        cur_topic = vault_state.current_topic  # INV-03: current_topic trỏ topic tồn tại (kiểm DIR — topic rỗng vẫn hợp lệ)
        if cur_topic and not (vault_root / "topics" / cur_topic).is_dir():
            rep.err("E-REF-BROKEN", "vault_state.md",
                    f"current_topic {cur_topic!r} không trỏ tới topic tồn tại (INV-03)")
    utc_offset = vault_state.utc_offset if vault_state is not None else "+00:00"
    today_local = _today_local(now, utc_offset)  # INV-05: mốc 'today' (ngày lịch thật theo offset)

    try:
        cfg = FA.load_config(system_root / "fsrs_config.yaml")
    except FileNotFoundError:
        rep.err("E-SCHEMA-CONFIG", "fsrs_config.yaml", f"không thấy fsrs_config.yaml trong {system_root}")
        return

    topics_dir = vault_root / "topics"
    if topics_dir.is_dir():
        for td in sorted(p for p in topics_dir.iterdir()
                         if p.is_dir() and not p.name.startswith((".", "_"))):
            _validate_topic(td, vault_root, vault_state, cfg, utc_offset, rep, all_lesson_ids,
                            today_local, real_vault_root=real_vault_root)


# ========================================================================
# FULL --scope full (P07b) — SEMANTIC. Cụm 1: cổng "đã hiểu" + evidence + verbatim.
# ========================================================================
# Ngưỡng cổng learned_gate (spec 9.3). critique=1, còn lại=2.
_GATE = {"concept": 2, "explain": 2, "apply": 2, "critique": 1, "teachback": 2}


def _check_gate_and_evidence(lesson, lesson_dir: Path, vault_root: Path, rep: Report):
    """INV-07 (E-GATE-FAIL), INV-22 (E-ASSESS-NOEVIDENCE), INV-22b (E-ASSESS-FAKEQUOTE).
    Nguồn evidence/transcript = lesson.md body (AST semantic P04b)."""
    rel = (lesson_dir / "lesson_state.md").relative_to(vault_root)
    body_path = lesson_dir / "lesson.md"
    text = VIO.read_text(body_path) if body_path.is_file() else ""
    evidence = A.extract_evidence(text)
    answers = A.extract_answer_blocks(text)

    # INV-07: status=learned ⇒ mọi trục đạt ngưỡng cổng.
    if lesson.status == "learned":
        for ax, thr in _GATE.items():
            if getattr(lesson.mastery, ax).score < thr:
                rep.err("E-GATE-FAIL", rel,
                        f"status=learned nhưng {ax}={getattr(lesson.mastery, ax).score} < ngưỡng {thr} (INV-07)")

    # INV-22: mỗi trục đạt ngưỡng cổng phải có ≥1 evidence axis khớp, quote không rỗng.
    ev_by_axis: dict = {}
    for ev in evidence:
        ev_by_axis.setdefault(ev.get("axis"), []).append(ev)
    for ax, thr in _GATE.items():
        if getattr(lesson.mastery, ax).score >= thr:
            has = [e for e in ev_by_axis.get(ax, []) if (e.get("quote") or "").strip()]
            if not has:
                rep.err("E-ASSESS-NOEVIDENCE", rel,
                        f"trục {ax}={getattr(lesson.mastery, ax).score} >= ngưỡng {thr} nhưng thiếu evidence (INV-22)")

    # INV-22b: mọi evidence.quote phải ⊆ transcript MỘT answer block (sau normalize_for_match, spec 9.6).
    norm_blocks = [C.normalize_for_match(t) for t in answers.values()]
    for ev in evidence:
        q = (ev.get("quote") or "").strip()
        if not q:
            continue
        nq = C.normalize_for_match(q)
        if not any(nq and nq in nb for nb in norm_blocks):
            rep.err("E-ASSESS-FAKEQUOTE", rel,
                    f"evidence {ev.get('id')!r}: quote không phải chuỗi con của transcript nào (INV-22b)")


# --- Claims (P07b-2a): INV-15 (cấu trúc) + INV-14 (tiền đề C) ------------
_CLAIM_CLASSES = {"A", "B", "C", "D"}
_CLAIM_STATUS = {"draft", "confirmed"}


def _collect_topic_claims(topic_dir: Path, vault_root: Path) -> list:
    """Gom mọi claim của topic (topic.md + lesson_notes.md từng lesson) kèm file gốc.
    Trả list[(claim_dict, file_rel)]. Claim chỉ hợp lệ trong '## Claims' của 2 loại file này (spec 5.5)."""
    files = [topic_dir / "topic.md"]
    lessons_dir = topic_dir / "lessons"
    if lessons_dir.is_dir():
        for ld in sorted(p for p in lessons_dir.iterdir() if p.is_dir()):
            files.append(ld / "lesson_notes.md")
    out = []
    for f in files:
        if f.is_file():
            rel = f.relative_to(vault_root)
            for c in A.extract_claims(VIO.read_text(f)):
                out.append((c, rel))
    return out


def _anchor_confirmed_valid(ref: str, sources: dict) -> bool:
    """ref 'src-XXX#aY' trỏ nguồn confirmed + anchor tồn tại + quote không rỗng (INV-12)."""
    if "#" not in ref:
        return False
    sid, aid = ref.split("#", 1)
    src = sources.get(sid)
    if src is None or src.status != "confirmed":
        return False
    anchor = next((a for a in src.anchors if a.id == aid), None)
    return anchor is not None and bool((anchor.quote or "").strip())


def _check_claims(collected: list, rep: Report, sources: dict | None = None):
    """INV-15 (cấu trúc), INV-14 (tiền đề C), INV-12/13 (nguồn — chỉ khi `sources` được cấp).
    sources: {src_id: Source model}. None = bỏ qua INV-12/13 (dùng cho unit test cấu trúc)."""
    by_id = {c.get("id"): c for c, _ in collected if c.get("id")}
    for c, rel in collected:
        cid = c.get("id")
        cls = c.get("class")
        status = c.get("status")
        # INV-15 — cấu trúc
        for field in ("id", "status", "text"):
            if not c.get(field):
                rep.err("E-CLAIM-UNCLASSED", rel, f"claim {cid!r} thiếu '{field}' (INV-15)")
        if cls not in _CLAIM_CLASSES:
            rep.err("E-CLAIM-UNCLASSED", rel, f"claim {cid!r} thiếu/không hợp lệ 'class' (INV-15)")
        if status not in _CLAIM_STATUS:
            rep.err("E-CLAIM-UNCLASSED", rel, f"claim {cid!r} 'status' không hợp lệ: {status!r} (INV-15)")
        if status == "draft" and not c.get("draft_reason"):
            rep.err("E-CLAIM-DRAFTREASON", rel, f"claim {cid!r} status=draft nhưng thiếu draft_reason (INV-15)")
        # INV-14 — tiền đề của C confirmed
        if status == "confirmed" and cls == "C":
            premises = c.get("premise_refs") or []
            if not premises:
                rep.err("E-CLAIM-WEAKBASE", rel, f"claim {cid!r} (C confirmed) không có tiền đề (INV-14)")
            for pid in premises:
                p = by_id.get(pid)
                if p is None or p.get("class") not in ("A", "B") or p.get("status") != "confirmed":
                    rep.err("E-CLAIM-WEAKBASE", rel,
                            f"claim {cid!r}: tiền đề {pid!r} không phải claim A/B confirmed (INV-14)")
        # INV-13 — không dùng nguồn raw/rejected làm anchor (mọi claim có source_refs)
        if sources is not None:
            for ref in (c.get("source_refs") or []):
                sid = ref.split("#", 1)[0]
                src = sources.get(sid)
                if src is not None and src.status in ("raw", "rejected"):
                    rep.err("E-SRC-RAWUSED", rel,
                            f"claim {cid!r}: dùng nguồn {sid!r} status={src.status} làm anchor (INV-13)")
        # INV-12 — B confirmed cần >=1 anchor nguồn confirmed hợp lệ
        if sources is not None and status == "confirmed" and cls == "B":
            refs = c.get("source_refs") or []
            if not any(_anchor_confirmed_valid(r, sources) for r in refs):
                rep.err("E-CLAIM-NOSRC", rel,
                        f"claim {cid!r} (B confirmed) không có anchor nguồn confirmed hợp lệ (INV-12)")


def _check_claim_location(topic_dir: Path, vault_root: Path, rep: Report):
    """INV-23 (E-CLAIM-LOC): claim chỉ được ở '## Claims' (level 2) của topic.md/lesson_notes.md.
    - Trong topic.md/lesson_notes.md: mọi fence 'claims:' không dưới '## Claims' → E-CLAIM-LOC.
    - Trong lesson.md (không được chứa claim): bất kỳ fence 'claims:' → E-CLAIM-LOC."""
    def _scan(path: Path, allow_claims_section: bool):
        if not path.is_file():
            return
        rel = path.relative_to(vault_root)
        for gov_text, gov_level in A.find_claims_fences(VIO.read_text(path)):
            ok = allow_claims_section and gov_text == "Claims" and gov_level == 2
            if not ok:
                where = f"dưới '{gov_text}'" if gov_text else "ngoài mọi heading"
                rep.err("E-CLAIM-LOC", rel, f"claim đặt sai vùng ({where}); chỉ được trong '## Claims' (INV-23)")

    _scan(topic_dir / "topic.md", allow_claims_section=True)
    lessons_dir = topic_dir / "lessons"
    if lessons_dir.is_dir():
        for ld in sorted(p for p in lessons_dir.iterdir() if p.is_dir()):
            _scan(ld / "lesson_notes.md", allow_claims_section=True)
            _scan(ld / "lesson.md", allow_claims_section=False)


def _check_draft_map(topic_dir: Path, vault_root: Path, collected: list, rep: Report):
    """INV-26 (E-DRAFT-IN-MAP): draft KHÔNG được vào '## Knowledge Map' của topic.md;
    và topic_state.has_draft_knowledge phải khớp việc còn/không claim draft."""
    tmd = topic_dir / "topic.md"
    draft_ids = [c.get("id") for c, _ in collected if c.get("status") == "draft" and c.get("id")]
    if tmd.is_file():
        km = A.extract_section_text(VIO.read_text(tmd), "Knowledge Map", level=2)
        if km:
            rel = tmd.relative_to(vault_root)
            for did in draft_ids:
                if did in km:
                    rep.err("E-DRAFT-IN-MAP", rel,
                            f"claim draft {did!r} xuất hiện trong '## Knowledge Map' (INV-26)")
    # has_draft_knowledge view phải đúng
    ts_path = topic_dir / "topic_state.md"
    if ts_path.is_file():
        _, ts = _parse_state_model(ts_path, vault_root, Report())  # nháp: core đã báo lỗi schema
        if ts is not None:
            # cùng logic với views.build_has_draft_knowledge (đếm mọi status=draft, không lọc theo id)
            # để bên-sinh và bên-kiểm không lệch khi có draft claim thiếu id.
            actual = any(c.get("status") == "draft" for c, _ in collected)
            if ts.has_draft_knowledge != actual:
                rep.err("E-DRAFT-IN-MAP", ts_path.relative_to(vault_root),
                        f"has_draft_knowledge={ts.has_draft_knowledge} != thực tế còn draft={actual} (INV-26)")


def validate_full_semantic(system_root: Path, vault_root: Path, rep: Report, now=None,
                           real_vault_root: Path | None = None):
    """Biên: bọc EIoEncoding → E-IO-ENCODING (không để non-UTF-8 crash validator).
    real_vault_root (DEC-073): vault root THẬT khi validate chạy trên overlay transaction (xem
    _check_exam_results). None = standalone."""
    try:
        _validate_full_semantic_impl(system_root, vault_root, rep, now=now, real_vault_root=real_vault_root)
    except VIO.EIoEncoding as e:
        _emit_io_encoding(e, vault_root, rep)


def _validate_full_semantic_impl(system_root: Path, vault_root: Path, rep: Report, now=None,
                                 real_vault_root: Path | None = None):
    """P07b: core + semantic. Semantic pass tự parse lại model bằng report nháp (tránh nhân đôi
    lỗi schema đã báo ở core), chỉ chạy INV ngữ nghĩa trên model parse thành công."""
    validate_full_core(system_root, vault_root, rep, now=now, real_vault_root=real_vault_root)
    topics_dir = vault_root / "topics"
    if not topics_dir.is_dir():
        return
    for td in sorted(p for p in topics_dir.iterdir()
                     if p.is_dir() and not p.name.startswith((".", "_"))):
        lessons_dir = td / "lessons"
        if lessons_dir.is_dir():
            for ld in sorted(p for p in lessons_dir.iterdir() if p.is_dir()):
                lp = ld / "lesson_state.md"
                if not lp.is_file():
                    continue
                _, lm = _parse_state_model(lp, vault_root, Report())  # report nháp: không nhân đôi lỗi core
                if lm is not None:
                    _check_gate_and_evidence(lm, ld, vault_root, rep)
        # nguồn của topic (INV-12/13): parse lại bằng report nháp (core đã báo lỗi schema nếu có).
        # sources.md vắng → {} (B confirmed vẫn phải có nguồn → E-CLAIM-NOSRC), KHÔNG None (None=bỏ qua).
        sources_index: dict = {}
        sp = td / "sources.md"
        if sp.is_file():
            _, src_model = _parse_state_model(sp, vault_root, Report())
            if src_model is not None:
                sources_index = {s.id: s for s in src_model.sources}
        collected = _collect_topic_claims(td, vault_root)
        _check_claims(collected, rep, sources_index)   # INV-15/14/12/13
        _check_claim_location(td, vault_root, rep)     # INV-23
        _check_draft_map(td, vault_root, collected, rep)  # INV-26


def main(argv=None):
    # Ép stdout UTF-8: report chứa tiếng Việt, console Windows mặc định cp1252 → UnicodeEncodeError.
    # Sửa ở một nơi thay vì bọc từng print (root-cause, không vá ngọn).
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True)
    ap.add_argument("--vault", required=True)
    ap.add_argument("--level", choices=["light", "full"], default="full")
    ap.add_argument("--scope", choices=["core", "full"], default="core")
    ap.add_argument("--file", default=None)
    ap.add_argument("--at", default=None,
                    help="ISO 8601 aware; mốc 'today' cho INV-05 (mặc định = now UTC thật). Vd '2026-07-04T10:00:00+07:00'")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    now = None
    if args.at:
        try:
            now = datetime.fromisoformat(args.at)
            if now.tzinfo is None:
                raise ValueError("--at phải kèm offset (aware)")
        except ValueError as e:
            print(f"FAIL — [E-ARG] --at không hợp lệ: {e}")
            return 2

    rep = Report()
    vault_root = Path(args.vault)
    if args.level == "light":
        validate_light(vault_root, Path(args.file) if args.file else None, rep)
    elif args.scope == "core":
        validate_full_core(Path(args.system), vault_root, rep, now=now)
    else:
        validate_full_semantic(Path(args.system), vault_root, rep, now=now)
    rep.dump(args.json)
    return 0 if rep.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
