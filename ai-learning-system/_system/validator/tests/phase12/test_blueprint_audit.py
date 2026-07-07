"""P12 AUDIT đối kháng — mandatory-curriculum-framework (Topic_Blueprint).

Bài học DEC-073/NOTE-036: validate STANDALONE + E2E happy-path CÓ THỂ bỏ sót bug tích hợp (đặc biệt
transaction-overlay + tương tác chéo). Bộ này probe các khoảng happy-path (test_e2e_blueprint) CHƯA phủ:

  A1 — /done AUTO-ADVANCE dưới blueprint approved (DEC-065 × blueprint): learn→next-lesson→learned→done
       → auto-advance chạy _check_blueprint trong transaction-overlay FULL; area_refs bảo toàn; coverage giữ.
  A2 — Overlay tường minh (DEC-073 class): lệnh FULL-transaction SAU khi có blueprint+curriculum KHÔNG
       false-positive (blueprint/curriculum đều TRONG vault → overlay resolve đúng).
  A3 — Robustness (DEC-071 class): blueprint.md sửa-tay-hỏng (YAML hợp lệ, SAI KIỂU) → E-SCHEMA sạch,
       KHÔNG crash traceback (qua lệnh đọc blueprint).
  A4 — INV-16: blueprint source_refs đường dẫn tuyệt đối → E-PORT-ABSPATH (portable).
  A5 — Tất định: cùng blueprint hỏng → cùng tập mã + thứ tự qua nhiều lần chạy (không lệ đồng hồ/thứ tự).

Test PASS-ngay là hợp lệ (audit/regression — tài liệu hoá scenario hoạt-động-đúng, tiền lệ DEC-068/NOTE-021);
nếu FAIL → đã lộ bug tích hợp cần fix GỐC.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S      # noqa: E402
import validate as V     # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc)       # 10:00 +07
DONE_AT = datetime(2026, 7, 6, 5, 0, tzinfo=timezone.utc)  # 12:00 +07

TRANSCRIPT = ("Container chia sẻ kernel host nên nhẹ hơn máy ảo. "
              "Khác máy ảo ở chỗ không ảo hoá phần cứng. "
              "Dùng docker run để khởi chạy một container. "
              "Nhược điểm là cách ly yếu hơn máy ảo. "
              "Container gói tiến trình cùng toàn bộ phụ thuộc.")
_QUOTES = {
    "concept": "Container chia sẻ kernel host nên nhẹ hơn máy ảo.",
    "explain": "Khác máy ảo ở chỗ không ảo hoá phần cứng.",
    "apply": "Dùng docker run để khởi chạy một container.",
    "critique": "Nhược điểm là cách ly yếu hơn máy ảo.",
    "teachback": "Container gói tiến trình cùng toàn bộ phụ thuộc.",
}
_SCORES = {"concept": 2, "explain": 2, "apply": 2, "critique": 1, "teachback": 2}


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    return v


def _full_errors(vault: Path, now=DONE_AT):
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, vault, rep, now=now)
    return [e["error_code"] for e in rep.errors]


def _make_lesson_learned(vault: Path, lesson_rel: str):
    ld = vault / "topics" / "docker" / "lessons" / lesson_rel
    lp = ld / "lesson_state.md"
    raw, body = S._load_raw(lp)
    raw["status"] = "learned"
    for ax, sc in _SCORES.items():
        raw["mastery"][ax] = {"score": sc, "evidence": []}
    lp.write_bytes(S._dump_state(raw, body))
    evs = "\n".join(
        f"#### Evidence ev-{ax}\n\n```yaml\naxis: {ax}\ntimestamp: 2026-07-06\n"
        f"quote: \"{q}\"\nai_assessment: \"đạt\"\n```\n"
        for ax, q in _QUOTES.items())
    md = (f"# {lesson_rel}\n\n## Mục tiêu\nHọc.\n\n## Sessions\n\n"
          f"### Session 2026-07-06\n#### Bạn trả lời q1\n{TRANSCRIPT}\n\n{evs}")
    (ld / "lesson.md").write_text(md, encoding="utf-8")


def _approved_blueprint_covered_curriculum(v: Path):
    """blueprint approved (ma-001,ma-002) + curriculum teachable phủ đủ (2 point → ma-001, ma-002)."""
    S.cmd_blueprint(v, SYSTEM, "docker", json.dumps([{"title": "Linux"}, {"title": "Image"}]), AT)
    S.cmd_blueprint_approve(v, SYSTEM, "docker", AT)
    pts = json.dumps([{"objective": "Linux", "area_refs": ["ma-001"]},
                      {"objective": "Image", "area_refs": ["ma-002"]}])
    c, rep = S.cmd_curriculum(v, SYSTEM, "docker", pts, AT)
    assert c, rep.errors


# ---- A1: /done auto-advance DƯỚI blueprint approved -----------------------
def test_done_autoadvance_under_approved_blueprint(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    _approved_blueprint_covered_curriculum(v)
    # next-lesson cho cp-001 → lesson-002; học qua gate; done → auto-advance (chạy _check_blueprint overlay)
    c, rep = S.cmd_next_lesson(v, SYSTEM, "docker", AT)
    assert c, rep.errors
    _make_lesson_learned(v, "lesson-002")
    c, rep = S.cmd_done(v, SYSTEM, "docker/lesson-002", done_at=DONE_AT)
    assert c, f"/done dưới blueprint approved phải commit (auto-advance + coverage giữ): {rep.errors}"
    cur = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["status"] == "done" and cur["current_point"] == "cp-002"
    assert cp1["area_refs"] == ["ma-001"], "auto-advance KHÔNG được làm mất area_refs (bảo toàn phủ)"
    assert _full_errors(v) == [], "vault PASS full sau done+auto-advance dưới blueprint"


# ---- A2: overlay tường minh (DEC-073 class) -------------------------------
def test_full_transaction_no_false_positive_with_blueprint(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    _approved_blueprint_covered_curriculum(v)
    # next-lesson là transaction-FULL: validate chạy trên OVERLAY. blueprint+curriculum trong vault →
    # overlay copy đủ → KHÔNG false-positive E-BP-*.
    c, rep = S.cmd_next_lesson(v, SYSTEM, "docker", AT)
    assert c, f"overlay false-positive E-BP-*? {rep.errors}"
    assert not any(e["error_code"].startswith("E-BP-") for e in rep.errors)


# ---- A3: robustness — blueprint.md sửa-tay-hỏng → E-SCHEMA sạch -----------
def test_broken_blueprint_clean_schema_error(tmp_path):
    v = _fresh(tmp_path)
    bp = v / "topics" / "docker" / "blueprint.md"
    # YAML HỢP LỆ nhưng SAI KIỂU: areas là chuỗi (không phải list) + status ngoài enum
    bp.write_text("---\nschema: blueprint\nschema_version: 1\ntopic_id: docker\n"
                  "status: xong\nareas: khong-phai-list\ncreated: 2026-06-30\nupdated: 2026-06-30\n---\n\n# x\n",
                  encoding="utf-8")
    # lệnh đọc blueprint (approve) phải suy biến → E-SCHEMA sạch (SessionError), KHÔNG crash traceback
    with pytest.raises(S.SessionError) as ei:
        S.cmd_blueprint_approve(v, SYSTEM, "docker", AT)
    assert getattr(ei.value, "error_code", "E-DRIVER") == "E-SCHEMA"
    # validator cũng báo E-SCHEMA (không crash)
    assert "E-SCHEMA" in _full_errors(v)


# ---- A4: INV-16 — blueprint source_refs đường dẫn tuyệt đối → E-PORT-ABSPATH
def test_blueprint_abspath_source_ref_flagged(tmp_path):
    v = _fresh(tmp_path)
    bp = v / "topics" / "docker" / "blueprint.md"
    bp.write_text("---\nschema: blueprint\nschema_version: 1\ntopic_id: docker\nstatus: draft\n"
                  "areas:\n  - id: ma-001\n    order: 1\n    title: \"Linux\"\n    mandatory: true\n"
                  "    source_refs: [\"C:\\\\Users\\\\x\\\\ref.md\"]\n"
                  "created: 2026-06-30\nupdated: 2026-06-30\n---\n\n# x\n", encoding="utf-8")
    assert "E-PORT-ABSPATH" in _full_errors(v), "abspath trong blueprint phải bị E-PORT-ABSPATH (INV-16)"


# ---- A5: tất định — cùng blueprint hỏng → cùng tập mã qua nhiều lần chạy --
def test_blueprint_error_determinism(tmp_path):
    v = _fresh(tmp_path)
    td = v / "topics" / "docker"
    # blueprint hỏng đa-lỗi: dup id + order hở + title rỗng
    (td / "blueprint.md").write_text(
        "---\nschema: blueprint\nschema_version: 1\ntopic_id: docker\nstatus: draft\nareas:\n"
        "  - id: ma-001\n    order: 1\n    title: \"A\"\n    mandatory: true\n    source_refs: []\n"
        "  - id: ma-001\n    order: 3\n    title: \"   \"\n    mandatory: true\n    source_refs: []\n"
        "created: 2026-06-30\nupdated: 2026-06-30\n---\n\n# x\n", encoding="utf-8")

    def _codes():
        rep = V.Report()
        V._check_blueprint(td, v, rep)
        return [e["error_code"] for e in rep.errors]

    r1, r2 = _codes(), _codes()
    assert r1 == r2, "thứ tự mã E-BP-* phải tất định qua các lần chạy"
    assert {"E-BP-DUP-ID", "E-BP-ORDER", "E-BP-EMPTY-TITLE"} <= set(r1)


# ---- A6: amend approved XÓA area đang được curriculum tham chiếu → ABORT (rollback) --
def test_amend_remove_referenced_area_aborts(tmp_path, monkeypatch):
    """Guarantee toàn vẹn tham chiếu dưới amend: xóa ma-002 khi cp-002.area_refs=[ma-002] →
    E-BP-AREA-REF-BROKEN → transaction rollback → blueprint GIỮ NGUYÊN 2 area (không mất toàn vẹn)."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    _approved_blueprint_covered_curriculum(v)  # ma-001,ma-002 ; cp-001→ma-001, cp-002→ma-002
    amend = json.dumps([{"id": "ma-001", "title": "Linux"}])  # bỏ ma-002 (còn cp-002 trỏ nó)
    c, rep = S.cmd_blueprint_amend(v, SYSTEM, "docker", amend, True, AT)
    assert not c, "amend xóa area đang được tham chiếu phải bị từ chối (rollback)"
    assert any(e["error_code"] == "E-BP-AREA-REF-BROKEN" for e in rep.errors), rep.errors
    areas = S._load_raw(v / "topics" / "docker" / "blueprint.md")[0]["areas"]
    assert len(areas) == 2, "blueprint phải giữ nguyên 2 area sau rollback (không mất toàn vẹn)"
