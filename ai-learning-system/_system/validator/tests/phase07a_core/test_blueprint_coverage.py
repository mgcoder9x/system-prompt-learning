"""P07a — Blueprint_Validator PHỦ (Wave 4, approved-gated). Kiểm quan hệ blueprint↔curriculum:
  - area mandatory chưa được point nào phủ  → E-BP-AREA-UNCOVERED
  - point không ánh xạ area nào (approved)  → E-BP-POINT-OUTSIDE
Chỉ ép khi blueprint.status == 'approved' (QĐ-2 / R5.4 backward-compat). Draft → KHÔNG kích (P9).

Lưu ý kỷ luật: logic coverage hiện thực CÙNG _check_blueprint với cấu trúc (Wave 3) vì gắn chặt. Test này
được teeth-verified bằng disable-probe (xem DEC) — RED khi block coverage bị vô hiệu, GREEN khi khôi phục.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402


def _area(aid: str, order: int, mandatory: bool = True) -> str:
    mand = "true" if mandatory else "false"
    return (f"  - id: {aid}\n    order: {order}\n    title: \"Mảng {order}\"\n"
            f"    mandatory: {mand}\n    source_refs: []\n")


def _write_blueprint(td: Path, areas_yaml: str, status: str) -> None:
    td.mkdir(parents=True, exist_ok=True)
    (td / "blueprint.md").write_text(
        "---\nschema: blueprint\nschema_version: 1\ntopic_id: docker\n"
        f"status: {status}\nareas:\n{areas_yaml}"
        "created: 2026-06-30\nupdated: 2026-06-30\n---\n\n# Khung\n", encoding="utf-8")


def _write_curriculum(td: Path, area_refs_by_point: list[list[str]], teachable: bool = True) -> None:
    """Coverage là CỔNG của teachable → mặc định fixture teachable=true (khẳng định sẵn sàng dạy)."""
    td.mkdir(parents=True, exist_ok=True)
    pts = ""
    for i, refs in enumerate(area_refs_by_point, start=1):
        ry = "[" + ", ".join(f'"{r}"' for r in refs) + "]"
        pts += (f"  - id: cp-{i:03d}\n    order: {i}\n    objective: \"Điểm {i}\"\n"
                f"    status: not_started\n    lesson_id: null\n    source_refs: []\n    area_refs: {ry}\n")
    tch = "true" if teachable else "false"
    (td / "curriculum.md").write_text(
        "---\nschema: curriculum\nschema_version: 1\ntopic_id: docker\n"
        f"current_point: cp-001\nteachable: {tch}\npoints:\n{pts}"
        "created: 2026-06-30\nupdated: 2026-06-30\n---\n\n# Giáo trình\n", encoding="utf-8")


def _codes(td: Path, v: Path) -> list[str]:
    rep = V.Report()
    V._check_blueprint(td, v, rep)
    return [e["error_code"] for e in rep.errors]


def test_approved_uncovered_area_fails(tmp_path):
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2), status="approved")
    _write_curriculum(td, [["ma-001"]])  # ma-002 (mandatory) chưa phủ
    assert "E-BP-AREA-UNCOVERED" in _codes(td, v)


def test_approved_full_coverage_ok(tmp_path):
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2), status="approved")
    _write_curriculum(td, [["ma-001"], ["ma-002"]])
    assert _codes(td, v) == []


def test_draft_uncovered_no_error(tmp_path):
    """P9 backward-compat: draft blueprint KHÔNG ép phủ (kể cả curriculum teachable)."""
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2), status="draft")
    _write_curriculum(td, [["ma-001"]], teachable=True)  # ma-002 chưa phủ nhưng draft → không lỗi
    assert "E-BP-AREA-UNCOVERED" not in _codes(td, v)
    assert "E-BP-POINT-OUTSIDE" not in _codes(td, v)


def test_approved_not_teachable_no_coverage_error(tmp_path):
    """CỔNG teachable: approved blueprint + curriculum teachable=false (đang dựng) → CHƯA ép phủ.
    Coverage chỉ chặn khi curriculum KHẲNG ĐỊNH sẵn sàng dạy (teachable=true) — R3.3 contrapositive."""
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2), status="approved")
    _write_curriculum(td, [["ma-001"]], teachable=False)  # thiếu ma-002 nhưng chưa teachable → PASS
    assert "E-BP-AREA-UNCOVERED" not in _codes(td, v)
    assert "E-BP-POINT-OUTSIDE" not in _codes(td, v)


def test_approved_point_outside_fails(tmp_path):
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1, mandatory=False), status="approved")
    _write_curriculum(td, [[]])  # point không ánh xạ area nào
    assert "E-BP-POINT-OUTSIDE" in _codes(td, v)


def test_approved_optional_area_not_required(tmp_path):
    """Area mandatory=false KHÔNG cần phủ (chỉ mandatory=true mới ép)."""
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1, mandatory=True) + _area("ma-002", 2, mandatory=False),
                     status="approved")
    _write_curriculum(td, [["ma-001"]])  # phủ ma-001 (mandatory); ma-002 optional không cần
    assert "E-BP-AREA-UNCOVERED" not in _codes(td, v)


def test_approved_no_curriculum_passes(tmp_path):
    """Approved blueprint nhưng CHƯA có curriculum → PASS (không brick vault; luồng approve→dựng-curriculum).
    Coverage là cổng teachable, không có curriculum = chưa khẳng định dạy → không vi phạm."""
    v = tmp_path / "vault"; td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1), status="approved")
    assert _codes(td, v) == []
