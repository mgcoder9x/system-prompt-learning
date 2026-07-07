"""P07a — Blueprint_Validator: ràng buộc NGỮ NGHĨA của blueprint.md mà model KHÔNG bắt được.

Model (M.Blueprint) chỉ giữ ràng buộc CẤU TRÚC (id pattern ^ma-*, order>=1, status Literal draft|approved,
mandatory bool, schema literal, updated>=created) → sai kiểu/enum ra E-SCHEMA. Các vi phạm NGỮ NGHĨA dưới
đây model cho qua, phải do `_check_blueprint` phát mã E-BP-* RIÊNG (design R6.1: mỗi loại một mã phân biệt):
  - id trùng giữa các area                 → E-BP-DUP-ID
  - order KHÔNG là hoán vị 1..N            → E-BP-ORDER
  - title rỗng (chỉ khoảng trắng)          → E-BP-EMPTY-TITLE
  - source_refs blueprint trỏ file thiếu   → E-BP-REF-BROKEN
  - curriculum point.area_refs trỏ area lạ → E-BP-AREA-REF-BROKEN (toàn vẹn tham chiếu INV-03; áp cả draft)

RED-first: test gọi V._check_blueprint (chưa tồn tại lúc viết) → đỏ; sau khi hiện thực → xanh.
Coverage (E-BP-AREA-UNCOVERED / E-BP-POINT-OUTSIDE) là Wave 4 (approved-gated) — ở test riêng.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402


def _area(aid: str, order: int, title: str = "Mảng hợp lệ", mandatory: bool = True,
          source_refs=None) -> str:
    refs = "[" + ", ".join(f'"{r}"' for r in (source_refs or [])) + "]"
    mand = "true" if mandatory else "false"
    return (f"  - id: {aid}\n"
            f"    order: {order}\n"
            f"    title: \"{title}\"\n"
            f"    mandatory: {mand}\n"
            f"    source_refs: {refs}\n")


def _write_blueprint(topic_dir: Path, areas_yaml: str, status: str = "draft") -> None:
    topic_dir.mkdir(parents=True, exist_ok=True)
    fm = ("---\n"
          "schema: blueprint\n"
          "schema_version: 1\n"
          "topic_id: docker\n"
          f"status: {status}\n"
          "areas:\n"
          f"{areas_yaml}"
          "created: 2026-06-30\n"
          "updated: 2026-06-30\n"
          "---\n\n# Khung giáo trình\n")
    (topic_dir / "blueprint.md").write_text(fm, encoding="utf-8")


def _write_curriculum_arearefs(topic_dir: Path, area_refs_by_point: list[list[str]]) -> None:
    """Ghi curriculum.md tối thiểu, mỗi point mang area_refs cho trước (để test ánh xạ point→area)."""
    topic_dir.mkdir(parents=True, exist_ok=True)
    pts = ""
    for i, refs in enumerate(area_refs_by_point, start=1):
        refs_yaml = "[" + ", ".join(f'"{r}"' for r in refs) + "]"
        pts += (f"  - id: cp-{i:03d}\n"
                f"    order: {i}\n"
                f"    objective: \"Điểm {i}\"\n"
                f"    status: not_started\n"
                f"    lesson_id: null\n"
                f"    source_refs: []\n"
                f"    area_refs: {refs_yaml}\n")
    fm = ("---\n"
          "schema: curriculum\n"
          "schema_version: 1\n"
          "topic_id: docker\n"
          "current_point: cp-001\n"
          "teachable: false\n"
          "points:\n"
          f"{pts}"
          "created: 2026-06-30\n"
          "updated: 2026-06-30\n"
          "---\n\n# Giáo trình\n")
    (topic_dir / "curriculum.md").write_text(fm, encoding="utf-8")


def _codes(topic_dir: Path, vault_root: Path) -> list[str]:
    rep = V.Report()
    V._check_blueprint(topic_dir, vault_root, rep)
    return [e["error_code"] for e in rep.errors]


def test_valid_blueprint_no_error(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2))
    assert _codes(td, v) == [], "khung hợp lệ không được có lỗi ngữ nghĩa"


def test_absent_blueprint_no_error(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    td.mkdir(parents=True)
    assert _codes(td, v) == []  # blueprint là tùy chọn


def test_dup_area_id(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-001", 2))
    assert "E-BP-DUP-ID" in _codes(td, v)


def test_order_not_permutation(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 3))  # thiếu 2
    assert "E-BP-ORDER" in _codes(td, v)


def test_empty_title(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1, title="   ") + _area("ma-002", 2))
    assert "E-BP-EMPTY-TITLE" in _codes(td, v)


def test_ref_broken(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1, source_refs=["reference/missing.md"]) + _area("ma-002", 2))
    assert "E-BP-REF-BROKEN" in _codes(td, v)


def test_ref_ok(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    (td / "reference").mkdir(parents=True)
    (td / "reference" / "linux.md").write_text("# lát cắt linux\n", encoding="utf-8")
    _write_blueprint(td, _area("ma-001", 1, source_refs=["reference/linux.md"]) + _area("ma-002", 2))
    assert "E-BP-REF-BROKEN" not in _codes(td, v)


# ---- E-BP-AREA-REF-BROKEN: curriculum point.area_refs trỏ area tồn tại (INV-03, cả draft) ----
def test_area_ref_broken(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2))
    _write_curriculum_arearefs(td, [["ma-999"], ["ma-002"]])  # ma-999 không tồn tại
    assert "E-BP-AREA-REF-BROKEN" in _codes(td, v)


def test_area_ref_ok(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_blueprint(td, _area("ma-001", 1) + _area("ma-002", 2))
    _write_curriculum_arearefs(td, [["ma-001"], ["ma-002"]])
    assert "E-BP-AREA-REF-BROKEN" not in _codes(td, v)
