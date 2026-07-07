"""P10 E2E — nghiệm thu vòng khung bắt buộc (mandatory-curriculum-framework) qua CLI thật, transaction mỗi bước.

(1) Chuỗi dương: blueprint(draft) → edit → approve → curriculum(area_refs phủ đủ) → validate PASS →
    next-lesson (transaction-FULL commit, area_refs bảo toàn) → validate PASS.
(2) Ca âm: approve → curriculum THIẾU phủ (teachable) → ABORT E-BP-AREA-UNCOVERED + không teachable + không lesson.
(3) Overlay (DEC-073): thao tác FULL sau khi có blueprint+curriculum KHÔNG false-positive (blueprint/curriculum
    đều TRONG vault → overlay resolve đúng).
(4) Backward-compat (P9): topic không blueprint → hành vi curriculum-driven cũ nguyên vẹn.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _full_ok(v: Path) -> bool:
    rep = V.Report()
    V.validate_full_semantic(ROOT, v, rep, now=AT)
    return rep.errors == []


def test_e2e_blueprint_happy_path(tmp_path):
    v = _fresh(tmp_path)
    # blueprint draft (2 mảng ban đầu)
    c, r = S.cmd_blueprint(v, ROOT, "docker", json.dumps([{"title": "Linux"}, {"title": "Image"}]), AT)
    assert c and _full_ok(v)
    # edit draft: giữ id ma-001/ma-002 + thêm ma-003
    edit = json.dumps([{"id": "ma-001", "title": "Linux nền tảng"},
                       {"id": "ma-002", "title": "Container & Image"},
                       {"title": "Compose"}])
    c, r = S.cmd_blueprint_edit(v, ROOT, "docker", edit, AT)
    assert c and _full_ok(v)
    # approve
    c, r = S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    assert c and _full_ok(v)
    # curriculum phủ đủ 3 mảng (ma-001..003)
    pts = json.dumps([{"objective": "Linux", "area_refs": ["ma-001"]},
                      {"objective": "Image", "area_refs": ["ma-002"]},
                      {"objective": "Compose", "area_refs": ["ma-003"]}])
    c, r = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert c, r.errors
    assert _full_ok(v)
    # next-lesson (transaction-FULL): sinh lesson cho cp-001, area_refs bảo toàn
    c, r = S.cmd_next_lesson(v, ROOT, "docker", AT)
    assert c, r.errors
    assert _full_ok(v)
    raw = S._load_raw(v / "topics" / "docker" / "curriculum.md")[0]
    cp1 = next(p for p in raw["points"] if p["id"] == "cp-001")
    assert cp1["area_refs"] == ["ma-001"] and cp1["lesson_id"] == "docker/lesson-002"


def test_e2e_incomplete_coverage_blocks_teach(tmp_path):
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", json.dumps([{"title": "Linux"}, {"title": "Image"}]), AT)
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    # curriculum chỉ phủ ma-001 (teachable) → ABORT
    pts = json.dumps([{"objective": "Linux", "area_refs": ["ma-001"]}])
    c, r = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert not c
    assert any(e["error_code"] == "E-BP-AREA-UNCOVERED" for e in r.errors)
    assert not (v / "topics" / "docker" / "curriculum.md").is_file()  # rollback


def test_e2e_backward_compat_no_blueprint(tmp_path):
    """P9: topic không blueprint → vòng curriculum cũ chạy nguyên vẹn, validate PASS."""
    v = _fresh(tmp_path)
    pts = json.dumps([{"objective": "A"}, {"objective": "B"}])
    c, r = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert c and _full_ok(v)
    c, r = S.cmd_next_lesson(v, ROOT, "docker", AT)
    assert c and _full_ok(v)


def test_e2e_amend_add_mandatory_breaks_coverage(tmp_path):
    """Amend approved thêm mảng mandatory MỚI trong khi curriculum teachable chưa phủ → ABORT (rollback),
    giữ guarantee: không thể có curriculum teachable dưới approved blueprint mà thiếu phủ."""
    v = _fresh(tmp_path)
    S.cmd_blueprint(v, ROOT, "docker", json.dumps([{"title": "Linux"}]), AT)  # ma-001
    S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    S.cmd_curriculum(v, ROOT, "docker", json.dumps([{"objective": "Linux", "area_refs": ["ma-001"]}]), AT)
    assert _full_ok(v)  # phủ đủ
    # amend thêm ma-002 mandatory (chưa point nào phủ) → coverage vỡ → ABORT
    amend = json.dumps([{"id": "ma-001", "title": "Linux"}, {"title": "Image"}])
    c, r = S.cmd_blueprint_amend(v, ROOT, "docker", amend, True, AT)
    assert not c
    assert any(e["error_code"] == "E-BP-AREA-UNCOVERED" for e in r.errors), r.errors
    # blueprint giữ nguyên 1 mảng (rollback)
    assert len(S._load_raw(v / "topics" / "docker" / "blueprint.md")[0]["areas"]) == 1
