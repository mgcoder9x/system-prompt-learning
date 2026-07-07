"""P10 driver — session.py: /review /done chạy transaction-FULL thật (spec 11A, 10.3, 14).

Nguyên tắc gốc:
- Dùng CHUNG convention replay với validator (_check_replay): card sinh từ local-midnight của `created`
  ⇒ INV-08 đúng by-construction, KHÔNG tự chế convention riêng.
- Validator là LƯỚI AN TOÀN: driver đề xuất writes → Transaction.validate_staged (FULL = core+semantic,
  toàn bộ INV-01..26 theo spec 10.8) → chỉ commit khi PASS; sai → ABORT, file thật không đổi.
- /review /done là transaction 1-GỐC (vault): chỉ đụng lesson_state + topic_state (+open_session).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, time as _dtime, timezone
from pathlib import Path

import yaml

import fsrs_adapter as FA
import models as M
import views as VW
import vault_io as VIO
import transaction as TX
import validate as V
import schedule as SCHED


# ---- helpers: card <-> yaml -------------------------------------------
def _card_for_yaml(card: dict) -> dict:
    """due_date str → date obj (model strict cần date); giữ str cho *_at_utc; float|None giữ nguyên."""
    from datetime import date
    return {
        "state": card["state"],
        "step": card["step"],
        "stability": card["stability"],
        "difficulty": card["difficulty"],
        "due_at_utc": card["due_at_utc"],
        "due_date": date.fromisoformat(card["due_date"]),
        "last_reviewed_at_utc": card["last_reviewed_at_utc"],
    }


class SessionError(Exception):
    """Lỗi vận hành driver (báo qua main() → E-DRIVER trừ khi có error_code riêng)."""


class SchemaError(SessionError):
    """Driver đọc file on-disk hỏng (thiếu front-matter / YAML hỏng / schema sai).
    Mang error_code chuẩn (E-SCHEMA / E-SCHEMA-YAML) + path để main() báo SẠCH, KHÔNG crash traceback.
    Bản chất: tầng đọc-parse của driver phải suy biến duyên dáng giống validator (spec §10.4/§10.6/§19)."""
    def __init__(self, path, error_code: str, message: str):
        self.path = path
        self.error_code = error_code
        super().__init__(f"{path}: {message}" if path else message)


def _split(text: str):
    """('---', fm_str, body) với body giữ nguyên phần sau front-matter."""
    parts = text.split("---", 2)
    return parts[1], parts[2]  # fm, body


def _dump_state(raw: dict, body: str) -> bytes:
    fm = yaml.safe_dump(raw, sort_keys=False, allow_unicode=True)
    return ("---\n" + fm + "---" + body).encode("utf-8")


def _load_raw(path: Path) -> tuple[dict, str]:
    text = VIO.read_text(path)
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SchemaError(path, "E-SCHEMA", "thiếu front-matter '---' (không tách được YAML/body)")
    fm, body = parts[1], parts[2]
    try:
        raw = yaml.safe_load(fm) or {}
    except yaml.YAMLError as e:
        raise SchemaError(path, "E-SCHEMA-YAML", f"front-matter YAML hỏng: {e}")
    if not isinstance(raw, dict):
        raise SchemaError(path, "E-SCHEMA", "front-matter không phải mapping YAML")
    return raw, body


def _lesson_model_from_raw(raw: dict, path=None) -> M.LessonState:
    from canonical import normalize_yaml_object
    try:
        return M.LessonState(**normalize_yaml_object(raw, str_fields=V._STR_FIELDS))
    except SchemaError:
        raise
    except Exception as e:  # pydantic ValidationError, type/normalize errors → mã lỗi sạch
        msg = str(e).splitlines()[0] if str(e) else repr(e)
        raise SchemaError(path, "E-SCHEMA", msg)


def _load_vault_state(vault: Path) -> tuple[dict, str]:
    """Đọc vault_state.md → (raw, body), NHƯNG validate cấu trúc qua M.VaultState TRƯỚC.
    Bản chất: lệnh đọc vault_state như raw dict rồi giả định kiểu field (open_session.get,
    '/' in current_lesson) — nếu YAML hợp lệ mà SAI KIỂU (open_session=chuỗi, current_lesson=int)
    thì crash AttributeError/TypeError thô. Validate qua model (cùng normalize như validator,
    KHÔNG lossy-coerce current_lesson/current_topic) → sai kiểu ra E-SCHEMA sạch, nhất quán validator.
    Trả raw để lệnh dùng/ghi (raw đã đảm bảo đúng kiểu sau khi model PASS)."""
    vs = Path(vault) / "vault_state.md"
    raw, body = _load_raw(vs)  # đã guard thiếu-fm / YAMLError / non-dict
    from canonical import normalize_yaml_object
    try:
        M.VaultState(**normalize_yaml_object(raw, str_fields=V._STR_FIELDS))
    except Exception as e:
        msg = str(e).splitlines()[0] if str(e) else repr(e)
        raise SchemaError(vs, "E-SCHEMA", msg)
    return raw, body


def _require_list_of_maps(value, field: str, path) -> None:
    """Guard cấu trúc: `value` phải là list các mapping (dict). Sai → SchemaError E-SCHEMA sạch.
    Dùng cho collection AUTHORED mà driver ITERATE trên raw TRƯỚC khi model/regen kịp bắt
    (chống crash AttributeError/KeyError khi field sai kiểu — YAML hợp lệ nhưng không phải list-of-map)."""
    if not isinstance(value, list) or not all(isinstance(e, dict) for e in value):
        raise SchemaError(path, "E-SCHEMA", f"{field} phải là list các mapping")


def _load_topic_state(path: Path) -> tuple[dict, str]:
    """Đọc topic_state → (raw, body); validate INDEX 'lessons' (authored) qua M.LessonIndexEntry
    (đảm bảo mỗi entry có id:str + status:enum → driver iterate/e['id'] an toàn). CỐ Ý KHÔNG validate
    review_schedule/assessment (view regen GHI ĐÈ — validate cả model sẽ chặn nhầm self-heal view corrupt).
    Sai-kiểu lessons → E-SCHEMA sạch thay crash AttributeError/KeyError."""
    raw, body = _load_raw(path)
    lessons = raw.get("lessons", [])
    if not isinstance(lessons, list):
        raise SchemaError(path, "E-SCHEMA", "topic_state.lessons phải là list")
    try:
        for e in lessons:
            if not isinstance(e, dict):
                raise TypeError("mỗi phần tử 'lessons' phải là mapping")
            M.LessonIndexEntry(**e)
    except Exception as ex:
        msg = str(ex).splitlines()[0] if str(ex) else repr(ex)
        raise SchemaError(path, "E-SCHEMA", f"topic_state.lessons không hợp lệ: {msg}")
    return raw, body


def _load_model_validated(path: Path, model) -> tuple[dict, str]:
    """Đọc file state → (raw, body), NHƯNG validate cấu trúc qua `model` (pydantic) TRƯỚC (cùng khuôn
    _load_vault_state/_load_topic_state, DEC-042/043). Bản chất: lệnh GHI iterate RAW collection + phần tử
    .get('id')/... — nếu sai kiểu (list non-dict / không phải list, YAML HỢP LỆ nhưng sửa-tay-hỏng) sẽ crash
    AttributeError thô. Validate qua model → E-SCHEMA sạch (SchemaError ⊂ SessionError → main() báo sạch,
    KHÔNG crash — NOTE-018). Trả raw để lệnh thao tác/ghi (raw đã đảm bảo đúng kiểu sau khi model PASS)."""
    raw, body = _load_raw(path)  # guard thiếu-fm / YAMLError / non-dict
    from canonical import normalize_yaml_object
    try:
        model(**normalize_yaml_object(raw, str_fields=V._STR_FIELDS))
    except SchemaError:
        raise
    except Exception as e:
        msg = str(e).splitlines()[0] if str(e) else repr(e)
        raise SchemaError(path, "E-SCHEMA", msg)
    return raw, body


def _load_curriculum_validated(cpath: Path) -> tuple[dict, str]:
    """curriculum.md validate qua M.Curriculum (xem _load_model_validated) — dùng cho insert/next_lesson."""
    return _load_model_validated(cpath, M.Curriculum)


# ---- templates (spec §2/§3, DEC-013): instantiate .template.md ---------
def _fill_template(text: str, subst: dict) -> str:
    for k, v in subst.items():
        text = text.replace(k, str(v))
    return text


def _yaml_scalar(v) -> str:
    """Serialize v thành scalar YAML AN TOÀN (JSON là tập con YAML flow) → chống ':','#','\"',... phá
    front-matter khi thay giá trị free-text người-dùng vào template (bug phát hiện ở walkthrough Q5)."""
    import json
    return json.dumps(str(v), ensure_ascii=False)


def _fill_frontmatter(fm_text: str, subst: dict, text_keys: set) -> str:
    """Thay placeholder trong FRONT-MATTER: free-text (text_keys) → scalar YAML-safe; còn lại (id/date) → raw
    (date phải giữ kiểu date, slug id an toàn)."""
    for k, v in subst.items():
        fm_text = fm_text.replace(k, _yaml_scalar(v) if k in text_keys else str(v))
    return fm_text


def _template_text(system: Path, subst: dict, *parts: str) -> str:
    """Đọc _system/templates/<parts>.template.md rồi thay placeholder (body markdown, raw). KHÔNG parse."""
    raw = VIO.read_text(Path(system) / "templates" / Path(*parts))
    return _fill_template(raw, subst)


def _template_state(system: Path, subst: dict, *parts: str, text_keys=()) -> tuple[dict, str]:
    """Template có front-matter → (raw_dict, body). Front-matter: free-text thay YAML-safe (chống ký tự
    đặc biệt phá YAML); body markdown: raw. text_keys = tập placeholder của giá trị free-text người-dùng."""
    raw = VIO.read_text(Path(system) / "templates" / Path(*parts))
    fm_t, body_t = _split(raw)
    fm = _fill_frontmatter(fm_t, subst, set(text_keys))
    return yaml.safe_load(fm) or {}, _fill_template(body_t, subst)


# ---- topic paths --------------------------------------------------------
def _topic_of(lesson_id: str) -> str:
    return lesson_id.split("/", 1)[0]


def _lesson_dir(vault: Path, lesson_id: str) -> Path:
    topic, name = lesson_id.split("/", 1)
    return vault / "topics" / topic / "lessons" / name


def _topic_claim_texts(vault: Path, topic: str, exclude_lesson_id: str | None = None) -> list[str]:
    """Nội dung topic.md + mọi lesson_notes.md của topic — nguồn đếm draft claim (INV-26/§15.1).
    Khớp ĐÚNG tập file validate._collect_topic_claims dùng (không lệch nguồn). Bỏ lesson bị exclude
    (dùng cho /forget: lesson sắp xoá không được tính draft)."""
    tdir = vault / "topics" / topic
    texts: list[str] = []
    tmd = tdir / "topic.md"
    if tmd.is_file():
        texts.append(VIO.read_text(tmd))
    ldir = tdir / "lessons"
    if ldir.is_dir():
        for ld in sorted(p for p in ldir.iterdir() if p.is_dir()):
            if exclude_lesson_id is not None and f"{topic}/{ld.name}" == exclude_lesson_id:
                continue
            ln = ld / "lesson_notes.md"
            if ln.is_file():
                texts.append(VIO.read_text(ln))
    return texts


def _regen_topic_views(vault: Path, topic: str, updated_lesson_id: str | None = None,
                       updated_raw: dict | None = None, exclude_lesson_id: str | None = None) -> dict:
    """Parse mọi lesson_state của topic thành model → VW.regen_all(stage='full').
    - (updated_lesson_id, updated_raw): thay lesson đó bằng bản mới (dùng cho /review).
    - exclude_lesson_id: bỏ hẳn lesson đó khỏi view (dùng cho /forget — lesson sắp bị xoá,
      file vẫn còn trên đĩa lúc regen nên phải loại tường minh).
    - không cấp gì: đọc toàn bộ từ đĩa (dùng cho /done).
    stage='full' (không phải 'core'): để has_draft_knowledge (INV-26) được sinh lại + đồng bộ ở MỌI
    đường regen (fix gốc — /done/review/forget không còn kẹt E-DRAFT-IN-MAP khi vault có draft claim)."""
    lessons_dir = vault / "topics" / topic / "lessons"
    models = []
    for ld in sorted(p for p in lessons_dir.iterdir() if p.is_dir()):
        lid = f"{topic}/{ld.name}"
        if exclude_lesson_id is not None and lid == exclude_lesson_id:
            continue
        if updated_lesson_id is not None and lid == updated_lesson_id:
            models.append(_lesson_model_from_raw(updated_raw, ld / "lesson_state.md"))
        else:
            lp = ld / "lesson_state.md"
            raw, _ = _load_raw(lp)
            models.append(_lesson_model_from_raw(raw, lp))
    claim_texts = _topic_claim_texts(vault, topic, exclude_lesson_id)
    regen = VW.regen_all(models, stage="full", claim_texts=claim_texts)
    # spec §4: topic_state.lessons[].status là VIEW đồng bộ từ lesson_state.status → đính kèm để _apply sync.
    regen["lesson_status"] = {m.lesson_id: m.status for m in models}
    return regen


def _apply_views_to_topic_raw(topic_raw: dict, regen: dict, updated_date) -> None:
    rs = regen["review_schedule"]
    topic_raw["review_schedule"] = {
        "generated_from_hash": rs["generated_from_hash"],
        "items": [dict(it) for it in rs["items"]],  # due_date là date obj → YAML unquoted
    }
    topic_raw["assessment"] = dict(regen["assessment"])
    if "has_draft_knowledge" in regen:  # stage='full' → đồng bộ view INV-26
        topic_raw["has_draft_knowledge"] = regen["has_draft_knowledge"]
    lstat = regen.get("lesson_status")  # spec §4/INV-25: đồng bộ index status từ lesson_state (view)
    if lstat:
        for e in topic_raw.get("lessons", []):
            if e.get("id") in lstat:
                e["status"] = lstat[e["id"]]
    topic_raw["updated"] = updated_date


# ---- cmd_review ---------------------------------------------------------
def _recover_first(vault: Path) -> list:
    """Spec 10.3 (BẮT BUỘC — RECOVER-FIRST): trước MỌI ghi mới, hoàn tất transaction dở
    (roll-forward) hoặc chặn bằng E-TX-PARTIAL. Chạy TRƯỚC khi đọc context để bản đọc là
    hậu-recovery (tránh E-STALE-CONTEXT giả khi tx dở đụng đúng file lệnh sắp ghi).
    Vault GĐ1 là 1 gốc (sibling_roots rỗng) nên all_roots=None là đủ."""
    return TX.recover(Path(vault))


def cmd_review(vault: Path, system: Path, lesson_id: str, item_id: str,
               grade: int, reviewed_at: datetime):
    """Chấm 1 review item → transaction-FULL commit. Trả (committed: bool, report: V.Report)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)  # spec 10.3: RECOVER-FIRST trước khi đọc context/ghi mới
    cfg = FA.load_config(system / "fsrs_config.yaml")
    offset = _load_vault_state(vault)[0].get("utc_offset", "+00:00")
    tz = FA._parse_offset(offset)
    reviewed_local_date = reviewed_at.astimezone(tz).date()

    topic = _topic_of(lesson_id)
    ld = _lesson_dir(vault, lesson_id)
    ls_path = ld / "lesson_state.md"
    ts_path = vault / "topics" / topic / "topic_state.md"

    ls_raw, ls_body = _load_raw(ls_path)
    _lesson_model_from_raw(ls_raw, ls_path)  # validate target lesson (review_items + item fields) → E-SCHEMA sạch nếu hỏng
    ls_hash = VIO.content_hash(ls_path)
    ts_raw, ts_body = _load_topic_state(ts_path)
    ts_hash = VIO.content_hash(ts_path)

    item = next((rv for rv in ls_raw.get("review_items", []) if rv.get("id") == item_id), None)
    if item is None:
        raise SessionError(f"không thấy review item {item_id!r} trong {lesson_id}")

    created = item["created"]  # date obj (safe_load)
    old_log = list(item.get("log", []))
    # FA.review raise EReviewBadGrade nếu grade ∉ 0..3 (không tạo transaction)
    created_at_midnight = datetime.combine(created, _dtime(0, 0), tzinfo=tz)
    new_event, card = FA.review(created_at_midnight, old_log, grade, reviewed_at, cfg, offset)
    new_log = old_log + [new_event]
    mastery_state = FA.derive_mastery(card, new_log, cfg)

    item["card"] = _card_for_yaml(card)
    item["log"] = new_log
    item["mastery_state"] = mastery_state
    ls_raw["updated"] = reviewed_local_date

    regen = _regen_topic_views(vault, topic, lesson_id, ls_raw)
    _apply_views_to_topic_raw(ts_raw, regen, reviewed_local_date)

    ls_rel = ls_path.relative_to(vault).as_posix()
    ts_rel = ts_path.relative_to(vault).as_posix()
    writes = [
        TX.Write(ls_rel, _dump_state(ls_raw, ls_body), expected_read_hash=ls_hash),
        TX.Write(ts_rel, _dump_state(ts_raw, ts_body), expected_read_hash=ts_hash),
    ]
    return _run_tx(vault, system, writes, now=reviewed_at)


def _advance_curriculum(cur_raw: dict, lesson_id: str, learned: bool, today) -> bool:
    """R7 auto-advance (thuần, tất định): nếu lesson đạt learned_gate (`learned`) VÀ map một
    curriculum_point CHƯA done → set point.status='done', dời `current_point` sang point chưa-done
    ĐẦU TIÊN theo order; hết point chưa-done → current_point GIỮ NGUYÊN (point tồn tại → 'hoàn tất'
    ngầm, KHÔNG thêm field mới, tránh CR schema + không dangling INV-03). Trả True nếu có thay đổi
    (caller ghi curriculum.md trong CÙNG transaction), else False.

    Idempotent — no-op khi: chưa learned / lesson không map point nào / point đã done (chống nhảy 2 lần)."""
    if not learned:
        return False
    points = cur_raw.get("points") or []
    target = next((p for p in points if p.get("lesson_id") == lesson_id), None)
    if target is None or target.get("status") == "done":
        return False
    target["status"] = "done"
    remaining = sorted((p for p in points if p.get("status") != "done"),
                       key=lambda p: p.get("order", 0))
    if remaining:
        cur_raw["current_point"] = remaining[0]["id"]  # dời sang point chưa-done nhỏ nhất theo order
    cur_raw["updated"] = today
    return True


# ---- cmd_done -----------------------------------------------------------
def cmd_done(vault: Path, system: Path, lesson_id: str, done_at: datetime):
    """Đóng sổ phiên (spec 11B.2, 10.8): regen view + clear open_session + FULL-validate + commit —
    TẤT CẢ trong cùng một transaction-FULL. Trả (committed: bool, report: V.Report).

    Driver KHÔNG sửa nội dung lesson (đó là việc AI trong phiên); /done chỉ:
    - clear vault_state.open_session.lesson_id/started_at + set last_full_validate,
    - regen view topic từ trạng thái lesson trên đĩa (idempotent nếu /review đã sinh),
    - để validator FULL định đoạt trước khi commit.
    """
    vault, system = Path(vault), Path(system)
    _recover_first(vault)  # spec 10.3: RECOVER-FIRST trước khi đọc context/ghi mới
    offset = _load_vault_state(vault)[0].get("utc_offset", "+00:00")
    tz = FA._parse_offset(offset)
    done_local_date = done_at.astimezone(tz).date()
    topic = _topic_of(lesson_id)

    vs_path = vault / "vault_state.md"
    ts_path = vault / "topics" / topic / "topic_state.md"
    vs_raw, vs_body = _load_vault_state(vault)
    vs_hash = VIO.content_hash(vs_path)
    ts_raw, ts_body = _load_topic_state(ts_path)
    ts_hash = VIO.content_hash(ts_path)

    # clear cờ đóng-sổ (spec 11B.2): lesson_id/started_at = null, cập nhật last_full_validate
    sess = dict(vs_raw.get("open_session") or {})
    sess["lesson_id"] = None
    sess["started_at"] = None
    sess["last_full_validate"] = FA.canonical_reviewed_at(done_at, offset)
    vs_raw["open_session"] = sess

    regen = _regen_topic_views(vault, topic)
    _apply_views_to_topic_raw(ts_raw, regen, done_local_date)

    writes = [
        TX.Write(vs_path.relative_to(vault).as_posix(), _dump_state(vs_raw, vs_body),
                 expected_read_hash=vs_hash),
        TX.Write(ts_path.relative_to(vault).as_posix(), _dump_state(ts_raw, ts_body),
                 expected_read_hash=ts_hash),
    ]

    # R7 auto-advance: nếu topic có giáo trình VÀ lesson đạt learned_gate → tiến con trỏ giáo trình
    # trong CÙNG transaction-FULL (validator gate E-CURR-* trước commit; rollback nếu fail).
    cpath = vault / "topics" / topic / "curriculum.md"
    if cpath.is_file():
        learned = regen.get("lesson_status", {}).get(lesson_id) == "learned"
        cur_raw, cur_body = _load_raw(cpath)
        if _advance_curriculum(cur_raw, lesson_id, learned, done_local_date):
            writes.append(TX.Write(cpath.relative_to(vault).as_posix(),
                                   _dump_state(cur_raw, cur_body),
                                   expected_read_hash=VIO.content_hash(cpath)))

    return _run_tx(vault, system, writes, now=done_at)


# ---- cmd_forget (xoá có thẩm quyền, spec 10.3a + 11A /forget) ----------
def cmd_forget(vault: Path, system: Path, lesson_id: str, reason: str,
               confirmed_by_user: bool, at: datetime):
    """Xoá 1 lesson có thẩm quyền: ghi TOMBSTONE (tha INV-11) + xoá file lesson (prune dir rỗng)
    + gỡ lesson khỏi index topic + regen view (loại lesson) + đồng bộ con trỏ. Transaction-FULL.
    Trả (committed, report). Topic-level /forget DEFER (blast radius lớn, khai báo trung thực)."""
    vault, system = Path(vault), Path(system)
    if not confirmed_by_user:
        raise SessionError("/forget cần xác nhận tường minh (confirmed_by_user=True) — spec 10.3a")
    if "/" not in lesson_id:
        raise SessionError(f"/forget topic-level chưa hỗ trợ (chỉ lesson): {lesson_id!r}")
    _recover_first(vault)

    offset = _load_vault_state(vault)[0].get("utc_offset", "+00:00")
    tz = FA._parse_offset(offset)
    local_date = at.astimezone(tz).date()
    topic = _topic_of(lesson_id)
    ld = _lesson_dir(vault, lesson_id)
    ls_path = ld / "lesson_state.md"
    if not ls_path.is_file():
        raise SessionError(f"không thấy lesson {lesson_id!r} để forget")

    ls_raw, _ = _load_raw(ls_path)
    _require_list_of_maps(ls_raw.get("review_items", []), "lesson_state.review_items", ls_path)
    item_ids = [rv.get("id") for rv in ls_raw.get("review_items", []) if rv.get("id")]

    # 1) xoá MỌI file trong lesson dir (dir rỗng sẽ được transaction prune)
    writes = [TX.Write(f.relative_to(vault).as_posix(), None,
                       expected_read_hash=VIO.content_hash(f), op="delete")
              for f in sorted(ld.iterdir()) if f.is_file()]

    # 2) topic_state: gỡ khỏi index + regen view (loại lesson) + đồng bộ current_lesson
    ts_path = vault / "topics" / topic / "topic_state.md"
    ts_raw, ts_body = _load_topic_state(ts_path)
    ts_hash = VIO.content_hash(ts_path)
    ts_raw["lessons"] = [e for e in ts_raw.get("lessons", []) if e.get("id") != lesson_id]
    regen = _regen_topic_views(vault, topic, exclude_lesson_id=lesson_id)
    _apply_views_to_topic_raw(ts_raw, regen, local_date)
    if ts_raw.get("current_lesson") == lesson_id:
        remaining = [e["id"] for e in ts_raw["lessons"]]
        ts_raw["current_lesson"] = remaining[0] if remaining else None
    writes.append(TX.Write(ts_path.relative_to(vault).as_posix(), _dump_state(ts_raw, ts_body),
                           expected_read_hash=ts_hash))

    # 3) vault_state: đồng bộ con trỏ + ĐÓNG phiên nếu trỏ lesson bị xoá (INV-03/25 + vòng đời phiên §11B.2)
    vs_path = vault / "vault_state.md"
    vs_raw, vs_body = _load_vault_state(vault)
    vs_dirty = False
    if vs_raw.get("current_lesson") == lesson_id:
        vs_raw["current_lesson"] = ts_raw.get("current_lesson")
        vs_dirty = True
    sess = vs_raw.get("open_session") or {}
    if sess.get("lesson_id") == lesson_id:  # phiên mở trên lesson bị xoá → đóng phiên (tránh open_session dangling)
        sess = dict(sess)
        sess["lesson_id"] = None
        sess["started_at"] = None
        vs_raw["open_session"] = sess
        vs_dirty = True
    if vs_dirty:
        writes.append(TX.Write(vs_path.relative_to(vault).as_posix(), _dump_state(vs_raw, vs_body),
                               expected_read_hash=VIO.content_hash(vs_path)))

    tomb = TX.Tombstone(op="delete", scope="lesson", lesson_id=lesson_id, item_ids=item_ids,
                        reason=reason, at=FA.canonical_reviewed_at(at, offset), confirmed_by_user=True)
    return _run_tx(vault, system, writes, tombstones=[tomb], now=at)


# ---- cmd_learn (tạo topic MỚI + lesson-001 từ template, spec 11A.1) ----
def cmd_learn(vault: Path, system: Path, topic_id: str, title: str,
              lesson_title: str, objective: str, at: datetime):
    """Tạo topic MỚI + lesson-001 từ template (transaction-FULL). Trả (committed, report).

    Backend tất định (phần hỏi calibrate Q1–Q3 của spec 11A.1 là tầng AI-chat, KHÔNG ở đây).
    Chỉ tạo topic mới: topic đã tồn tại → E-DRIVER. View sinh bằng views.py (lesson mới rỗng
    review_items ⇒ view rỗng), KHÔNG bake hash tay. Index/current_lesson/con trỏ vault đồng bộ (INV-25/03)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)  # spec 10.3: RECOVER-FIRST trước khi ghi mới
    if "/" in topic_id or not topic_id.strip():
        raise SessionError(f"topic_id không hợp lệ (slug, không chứa '/'): {topic_id!r}")
    offset = _load_vault_state(vault)[0].get("utc_offset", "+00:00")
    tz = FA._parse_offset(offset)
    created = at.astimezone(tz).date()

    topic_dir = vault / "topics" / topic_id
    if topic_dir.exists():
        raise SessionError(f"topic {topic_id!r} đã tồn tại — /learn chỉ tạo topic MỚI (spec 11A.1)")
    lesson_name = "lesson-001"
    lesson_id = f"{topic_id}/{lesson_name}"
    subst = {
        "<<TOPIC_ID>>": topic_id, "<<TOPIC_TITLE>>": title,
        "<<LESSON_ID>>": lesson_id, "<<LESSON_TITLE>>": lesson_title,
        "<<OBJECTIVE>>": objective, "<<CREATED>>": created.isoformat(),
    }
    # placeholder của giá trị FREE-TEXT người-dùng → phải thay YAML-safe trong front-matter (id/date giữ raw)
    _TEXT_KEYS = {"<<TOPIC_TITLE>>", "<<LESSON_TITLE>>", "<<OBJECTIVE>>"}

    # lesson_state: instantiate → model → regen view (rỗng vì review_items=[])
    ls_raw, ls_body = _template_state(system, subst, "lesson_template", "lesson_state.template.md",
                                      text_keys=_TEXT_KEYS)
    ls_model = _lesson_model_from_raw(ls_raw)
    regen = _regen_from_models([ls_model])

    # topic_state: index + current_lesson + view (đồng bộ INV-25/09)
    ts_raw, ts_body = _template_state(system, subst, "topic_template", "topic_state.template.md",
                                      text_keys=_TEXT_KEYS)
    ts_raw["lessons"] = [{"id": lesson_id, "status": ls_raw["status"]}]
    ts_raw["current_lesson"] = lesson_id
    _apply_views_to_topic_raw(ts_raw, regen, created)

    src_raw, src_body = _template_state(system, subst, "topic_template", "sources.template.md",
                                        text_keys=_TEXT_KEYS)
    # topic.md: content cấp-topic (CR-0005) — có '## Lộ trình' + '## Knowledge Map'. Body markdown → raw subst
    # (không front-matter, không cần escape YAML). AI cập nhật Lộ trình khi dạy.
    topic_md = _template_text(system, subst, "topic_template", "topic.template.md")
    lesson_md = _template_text(system, subst, "lesson_template", "lesson.template.md")
    lesson_notes = _template_text(system, subst, "lesson_template", "lesson_notes.template.md")

    # vault_state: trỏ topic/lesson mới (INV-03)
    vs_path = vault / "vault_state.md"
    vs_raw, vs_body = _load_vault_state(vault)
    vs_hash = VIO.content_hash(vs_path)
    vs_raw["current_topic"] = topic_id
    vs_raw["current_lesson"] = lesson_id
    # MỞ phiên (§5.4/§11B.2): /learn mở phiên trên lesson mới — set trong CÙNG write vault_state
    sess = dict(vs_raw.get("open_session") or {})
    sess["lesson_id"] = lesson_id
    sess["started_at"] = FA.canonical_reviewed_at(at, offset)
    vs_raw["open_session"] = sess

    tp = f"topics/{topic_id}"
    lp = f"{tp}/lessons/{lesson_name}"
    writes = [
        TX.Write(f"{tp}/topic_state.md", _dump_state(ts_raw, ts_body), expected_read_hash=None),
        TX.Write(f"{tp}/topic.md", topic_md.encode("utf-8"), expected_read_hash=None),  # CR-0005 roadmap
        TX.Write(f"{tp}/sources.md", _dump_state(src_raw, src_body), expected_read_hash=None),
        TX.Write(f"{lp}/lesson.md", lesson_md.encode("utf-8"), expected_read_hash=None),
        TX.Write(f"{lp}/lesson_state.md", _dump_state(ls_raw, ls_body), expected_read_hash=None),
        TX.Write(f"{lp}/lesson_notes.md", lesson_notes.encode("utf-8"), expected_read_hash=None),
        TX.Write("vault_state.md", _dump_state(vs_raw, vs_body), expected_read_hash=vs_hash),
    ]
    return _run_tx(vault, system, writes, now=at)


def _regen_from_models(models: list) -> dict:
    return VW.regen_all(models, stage="core")


# ---- cmd_schedule (CHỈ ĐỌC, spec 8.5 + 11A.2 /schedule) ----------------
def _all_lesson_models(vault: Path) -> list:
    """Parse mọi lesson_state.md của mọi topic thành model (chỉ đọc, cho engine due)."""
    out = []
    topics = Path(vault) / "topics"
    if not topics.is_dir():
        return out
    for tdir in sorted(p for p in topics.iterdir() if p.is_dir()):
        ldir = tdir / "lessons"
        if not ldir.is_dir():
            continue
        for ld in sorted(p for p in ldir.iterdir() if p.is_dir()):
            ls = ld / "lesson_state.md"
            if ls.is_file():
                out.append(_lesson_model_from_raw(_load_raw(ls)[0], ls))
    return out


def cmd_schedule(vault: Path, system: Path, at: datetime, days: int = 0) -> list[dict]:
    """CHỈ ĐỌC: liệt kê item tới hạn trong `days` ngày tới (spec 8.5, engine schedule.py).
    days=0 = 'cần ôn hôm nay'. Không ghi, không transaction."""
    vault = Path(vault)
    vs_raw = _load_vault_state(vault)[0]
    offset = vs_raw.get("utc_offset", "+00:00")
    cutoff = int(vs_raw.get("day_cutoff_hour", 4))
    now_utc = at.astimezone(timezone.utc)
    due = SCHED.due_within(_all_lesson_models(vault), now_utc, offset, cutoff, days=days)
    return [{"lesson_id": lid, "item_id": rv.id, "mastery_state": rv.mastery_state,
             "due_date": rv.card.due_date.isoformat(), "prompt_ref": rv.prompt_ref}
            for lid, rv in due]


# ---- cmd_status / cmd_resume (CHỈ ĐỌC, spec 11B + 11B.2) ---------------
def cmd_status(vault: Path, system: Path, at: datetime) -> dict:
    """CHỈ ĐỌC (cửa vào, spec 11B): topic/lesson hiện tại + số câu tới hạn hôm nay (engine 8.5)
    + cảnh báo phiên chưa /done (open_session, spec 11B.2) + gợi ý lệnh kế. Không ghi."""
    vault = Path(vault)
    vs_raw = _load_vault_state(vault)[0]
    offset = vs_raw.get("utc_offset", "+00:00")
    cutoff = int(vs_raw.get("day_cutoff_hour", 4))
    now_utc = at.astimezone(timezone.utc)
    due = SCHED.due_today(_all_lesson_models(vault), now_utc, offset, cutoff)
    sess = vs_raw.get("open_session") or {}
    open_lesson = sess.get("lesson_id")
    current_lesson = vs_raw.get("current_lesson")
    suggestion = "review" if due else ("resume" if current_lesson else "learn")
    return {
        "current_topic": vs_raw.get("current_topic"),
        "current_lesson": current_lesson,
        "due_today": len(due),
        "due_items": [{"lesson_id": lid, "item_id": rv.id} for lid, rv in due],
        "unclosed_session": open_lesson is not None,   # spec 11B.2: cảnh báo phiên chưa /done
        "open_session_lesson": open_lesson,
        "open_session_started_at": sess.get("started_at"),
        "suggestion": suggestion,
    }


def cmd_resume(vault: Path, system: Path, at: datetime):
    """MỞ phiên trên current_lesson + trả info học tiếp (spec 11B/11B.2, CR-0003 — đảo read-only DEC-016).
    Set open_session.lesson_id/started_at trong transaction-LIGHT (chỉ đụng vault_state, không FSRS/view).
    Không có current_lesson → no-op. Trả (committed, report|None, info)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    vs_path = vault / "vault_state.md"
    vs_raw, vs_body = _load_vault_state(vault)
    current_lesson = vs_raw.get("current_lesson")
    info = {
        "current_topic": vs_raw.get("current_topic"),
        "current_lesson": current_lesson,
        "status": None, "next_action": None,
        "unclosed_session": (vs_raw.get("open_session") or {}).get("lesson_id") is not None,
    }
    if current_lesson and "/" in current_lesson:
        ls_path = _lesson_dir(vault, current_lesson) / "lesson_state.md"
        if ls_path.is_file():
            ls_raw = _load_raw(ls_path)[0]
            info["status"] = ls_raw.get("status")
            info["next_action"] = ls_raw.get("next_action")
    if not current_lesson:
        return True, None, info  # không có lesson để mở phiên (no-op)
    offset = vs_raw.get("utc_offset", "+00:00")
    sess = dict(vs_raw.get("open_session") or {})
    sess["lesson_id"] = current_lesson
    sess["started_at"] = FA.canonical_reviewed_at(at, offset)
    vs_raw["open_session"] = sess
    writes = [TX.Write("vault_state.md", _dump_state(vs_raw, vs_body),
                       expected_read_hash=VIO.content_hash(vs_path))]
    committed, rep = _run_tx(vault, system, writes, level="light", now=at)  # §11B.2: mở phiên = ghi nhỏ
    info["unclosed_session"] = True
    return committed, rep, info


# ---- cmd_source (nạp nguồn status=raw, spec 15 + 5.3; transaction-LIGHT) ----
_SRC_ID_RE = re.compile(r"^src-(\d+)$")


def _next_src_id(sources: list) -> str:
    """id nguồn kế tiếp: src-NNN (zero-pad 3), max hiện có + 1; rỗng → src-001."""
    nums = [int(m.group(1)) for s in sources
            if (m := _SRC_ID_RE.match(str(s.get("id", "")))) is not None]
    return f"src-{(max(nums) + 1) if nums else 1:03d}"


def cmd_source(vault: Path, system: Path, topic_id: str, ref: str, kind: str,
               at: datetime, scope: str = "", trust: str = "unknown"):
    """Nạp 1 nguồn mới vào topics/<topic>/sources.md ở status=raw (spec 15 bước 1).
    Transaction-LIGHT (spec 10.8/11A: ghi-trong-phiên; raw source không đụng FSRS/view/cross-ref —
    INV-13 chỉ kích khi có CLAIM trỏ nguồn raw, chưa có lúc nạp). Phân loại kind/trust là tầng AI-chat;
    backend chỉ ghi tất định. Trả (committed, report, new_src_id). Kind/enum sai → validator LIGHT bắt."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại — /source cần topic đã có (dùng /learn trước)")
    offset = _load_vault_state(vault)[0].get("utc_offset", "+00:00")
    tz = FA._parse_offset(offset)
    added = at.astimezone(tz).date()

    src_path = topic_dir / "sources.md"
    if src_path.is_file():
        src_raw, src_body = _load_raw(src_path)
        ehr = VIO.content_hash(src_path)
    else:
        # sources.md chưa có (topic demo có thể thiếu) → tạo mới, schema_version khớp vault
        vault_sv = _load_vault_state(vault)[0].get("schema_version", 1)
        src_raw = {"schema": "sources", "schema_version": vault_sv, "topic_id": topic_id, "sources": []}
        src_body = f"\n\n# Nguồn — {topic_id}\n"
        ehr = None

    sources = src_raw.setdefault("sources", [])
    new_id = _next_src_id(sources)
    sources.append({
        "id": new_id, "kind": kind, "ref": ref, "status": "raw",
        "trust": trust, "scope": scope, "added": added, "anchors": [],
    })
    writes = [TX.Write(src_path.relative_to(vault).as_posix(),
                       _dump_state(src_raw, src_body), expected_read_hash=ehr)]
    committed, rep = _run_tx(vault, system, writes, level="light", now=at)  # spec 10.8: in-session = LIGHT
    return committed, rep, new_id


def cmd_collect(vault: Path, system: Path, topic_id: str, slug: str, content: str, at: datetime):
    """Ghi một lát cắt tài liệu tham chiếu vào topics/<topic>/reference/<slug>.md (CR-0008, transaction-LIGHT).
    Đầu vào cho việc dựng giáo trình (Reference_Store). Backend ghi TẤT ĐỊNH; AI (chat) lo lấy nội dung
    (như cmd_learn/cmd_source — KHÔNG tự-fetch mạng). Trả (committed, report, ref_tương_đối_topic).
    An toàn: slug là TÊN FILE .md (không path/traversal); topic phải tồn tại; nội dung không rỗng;
    abspath trong nội dung bị LIGHT validate chặn (INV-16). reference/ chỉ chứa .md (lát cắt text)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại — /collect cần topic đã có (dùng /learn trước)")
    name = slug.strip()
    if not name:
        raise SessionError("slug rỗng")
    if not name.endswith(".md"):
        name += ".md"
    if "/" in name or "\\" in name or ".." in name:
        raise SessionError(f"slug không hợp lệ (chỉ tên file .md, không path/traversal): {slug!r}")
    if not content.strip():
        raise SessionError("nội dung reference rỗng")
    rel = (topic_dir / "reference" / name).relative_to(vault).as_posix()
    writes = [TX.Write(rel, content.encode("utf-8"), expected_read_hash=None)]
    committed, rep = _run_tx(vault, system, writes, level="light", now=at)  # spec 10.8: in-session = LIGHT
    return committed, rep, f"reference/{name}"


def cmd_curriculum(vault: Path, system: Path, topic_id: str, points_json: str, at: datetime):
    """Dựng topics/<topic>/curriculum.md từ danh sách điểm học (CR-0008, transaction-FULL).
    `points_json`: chuỗi JSON list [{objective, source_refs?}]. Backend gán cp-NNN + order 1..N TẤT ĐỊNH +
    status=not_started + current_point=cp-001 + teachable=true; AI (chat) soạn NỘI DUNG điểm (Class D).
    Ghi qua transaction-FULL → validator kiểm E-CURR-* (cấu trúc sai → ABORT). Dùng _dump_state (safe_dump)
    nên free-text objective an toàn. Chỉ DỰNG mới (đã có curriculum.md → lỗi; sửa/bổ sung là luồng khác)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại — /curriculum cần topic đã có (dùng /learn trước)")
    cpath = topic_dir / "curriculum.md"
    if cpath.is_file():
        raise SessionError(f"topic {topic_id!r} đã có curriculum.md — /curriculum chỉ DỰNG mới")
    try:
        raw_points = json.loads(points_json)
    except (json.JSONDecodeError, TypeError) as e:
        raise SessionError(f"--points không phải JSON hợp lệ: {e}")
    if not isinstance(raw_points, list) or not raw_points:
        raise SessionError("--points phải là JSON list không rỗng các điểm học")
    points = []
    for i, p in enumerate(raw_points, start=1):
        if not isinstance(p, dict) or not str(p.get("objective", "")).strip():
            raise SessionError(f"điểm #{i} thiếu 'objective' không rỗng")
        srefs = p.get("source_refs") or []
        if not isinstance(srefs, list) or not all(isinstance(s, str) for s in srefs):
            raise SessionError(f"điểm #{i} 'source_refs' phải là list chuỗi")
        arefs = p.get("area_refs") or []  # CR-0012: ánh xạ Mandatory_Area (phủ blueprint); default []
        if not isinstance(arefs, list) or not all(isinstance(s, str) for s in arefs):
            raise SessionError(f"điểm #{i} 'area_refs' phải là list chuỗi")
        points.append({
            "id": f"cp-{i:03d}", "order": i, "objective": str(p["objective"]),
            "status": "not_started", "lesson_id": None, "source_refs": srefs, "area_refs": arefs,
        })
    vs_raw = _load_vault_state(vault)[0]
    today = at.astimezone(FA._parse_offset(vs_raw.get("utc_offset", "+00:00"))).date()
    raw = {
        "schema": "curriculum", "schema_version": vs_raw.get("schema_version", 1),
        "topic_id": topic_id, "current_point": "cp-001", "teachable": True,
        "points": points, "created": today, "updated": today,
    }
    body = (f"\n\n# Giáo trình — {topic_id}\n\n"
            "Danh sách điểm cần học (Curriculum_Point), sinh bởi /curriculum. Mỗi lesson bám theo một điểm.\n")
    writes = [TX.Write(cpath.relative_to(vault).as_posix(), _dump_state(raw, body), expected_read_hash=None)]
    return _run_tx(vault, system, writes, now=at)  # FULL: _check_curriculum kiểm E-CURR-* (abort nếu cấu trúc sai)


def cmd_curriculum_insert(vault: Path, system: Path, topic_id: str, insert_at: int,
                          point_json: str, at: datetime):
    """Chèn một Curriculum_Point vào vị trí `insert_at` (1..N+1) của giáo trình (CR-0010, R8, transaction-FULL).

    `point_json`: JSON một object {objective, source_refs?}. Point mới nhận order=insert_at + id duy nhất ổn
    định (`cp-{max_suffix+1}` — KHÔNG tái dùng số theo order, tránh trùng khi về sau xoá/chèn); các point có
    order>=insert_at dịch +1 (giữ hoán vị 1..N+1 → E-CURR-ORDER). GIỮ NGUYÊN id + status các point cũ và
    `current_point` (tham chiếu id, không phụ thuộc order — R8.3/INV-03). Vị trí ngoài [1..N+1] / curriculum
    thiếu / objective rỗng → từ chối, không đổi (R8.7). transaction-FULL: validator gate E-CURR-* trước commit,
    sai → rollback (R8.5). Trả (committed, report)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại")
    cpath = topic_dir / "curriculum.md"
    if not cpath.is_file():
        raise SessionError(f"topic {topic_id!r} chưa có curriculum — dùng /curriculum dựng trước (R8 chèn vào giáo trình đang có)")
    try:
        p = json.loads(point_json)
    except (json.JSONDecodeError, TypeError) as e:
        raise SessionError(f"--point không phải JSON hợp lệ: {e}")
    if not isinstance(p, dict) or not str(p.get("objective", "")).strip():
        raise SessionError("--point thiếu 'objective' không rỗng")
    srefs = p.get("source_refs") or []
    if not isinstance(srefs, list) or not all(isinstance(s, str) for s in srefs):
        raise SessionError("--point 'source_refs' phải là list chuỗi")
    arefs = p.get("area_refs") or []  # CR-0012: ánh xạ Mandatory_Area
    if not isinstance(arefs, list) or not all(isinstance(s, str) for s in arefs):
        raise SessionError("--point 'area_refs' phải là list chuỗi")

    cur_raw, cur_body = _load_curriculum_validated(cpath)  # sửa-tay-hỏng → E-SCHEMA sạch (không crash)
    points = cur_raw.get("points") or []
    n = len(points)
    if not (1 <= insert_at <= n + 1):
        raise SessionError(f"insert_at {insert_at} ngoài khoảng hợp lệ [1..{n + 1}] (R8.7)")
    # id mới = cp-{max_suffix+1} (ổn định, duy nhất); an toàn cả khi id cũ không liên tục
    max_suf = 0
    for pt in points:
        m = re.match(r"^cp-(\d+)$", str(pt.get("id", "")))
        if m:
            max_suf = max(max_suf, int(m.group(1)))
    new_id = f"cp-{max_suf + 1:03d}"
    if any(str(pt.get("id")) == new_id for pt in points):  # phòng vệ (id phi-số) — không trùng (R8.4/8.7)
        raise SessionError(f"không sinh được id duy nhất (đụng {new_id!r})")

    for pt in points:  # dịch order các point từ vị trí chèn trở đi (giữ hoán vị)
        if int(pt.get("order", 0)) >= insert_at:
            pt["order"] = int(pt["order"]) + 1
    new_point = {"id": new_id, "order": insert_at, "objective": str(p["objective"]),
                 "status": "not_started", "lesson_id": None, "source_refs": srefs, "area_refs": arefs}
    points.insert(insert_at - 1, new_point)   # vị trí list gọn gàng (validator sắp theo order dù sao)
    cur_raw["points"] = points
    today = at.astimezone(FA._parse_offset(_load_vault_state(vault)[0].get("utc_offset", "+00:00"))).date()
    cur_raw["updated"] = today
    writes = [TX.Write(cpath.relative_to(vault).as_posix(), _dump_state(cur_raw, cur_body),
                       expected_read_hash=VIO.content_hash(cpath))]
    return _run_tx(vault, system, writes, now=at)  # FULL: E-CURR-* (order hoán vị/dup-id/ref) gate; sai → rollback


# ---- blueprint (Topic_Blueprint — khung giáo trình bắt buộc, CR-0011/0013) ----
def _load_blueprint_validated(bpath: Path) -> tuple[dict, str]:
    """blueprint.md validate qua M.Blueprint (xem _load_model_validated) — sửa-tay-hỏng → E-SCHEMA sạch."""
    return _load_model_validated(bpath, M.Blueprint)


def _parse_areas_json(areas_json: str, existing_ids=None) -> list[dict]:
    """Parse JSON list mảng cho build/edit/amend → list dict {id, order, title, mandatory, source_refs}.
    existing_ids=None (BUILD): mọi id sinh mới ma-001..N theo vị trí. existing_ids=set (EDIT/AMEND): item
    có 'id' phải trỏ area đang có (GIỮ id ổn định — R1.2); item không 'id' → sinh ma-{max+1} duy nhất."""
    try:
        raw = json.loads(areas_json)
    except (json.JSONDecodeError, TypeError) as e:
        raise SessionError(f"--areas không phải JSON hợp lệ: {e}")
    if not isinstance(raw, list) or not raw:
        raise SessionError("--areas phải là JSON list không rỗng các mảng bắt buộc")
    max_suf = 0
    for aid in (existing_ids or set()):
        m = re.match(r"^ma-(\d+)$", str(aid))
        if m:
            max_suf = max(max_suf, int(m.group(1)))
    areas, seen = [], set()
    for i, a in enumerate(raw, start=1):
        if not isinstance(a, dict) or not str(a.get("title", "")).strip():
            raise SessionError(f"mảng #{i} thiếu 'title' không rỗng")
        srefs = a.get("source_refs") or []
        if not isinstance(srefs, list) or not all(isinstance(s, str) for s in srefs):
            raise SessionError(f"mảng #{i} 'source_refs' phải là list chuỗi")
        mand = a.get("mandatory", True)
        if not isinstance(mand, bool):
            raise SessionError(f"mảng #{i} 'mandatory' phải là bool")
        if existing_ids is None:
            aid = f"ma-{i:03d}"
        elif a.get("id") is not None:
            aid = str(a["id"])
            if aid not in existing_ids:
                raise SessionError(f"mảng #{i}: id {aid!r} không trỏ Mandatory_Area đang có (giữ id ổn định R1.2)")
        else:
            max_suf += 1
            aid = f"ma-{max_suf:03d}"
        if aid in seen:
            raise SessionError(f"mảng #{i}: id {aid!r} trùng trong danh sách")
        seen.add(aid)
        areas.append({"id": aid, "order": i, "title": str(a["title"]),
                      "mandatory": mand, "source_refs": srefs})
    return areas


def cmd_blueprint(vault: Path, system: Path, topic_id: str, areas_json: str, at: datetime):
    """Dựng topics/<topic>/blueprint.md (status=draft) từ danh sách mảng bắt buộc (CR-0013, transaction-FULL).
    `areas_json`: JSON list [{title, mandatory?, source_refs?}]. Backend gán ma-NNN + order 1..N TẤT ĐỊNH +
    mandatory mặc định true. Chỉ DỰNG mới (đã có → lỗi; sửa qua --edit/--amend). Thiếu tham số → hỏi lại/lỗi
    (R2.5, không đoán). Validator gate E-BP-* (cấu trúc sai → ABORT)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại — /blueprint cần topic đã có (dùng /learn trước)")
    bpath = topic_dir / "blueprint.md"
    if bpath.is_file():
        raise SessionError(f"topic {topic_id!r} đã có blueprint.md — /blueprint chỉ DỰNG mới (sửa: --edit/--amend)")
    areas = _parse_areas_json(areas_json, existing_ids=None)
    vs_raw = _load_vault_state(vault)[0]
    today = at.astimezone(FA._parse_offset(vs_raw.get("utc_offset", "+00:00"))).date()
    raw = {
        "schema": "blueprint", "schema_version": vs_raw.get("schema_version", 1),
        "topic_id": topic_id, "status": "draft", "areas": areas,
        "created": today, "updated": today,
    }
    body = (f"\n\n# Khung giáo trình bắt buộc — {topic_id}\n\n"
            "Danh sách Mandatory_Area (zero→chuyên-gia), sinh bởi /blueprint. Giáo trình phải phủ đủ khi approved.\n")
    writes = [TX.Write(bpath.relative_to(vault).as_posix(), _dump_state(raw, body), expected_read_hash=None)]
    return _run_tx(vault, system, writes, now=at)  # FULL: _check_blueprint gate E-BP-* (abort nếu sai)


def _blueprint_set_areas(vault: Path, system: Path, topic_id: str, areas_json: str, at: datetime,
                         *, require_status: str, confirm: bool = False):
    """Chung cho edit (draft) + amend (approved): thay danh sách areas, GIỮ id ổn định (R1.2). transaction-FULL
    re-validate E-BP-* → rollback nếu sai (R4.4). require_status khoá đúng trạng thái được phép sửa."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    bpath = vault / "topics" / topic_id / "blueprint.md"
    if not bpath.is_file():
        raise SessionError(f"topic {topic_id!r} chưa có blueprint — dùng /blueprint dựng trước")
    bp_raw, bp_body = _load_blueprint_validated(bpath)
    status = bp_raw.get("status")
    if status != require_status:
        raise SessionError(f"blueprint {topic_id!r} ở trạng thái {status!r} — thao tác này cần {require_status!r}")
    if require_status == "approved" and not confirm:
        raise SessionError("sửa blueprint đã approved cần --confirm tường minh (R4.3)")
    existing_ids = {str(a.get("id")) for a in (bp_raw.get("areas") or [])}
    bp_raw["areas"] = _parse_areas_json(areas_json, existing_ids=existing_ids)
    bp_raw["updated"] = at.astimezone(FA._parse_offset(_load_vault_state(vault)[0].get("utc_offset", "+00:00"))).date()
    writes = [TX.Write(bpath.relative_to(vault).as_posix(), _dump_state(bp_raw, bp_body),
                       expected_read_hash=VIO.content_hash(bpath))]
    return _run_tx(vault, system, writes, now=at)


def cmd_blueprint_edit(vault: Path, system: Path, topic_id: str, areas_json: str, at: datetime):
    """Sửa areas khi blueprint còn 'draft' (R4.1). Approved → từ chối (dùng --amend --confirm)."""
    return _blueprint_set_areas(vault, system, topic_id, areas_json, at, require_status="draft")


def cmd_blueprint_amend(vault: Path, system: Path, topic_id: str, areas_json: str, confirm: bool, at: datetime):
    """Sửa areas khi blueprint 'approved' — CHỈ khi confirm=True (R4.3/4.4). transaction-FULL re-validate."""
    return _blueprint_set_areas(vault, system, topic_id, areas_json, at, require_status="approved", confirm=confirm)


def cmd_blueprint_approve(vault: Path, system: Path, topic_id: str, at: datetime):
    """Chuyển draft→approved (R4.2). transaction-FULL gate Blueprint_Validator; FAIL → rollback, giữ draft (R4.6)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    bpath = vault / "topics" / topic_id / "blueprint.md"
    if not bpath.is_file():
        raise SessionError(f"topic {topic_id!r} chưa có blueprint — dùng /blueprint dựng trước")
    bp_raw, bp_body = _load_blueprint_validated(bpath)
    if bp_raw.get("status") == "approved":
        raise SessionError(f"blueprint {topic_id!r} đã approved")
    bp_raw["status"] = "approved"
    bp_raw["updated"] = at.astimezone(FA._parse_offset(_load_vault_state(vault)[0].get("utc_offset", "+00:00"))).date()
    writes = [TX.Write(bpath.relative_to(vault).as_posix(), _dump_state(bp_raw, bp_body),
                       expected_read_hash=VIO.content_hash(bpath))]
    return _run_tx(vault, system, writes, now=at)


def cmd_next_lesson(vault: Path, system: Path, topic_id: str, at: datetime):
    """'Nhảy bài' (CR-0008, transaction-FULL): sinh lesson kế cho current_point của giáo trình.
    Tạo lessons/lesson-NNN từ template (objective = objective của current_point), set point.lesson_id,
    append topic_state.lessons[] + regen view từ TẤT CẢ lesson (INV-25/09), trỏ vault_state.current_lesson +
    mở phiên. Chỉ khi curriculum.teachable=true (R6.8) VÀ current_point CHƯA có lesson (chưa /done nhảy điểm).
    AI dạy NỘI DUNG sau (Class D). Trả (committed, report)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if "/" in topic_id or not topic_id.strip():
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại")
    cpath = topic_dir / "curriculum.md"
    if not cpath.is_file():
        raise SessionError(f"topic {topic_id!r} chưa có curriculum — dùng /curriculum trước")
    cur_raw, cur_body = _load_curriculum_validated(cpath)  # sửa-tay-hỏng → E-SCHEMA sạch (không crash)
    if not cur_raw.get("teachable"):
        raise SessionError(f"curriculum của {topic_id!r} chưa teachable (chưa được-phép-dạy)")
    current_point = cur_raw.get("current_point")
    cp = next((p for p in (cur_raw.get("points") or []) if p.get("id") == current_point), None)
    if cp is None:
        raise SessionError(f"current_point {current_point!r} không tồn tại trong giáo trình")
    if cp.get("lesson_id"):
        raise SessionError(f"current_point {current_point!r} đã có lesson {cp['lesson_id']!r} — /done để nhảy điểm kế")
    objective = str(cp.get("objective") or "").strip()
    if not objective:
        raise SessionError(f"current_point {current_point!r} có objective rỗng")

    vs_path = vault / "vault_state.md"
    vs_raw, vs_body = _load_vault_state(vault)
    vs_hash = VIO.content_hash(vs_path)
    offset = vs_raw.get("utc_offset", "+00:00")
    created = at.astimezone(FA._parse_offset(offset)).date()

    lessons_dir = topic_dir / "lessons"
    nums = []
    if lessons_dir.is_dir():
        for d in lessons_dir.iterdir():
            if d.is_dir() and d.name.startswith("lesson-"):
                tail = d.name.split("-", 1)[1]
                if tail.isdigit():
                    nums.append(int(tail))
    lesson_name = f"lesson-{(max(nums) + 1) if nums else 1:03d}"
    lesson_id = f"{topic_id}/{lesson_name}"

    ts_path = topic_dir / "topic_state.md"
    ts_raw, ts_body = _load_raw(ts_path)
    ts_hash = VIO.content_hash(ts_path)
    subst = {
        "<<TOPIC_ID>>": topic_id, "<<TOPIC_TITLE>>": ts_raw.get("title", topic_id),
        "<<LESSON_ID>>": lesson_id, "<<LESSON_TITLE>>": objective,
        "<<OBJECTIVE>>": objective, "<<CREATED>>": created.isoformat(),
    }
    _TEXT_KEYS = {"<<TOPIC_TITLE>>", "<<LESSON_TITLE>>", "<<OBJECTIVE>>"}
    ls_raw, ls_body = _template_state(system, subst, "lesson_template", "lesson_state.template.md",
                                      text_keys=_TEXT_KEYS)
    lesson_md = _template_text(system, subst, "lesson_template", "lesson.template.md")
    lesson_notes = _template_text(system, subst, "lesson_template", "lesson_notes.template.md")

    # regen view từ TẤT CẢ lesson: cũ (trên đĩa) + mới (in-memory, chưa ghi)
    models = []
    if lessons_dir.is_dir():
        for d in sorted(p for p in lessons_dir.iterdir() if p.is_dir()):
            lp_disk = d / "lesson_state.md"
            raw_disk, _ = _load_raw(lp_disk)
            models.append(_lesson_model_from_raw(raw_disk, lp_disk))
    models.append(_lesson_model_from_raw(ls_raw, lessons_dir / lesson_name / "lesson_state.md"))
    regen = VW.regen_all(models, stage="full", claim_texts=_topic_claim_texts(vault, topic_id))
    regen["lesson_status"] = {m.lesson_id: m.status for m in models}

    ts_raw.setdefault("lessons", []).append({"id": lesson_id, "status": ls_raw["status"]})
    ts_raw["current_lesson"] = lesson_id
    _apply_views_to_topic_raw(ts_raw, regen, created)

    cp["lesson_id"] = lesson_id           # gắn lesson vào current_point (INV-03 tham chiếu)
    cur_raw["updated"] = created

    vs_raw["current_topic"] = topic_id
    vs_raw["current_lesson"] = lesson_id
    sess = dict(vs_raw.get("open_session") or {})
    sess["lesson_id"] = lesson_id
    sess["started_at"] = FA.canonical_reviewed_at(at, offset)
    vs_raw["open_session"] = sess

    tp = f"topics/{topic_id}"
    lp = f"{tp}/lessons/{lesson_name}"
    writes = [
        TX.Write(f"{lp}/lesson.md", lesson_md.encode("utf-8"), expected_read_hash=None),
        TX.Write(f"{lp}/lesson_state.md", _dump_state(ls_raw, ls_body), expected_read_hash=None),
        TX.Write(f"{lp}/lesson_notes.md", lesson_notes.encode("utf-8"), expected_read_hash=None),
        TX.Write(f"{tp}/topic_state.md", _dump_state(ts_raw, ts_body), expected_read_hash=ts_hash),
        TX.Write(f"{tp}/curriculum.md", _dump_state(cur_raw, cur_body), expected_read_hash=VIO.content_hash(cpath)),
        TX.Write("vault_state.md", _dump_state(vs_raw, vs_body), expected_read_hash=vs_hash),
    ]
    return _run_tx(vault, system, writes, now=at)  # FULL: INV-25 index + INV-09 view + INV-08 replay + E-CURR-*


def cmd_grade(vault: Path, system: Path, topic_id: str, submission_id: str, file: str,
              target: str, verdict: str, at: datetime):
    """Ghi một bản ghi CHẤM vào topics/<topic>/exam_results.md (CR-0008, transaction-LIGHT, R9).

    Bài nộp (Exam_Submission, có thể là CODE) nằm NGOÀI vault ở exam/ (sibling learning_vault) để không
    phá INV-17 trên vault. cmd_grade verify NGAY (LIGHT không chạy _check_exam_results): bài nộp `file` tồn
    tại + nằm trong exam/ + submission_id đúng pattern + target ∈ {topic, curriculum_point} + submission_id
    chưa trùng (INV-04) → nếu sai bất kỳ: TỪ CHỐI, không tạo bản ghi bộ phận (R9.6). Lưu ref TƯƠNG ĐỐI
    (portable, INV-16) do backend tự tính từ topic_dir (không bắt người dùng gõ '../..'). verdict là Class D
    (KHÔNG kiểm nội dung — R9.3). Trả (committed, report)."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not topic_id.strip() or "/" in topic_id:
        raise SessionError(f"topic_id không hợp lệ: {topic_id!r}")
    topic_dir = vault / "topics" / topic_id
    if not topic_dir.is_dir():
        raise SessionError(f"topic {topic_id!r} không tồn tại — /grade cần topic đã có")
    if not re.match(r"^ex-\S+$", submission_id):
        raise SessionError(f"submission_id sai pattern (cần 'ex-...'): {submission_id!r}")
    if not verdict.strip():
        raise SessionError("verdict rỗng")

    # (R9.6) bài nộp phải TỒN TẠI trong exam/ NGOÀI vault
    exam_root = (vault.parent / "exam").resolve()
    sub_resolved = Path(file).resolve()
    under_exam = sub_resolved == exam_root or exam_root in sub_resolved.parents
    if not under_exam:
        raise SessionError(f"bài nộp {file!r} không nằm trong exam/ (NGOÀI vault, sibling learning_vault)")
    if not sub_resolved.is_file():
        raise SessionError(f"bài nộp {file!r} không tồn tại — /grade cần bài nộp có thật (R9.6)")

    # (R9.6) target phải là topic HOẶC một Curriculum_Point tồn tại
    valid_targets = {topic_id}
    cpath = topic_dir / "curriculum.md"
    if cpath.is_file():
        cur_pts = _load_raw(cpath)[0].get("points")
        if isinstance(cur_pts, list):  # curriculum là tham chiếu PHỤ ở đây → guard mềm (không crash nếu hỏng)
            valid_targets |= {str(p["id"]) for p in cur_pts if isinstance(p, dict) and p.get("id")}
    if target not in valid_targets:
        raise SessionError(f"target {target!r} không phải topic hoặc Curriculum_Point tồn tại (R9.6)")

    ref = Path(os.path.relpath(sub_resolved, topic_dir.resolve())).as_posix()  # tương đối, portable
    vs_raw = _load_vault_state(vault)[0]
    today = at.astimezone(FA._parse_offset(vs_raw.get("utc_offset", "+00:00"))).date()
    entry = {"submission_id": submission_id, "ref": ref, "target": target,
             "graded_at": today, "verdict": verdict}

    epath = topic_dir / "exam_results.md"
    if epath.is_file():
        raw, body = _load_model_validated(epath, M.ExamResults)  # sửa-tay-hỏng → E-SCHEMA sạch (không crash)
        results = raw.get("results") or []
        if any(str(r.get("submission_id")) == submission_id for r in results):
            raise SessionError(f"submission_id {submission_id!r} đã có bản ghi chấm (INV-04, không trùng)")
        results.append(entry)
        raw["results"] = results
        expected = VIO.content_hash(epath)
    else:
        raw = {"schema": "exam_results", "schema_version": vs_raw.get("schema_version", 1),
               "topic_id": topic_id, "results": [entry]}
        body = (f"\n\n# Bản ghi chấm bài thực hành — {topic_id}\n\n"
                "Metadata chấm (Class D). Bài nộp nằm ở exam/ NGOÀI vault; đây chỉ là bản ghi tham chiếu.\n")
        expected = None
    writes = [TX.Write(epath.relative_to(vault).as_posix(), _dump_state(raw, body), expected_read_hash=expected)]
    return _run_tx(vault, system, writes, level="light", now=at)  # spec 10.8: in-session = LIGHT


# ---- cmd_ask (ghi câu hỏi phụ vào lesson.md ## Hỏi phụ, spec 14A/11; LIGHT) ----
_HOIPHU = "## Hỏi phụ"


def _append_hoiphu(text: str, question: str, added_date: str) -> str:
    """Chèn 1 bullet '- [YYYY-MM-DD] <q>' NGAY DƯỚI heading '## Hỏi phụ'; tạo section nếu thiếu.
    Không đụng heading/section khác. Split/join theo '\\n' để giữ nguyên newline cuối file.
    LIGHT validate lại sau (AST) → nếu chèn hỏng sẽ bị bắt + abort (không tin mù text-edit)."""
    bullet = f"- [{added_date}] {question}"
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == _HOIPHU:
            lines.insert(i + 1, bullet)
            return "\n".join(lines)
    sep = "" if text.endswith("\n") else "\n"
    return text + f"{sep}\n{_HOIPHU}\n{bullet}\n"


def cmd_ask(vault: Path, system: Path, lesson_id: str, question: str, at: datetime):
    """Ghi câu hỏi phụ vào '## Hỏi phụ' của lesson.md (spec 14A/§11). Transaction-LIGHT (ghi-trong-phiên,
    body lesson.md, không đụng FSRS/view — spec 10.8). Trả (committed, report). Câu trả lời do AI làm trong chat."""
    vault, system = Path(vault), Path(system)
    _recover_first(vault)
    if not question.strip():
        raise SessionError("câu hỏi rỗng")
    if "/" not in lesson_id:
        raise SessionError(f"lesson_id phải dạng '<topic>/<lesson>': {lesson_id!r}")
    offset = _load_vault_state(vault)[0].get("utc_offset", "+00:00")
    added = at.astimezone(FA._parse_offset(offset)).date().isoformat()
    lp = _lesson_dir(vault, lesson_id) / "lesson.md"
    if not lp.is_file():
        raise SessionError(f"không thấy lesson.md của {lesson_id!r}")
    text = VIO.read_text(lp)
    ehr = VIO.content_hash(lp)
    new_text = _append_hoiphu(text, question, added)
    writes = [TX.Write(lp.relative_to(vault).as_posix(), new_text.encode("utf-8"), expected_read_hash=ehr)]
    return _run_tx(vault, system, writes, level="light", now=at)  # spec 10.8: ghi-trong-phiên = LIGHT


def cmd_test(vault: Path, system: Path, lesson_id: str | None = None) -> dict:
    """CHỈ ĐỌC (spec 9.3 + CR-0002): báo cáo cổng learned_gate cho lesson (mặc định = current_lesson).
    TÁI DÙNG validate._check_gate_and_evidence trên BẢN SAO lesson đặt status='learned' để dò cổng
    (không nhân đôi luật INV-07/22). KHÔNG ghi — việc đặt 'learned' để luồng dạy + /done làm."""
    vault = Path(vault)
    vs_raw = _load_vault_state(vault)[0]
    lesson_id = lesson_id or vs_raw.get("current_lesson")
    if not lesson_id or "/" not in lesson_id:
        raise SessionError(f"lesson_id không hợp lệ / thiếu current_lesson: {lesson_id!r}")
    ld = _lesson_dir(vault, lesson_id)
    ls_path = ld / "lesson_state.md"
    if not ls_path.is_file():
        raise SessionError(f"không thấy lesson_state.md của {lesson_id!r}")
    lm = _lesson_model_from_raw(_load_raw(ls_path)[0], ls_path)
    probe = lm.model_copy(update={"status": "learned"})  # dò: 'nếu đánh dấu learned thì cổng có qua?'
    rep = V.Report()
    V._check_gate_and_evidence(probe, ld, vault, rep)
    axes = {ax: {"score": getattr(lm.mastery, ax).score, "threshold": thr,
                 "meets": getattr(lm.mastery, ax).score >= thr}
            for ax, thr in V._GATE.items()}
    return {
        "lesson_id": lesson_id,
        "current_status": lm.status,
        "gate_pass": rep.ok(),
        "axes": axes,
        "blocking": [f"{e['error_code']}: {e['message']}" for e in rep.errors],
    }


def cmd_gaps(vault: Path, system: Path) -> list[dict]:
    """CHỈ ĐỌC (spec 11A.2 /gaps): liệt kê open_gaps của mọi lesson. Không ghi, không transaction."""
    out = []
    for lm in _all_lesson_models(Path(vault)):
        for g in lm.open_gaps:
            out.append({"lesson_id": lm.lesson_id, "gap_id": g.id,
                        "desc": g.desc, "detected": g.detected.isoformat()})
    return out


def _run_tx(vault: Path, system: Path, writes: list, tombstones: list | None = None,
            level: str = "full", now=None):
    """Chạy transaction ở `level` (spec 10.8): FULL cho /review /done /forget /learn;
    LIGHT cho ghi-trong-phiên (vd /source raw — không đụng FSRS/view/cross-ref).
    now = mốc thao tác (at) → validate_staged dùng cho INV-05 (updated<=today), giữ nhất quán:
    updated ghi theo `at` thì 'today' khi validate cũng theo `at` (tất định, không lệ đồng hồ)."""
    tx = TX.Transaction(vault, level=level, now=now)
    tx.begin(writes, tombstones=tombstones)
    tx.stage()
    rep = tx.validate_staged(system, level)
    if not rep.ok():
        tx.abort()
        return False, rep
    tx.occ_recheck()
    tx.commit()
    return True, rep


# ---- CLI (spec 10.5: /review /done là LỆNH SHELL, dán report nguyên văn) -----
def _parse_at(s: str) -> datetime:
    """ISO 8601 aware. Naive → lỗi (thời điểm phải xác định múi giờ, spec 8.5)."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"--at phải kèm offset (aware), vd '2026-07-02T17:00:00+07:00'; nhận {s!r}")
    return dt


def _emit(command: str, committed: bool, rep, as_json: bool, err: dict | None = None):
    if as_json:
        out = {
            "command": command,
            "committed": committed,
            "pass": bool(rep.ok()) if rep is not None else False,
            "errors": [err] if err else (rep.errors if rep is not None else []),
            "warnings": rep.warnings if rep is not None else [],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if err:
            print(f"FAIL — [{err['error_code']}] {err['message']}")
        elif rep is not None:
            rep.dump(False)  # report nguyên văn (spec 10.5)
        print(f"[{command}] committed={str(committed).lower()}")


def _print_readonly(p: dict) -> None:
    """In gọn kết quả lệnh chỉ-đọc (schedule/status/resume) — dạng người-đọc."""
    cmd = p.get("command")
    if cmd == "schedule":
        print(f"[schedule] due trong {p['days']} ngày tới: {len(p['due'])} item")
        for it in p["due"]:
            print(f"  - {it['lesson_id']} {it['item_id']} ({it['mastery_state']}, due {it['due_date']})")
    elif cmd == "status":
        print(f"[status] topic={p['current_topic']} lesson={p['current_lesson']} "
              f"| due hôm nay: {p['due_today']} | gợi ý: /{p['suggestion']}")
        if p["unclosed_session"]:
            print(f"  ⚠ phiên {p['open_session_lesson']} mở từ {p['open_session_started_at']} "
                  f"CHƯA /done — chạy /done (FULL-validate) hoặc /validate (spec 11B.2)")
    elif cmd == "resume":
        print(f"[resume] lesson={p['current_lesson']} (status={p['status']})")
        print(f"  next_action: {p['next_action']}")
        if p["unclosed_session"]:
            print("  ⚠ có phiên chưa /done (spec 11B.2)")
    elif cmd == "gaps":
        print(f"[gaps] {len(p['gaps'])} open_gap:")
        for g in p["gaps"]:
            print(f"  - {g['lesson_id']} {g['gap_id']}: {g['desc']} (detected {g['detected']})")
    elif cmd == "test":
        print(f"[test] lesson={p['lesson_id']} status={p['current_status']} → gate_pass={p['gate_pass']}")
        for ax, d in p["axes"].items():
            print(f"  {'✓' if d['meets'] else '✗'} {ax}: {d['score']}/{d['threshold']}")
        for b in p["blocking"]:
            print(f"  ⛔ {b}")


CLI_COMMANDS = ("learn", "schedule", "status", "resume", "gaps", "test", "source", "collect", "curriculum", "blueprint", "next_lesson", "grade", "ask", "review", "done", "forget")  # backend session.py (khớp commands.md)

_READONLY_COMMANDS = ("schedule", "status", "gaps", "test")  # không transaction, không committed
# LƯU Ý: "resume" KHÔNG còn read-only từ CR-0003 (mở phiên = ghi vault_state, transaction-LIGHT).


def _build_parser() -> argparse.ArgumentParser:
    """Dựng argparse (tách khỏi main để test introspect subcommands ↔ commands.md)."""
    ap = argparse.ArgumentParser(prog="session.py")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in CLI_COMMANDS:
        sp = sub.add_parser(name)
        sp.add_argument("--system", required=True)
        sp.add_argument("--vault", required=True)
        sp.add_argument("--at", default=None, help="ISO 8601 aware; mặc định = now(UTC)")
        sp.add_argument("--json", action="store_true")
        if name == "learn":
            sp.add_argument("--topic", required=True, help="topic_id (slug ascii, không chứa '/')")
            sp.add_argument("--title", required=True)
            sp.add_argument("--lesson-title", dest="lesson_title", required=True)
            sp.add_argument("--objective", required=True)
        elif name == "schedule":
            sp.add_argument("--days", type=int, default=0, help="số ngày tới (0 = hôm nay, spec 8.5)")
        elif name in ("status", "resume", "gaps"):
            pass  # CHỈ ĐỌC: chỉ dùng args chung (--system/--vault/--at/--json)
        elif name == "source":
            sp.add_argument("--topic", required=True, help="topic_id chứa nguồn")
            sp.add_argument("--ref", required=True, help="link/đường dẫn/mô tả nguồn")
            sp.add_argument("--kind", required=True, help="doc|link|repo|book|note|question")
            sp.add_argument("--scope", default="")
            sp.add_argument("--trust", default="unknown", help="unknown|low|medium|high")
        elif name == "collect":
            sp.add_argument("--topic", required=True, help="topic_id nhận lát cắt tài liệu")
            sp.add_argument("--slug", required=True, help="tên file .md trong reference/ (không path)")
            sp.add_argument("--content", required=True, help="nội dung markdown lát cắt (AI lấy từ nguồn)")
        elif name == "curriculum":
            sp.add_argument("--topic", required=True, help="topic_id dựng/sửa giáo trình")
            sp.add_argument("--points", default=None,
                            help='(DỰNG) JSON list điểm học: [{"objective": "...", "source_refs": [...]}]')
            sp.add_argument("--insert-at", dest="insert_at", type=int, default=None,
                            help="(CHÈN R8) vị trí 1..N+1 chèn điểm mới")
            sp.add_argument("--point", default=None,
                            help='(CHÈN R8) JSON một điểm: {"objective": "...", "source_refs": [...]}')
        elif name == "blueprint":
            sp.add_argument("--topic", required=True, help="topic_id dựng/sửa khung bắt buộc")
            sp.add_argument("--areas", default=None,
                            help='(DỰNG/EDIT/AMEND) JSON list mảng: [{"title":"...","mandatory":true,"source_refs":[...]}]')
            sp.add_argument("--edit", action="store_true", help="(EDIT) sửa areas khi draft")
            sp.add_argument("--approve", action="store_true", help="(APPROVE) chuyển draft→approved")
            sp.add_argument("--amend", action="store_true", help="(AMEND) sửa areas khi approved (cần --confirm)")
            sp.add_argument("--confirm", action="store_true", help="xác nhận tường minh cho --amend approved (R4.3)")
        elif name == "next_lesson":
            sp.add_argument("--topic", required=True, help="topic_id sinh lesson kế cho current_point")
        elif name == "grade":
            sp.add_argument("--topic", required=True, help="topic_id chứa bản ghi chấm")
            sp.add_argument("--submission", required=True, help="submission_id (ex-...)")
            sp.add_argument("--file", required=True, help="đường dẫn bài nộp trong exam/ (NGOÀI vault)")
            sp.add_argument("--target", required=True, help="topic_id hoặc curriculum point (cp-NNN)")
            sp.add_argument("--verdict", required=True, help="kết quả chấm (Class D, free-text)")
        elif name == "ask":
            sp.add_argument("--lesson", required=True)
            sp.add_argument("--question", required=True, help="câu hỏi phụ")
        elif name == "test":
            sp.add_argument("--lesson", default=None, help="mặc định = current_lesson")
        else:
            sp.add_argument("--lesson", required=True)
        if name == "review":
            sp.add_argument("--item", required=True)
            sp.add_argument("--grade", type=int, required=True)  # KHÔNG choices: để EReviewBadGrade bắt
        if name == "forget":
            sp.add_argument("--reason", default="")
            sp.add_argument("--confirm", action="store_true",
                            help="xác nhận tường minh của người dùng (spec 10.3a); thiếu → từ chối")
    return ap


def main(argv=None) -> int:
    # stdout UTF-8: report chứa tiếng Việt (đồng nhất với validate.py).
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    args = _build_parser().parse_args(argv)

    try:
        at = _parse_at(args.at) if args.at else datetime.now(timezone.utc)
    except ValueError as e:
        _emit(args.command, False, None, args.json, {"error_code": "E-ARG", "message": str(e)})
        return 2

    if args.command in _READONLY_COMMANDS:  # CHỈ ĐỌC: không transaction, không committed
        try:
            if args.command == "schedule":
                payload = {"command": "schedule", "days": args.days,
                           "due": cmd_schedule(Path(args.vault), Path(args.system), at, args.days)}
            elif args.command == "status":
                payload = {"command": "status", **cmd_status(Path(args.vault), Path(args.system), at)}
            elif args.command == "gaps":
                payload = {"command": "gaps", "gaps": cmd_gaps(Path(args.vault), Path(args.system))}
            else:  # test
                payload = {"command": "test", **cmd_test(Path(args.vault), Path(args.system), args.lesson)}
        except VIO.EIoEncoding as e:
            _emit(args.command, False, None, args.json, {"error_code": "E-IO-ENCODING", "message": str(e)})
            return 1
        except (OSError, SessionError) as e:
            _emit(args.command, False, None, args.json,
                  {"error_code": getattr(e, "error_code", "E-DRIVER"), "message": str(e)})
            return 1
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            _print_readonly(payload)
        return 0

    if args.command == "resume":  # WRITE (CR-0003): mở phiên trên current_lesson (transaction-LIGHT)
        try:
            committed, rep, info = cmd_resume(Path(args.vault), Path(args.system), at)
        except VIO.EIoEncoding as e:
            _emit("resume", False, None, args.json, {"error_code": "E-IO-ENCODING", "message": str(e)})
            return 1
        except (OSError, SessionError) as e:
            _emit("resume", False, None, args.json,
                  {"error_code": getattr(e, "error_code", "E-DRIVER"), "message": str(e)})
            return 1
        except TX.TxError as e:
            _emit("resume", False, None, args.json, {"error_code": e.code, "message": e.message})
            return 1
        if args.json:
            out = {"command": "resume", "committed": committed,
                   "pass": bool(rep.ok()) if rep is not None else True,
                   "errors": rep.errors if rep is not None else [],
                   "warnings": rep.warnings if rep is not None else [],
                   **info}
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            _print_readonly({"command": "resume", **info})
            print(f"[resume] committed={str(committed).lower()}")
        return 0 if committed else 1

    try:
        if args.command == "learn":
            committed, rep = cmd_learn(Path(args.vault), Path(args.system),
                                       args.topic, args.title, args.lesson_title, args.objective, at)
        elif args.command == "review":
            committed, rep = cmd_review(Path(args.vault), Path(args.system),
                                        args.lesson, args.item, args.grade, at)
        elif args.command == "done":
            committed, rep = cmd_done(Path(args.vault), Path(args.system), args.lesson, at)
        elif args.command == "source":
            committed, rep, _src_id = cmd_source(Path(args.vault), Path(args.system),
                                                 args.topic, args.ref, args.kind, at,
                                                 scope=args.scope, trust=args.trust)
        elif args.command == "collect":
            committed, rep, _ref = cmd_collect(Path(args.vault), Path(args.system),
                                               args.topic, args.slug, args.content, at)
        elif args.command == "curriculum":
            if args.insert_at is not None:   # CR-0010 R8: chế độ CHÈN điểm giữa chừng
                if not args.point:
                    raise SessionError("chế độ --insert-at cần --point (JSON một điểm)")
                committed, rep = cmd_curriculum_insert(Path(args.vault), Path(args.system),
                                                       args.topic, args.insert_at, args.point, at)
            else:                            # chế độ DỰNG mới
                if not args.points:
                    raise SessionError("/curriculum cần --points (DỰNG) hoặc --insert-at + --point (CHÈN)")
                committed, rep = cmd_curriculum(Path(args.vault), Path(args.system),
                                                args.topic, args.points, at)
        elif args.command == "blueprint":
            if args.approve:
                committed, rep = cmd_blueprint_approve(Path(args.vault), Path(args.system), args.topic, at)
            elif args.amend:
                if not args.areas:
                    raise SessionError("--amend cần --areas (JSON list mảng)")
                committed, rep = cmd_blueprint_amend(Path(args.vault), Path(args.system),
                                                     args.topic, args.areas, args.confirm, at)
            elif args.edit:
                if not args.areas:
                    raise SessionError("--edit cần --areas (JSON list mảng)")
                committed, rep = cmd_blueprint_edit(Path(args.vault), Path(args.system),
                                                    args.topic, args.areas, at)
            else:  # DỰNG mới
                if not args.areas:
                    raise SessionError("/blueprint cần --areas (DỰNG) hoặc --edit/--approve/--amend")
                committed, rep = cmd_blueprint(Path(args.vault), Path(args.system),
                                               args.topic, args.areas, at)
        elif args.command == "next_lesson":
            committed, rep = cmd_next_lesson(Path(args.vault), Path(args.system), args.topic, at)
        elif args.command == "grade":
            committed, rep = cmd_grade(Path(args.vault), Path(args.system), args.topic,
                                       args.submission, args.file, args.target, args.verdict, at)
        elif args.command == "ask":
            committed, rep = cmd_ask(Path(args.vault), Path(args.system),
                                     args.lesson, args.question, at)
        else:  # forget
            committed, rep = cmd_forget(Path(args.vault), Path(args.system),
                                        args.lesson, args.reason, args.confirm, at)
    except VIO.EIoEncoding as e:
        _emit(args.command, False, None, args.json, {"error_code": "E-IO-ENCODING", "message": str(e)})
        return 1
    except FA.EReviewBadGrade as e:
        _emit(args.command, False, None, args.json, {"error_code": "E-REVIEW-BADGRADE", "message": str(e)})
        return 1
    except SessionError as e:
        _emit(args.command, False, None, args.json,
              {"error_code": getattr(e, "error_code", "E-DRIVER"), "message": str(e)})
        return 1
    except TX.TxError as e:
        _emit(args.command, False, None, args.json, {"error_code": e.code, "message": e.message})
        return 1

    _emit(args.command, committed, rep, args.json)
    return 0 if committed else 1


if __name__ == "__main__":
    sys.exit(main())
