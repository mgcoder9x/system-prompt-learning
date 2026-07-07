"""P07a — Curriculum_Validator: ràng buộc NGỮ NGHĨA của curriculum.md mà model KHÔNG bắt được.

Model (M.Curriculum) chỉ giữ ràng buộc CẤU TRÚC (id pattern, order>=1, status Literal, schema literal,
updated>=created) → sai kiểu/enum ra E-SCHEMA. Các vi phạm NGỮ NGHĨA dưới đây model cho qua, phải do
`_check_curriculum` phát mã RIÊNG (design R10.1: mỗi loại vi phạm một mã phân biệt):
  - id trùng giữa các point            → E-CURR-DUP-ID
  - order KHÔNG là hoán vị 1..N        → E-CURR-ORDER
  - objective rỗng (chỉ khoảng trắng)  → E-CURR-EMPTY-OBJECTIVE
RED-first: test gọi V._check_curriculum (chưa tồn tại lúc viết) → đỏ; sau khi hiện thực → xanh.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402


def _point(pid: str, order: int, objective: str = "Mục tiêu hợp lệ", status: str = "not_started",
           lesson_id=None, source_refs=None) -> str:
    ls = "null" if lesson_id is None else lesson_id
    refs = "[" + ", ".join(f'"{r}"' for r in (source_refs or [])) + "]"
    return (f"  - id: {pid}\n"
            f"    order: {order}\n"
            f"    objective: \"{objective}\"\n"
            f"    status: {status}\n"
            f"    lesson_id: {ls}\n"
            f"    source_refs: {refs}\n")


def _write_curriculum(topic_dir: Path, points_yaml: str, current_point: str = "cp-001") -> None:
    topic_dir.mkdir(parents=True, exist_ok=True)
    fm = ("---\n"
          "schema: curriculum\n"
          "schema_version: 1\n"
          "topic_id: docker\n"
          f"current_point: {current_point}\n"
          "teachable: false\n"
          "points:\n"
          f"{points_yaml}"
          "created: 2026-06-30\n"
          "updated: 2026-06-30\n"
          "---\n\n# Giáo trình\n")
    (topic_dir / "curriculum.md").write_text(fm, encoding="utf-8")


def _codes(topic_dir: Path, vault_root: Path, lesson_ids=frozenset()) -> list[str]:
    rep = V.Report()
    V._check_curriculum(topic_dir, vault_root, rep, set(lesson_ids))
    return [e["error_code"] for e in rep.errors]


def test_valid_curriculum_no_error(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_curriculum(td, _point("cp-001", 1) + _point("cp-002", 2))
    assert _codes(td, v) == [], "giáo trình hợp lệ không được có lỗi ngữ nghĩa"


def test_absent_curriculum_no_error(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    td.mkdir(parents=True)
    # không có curriculum.md → không lỗi (curriculum là tùy chọn)
    assert _codes(td, v) == []


def test_duplicate_point_id(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_curriculum(td, _point("cp-001", 1) + _point("cp-001", 2))
    assert "E-CURR-DUP-ID" in _codes(td, v)


def test_order_not_permutation(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    # order 1 và 3 (thiếu 2) → không phải hoán vị 1..N
    _write_curriculum(td, _point("cp-001", 1) + _point("cp-002", 3))
    assert "E-CURR-ORDER" in _codes(td, v)


def test_empty_objective(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_curriculum(td, _point("cp-001", 1, objective="   ") + _point("cp-002", 2))
    assert "E-CURR-EMPTY-OBJECTIVE" in _codes(td, v)


# ---- Task 3.2: E-CURR-POINTER (current_point dangling, INV-03) ----------
def test_pointer_dangling(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    # current_point trỏ cp-999 không tồn tại trong points
    _write_curriculum(td, _point("cp-001", 1) + _point("cp-002", 2), current_point="cp-999")
    assert "E-CURR-POINTER" in _codes(td, v)


def test_pointer_valid(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_curriculum(td, _point("cp-001", 1) + _point("cp-002", 2), current_point="cp-002")
    assert "E-CURR-POINTER" not in _codes(td, v)


# ---- Task 3.2: E-CURR-LESSON-LINK (lesson_id trỏ lesson thật, INV-25) ----
def test_lesson_link_broken(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    # point trỏ lesson_id không có trong all_lesson_ids (không tồn tại trên đĩa)
    _write_curriculum(td, _point("cp-001", 1, lesson_id="docker/lesson-001") + _point("cp-002", 2))
    assert "E-CURR-LESSON-LINK" in _codes(td, v, lesson_ids=set())


def test_lesson_link_ok(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    _write_curriculum(td, _point("cp-001", 1, lesson_id="docker/lesson-001") + _point("cp-002", 2))
    assert "E-CURR-LESSON-LINK" not in _codes(td, v, lesson_ids={"docker/lesson-001"})


# ---- Task 3.3: E-CURR-REF-BROKEN (source_refs trỏ file reference/ tồn tại) ----
def test_ref_broken(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    # source_ref trỏ file reference/ KHÔNG tồn tại trên đĩa
    _write_curriculum(td, _point("cp-001", 1, source_refs=["reference/missing.md"]) + _point("cp-002", 2))
    assert "E-CURR-REF-BROKEN" in _codes(td, v)


def test_ref_ok(tmp_path):
    v = tmp_path / "vault"
    td = v / "topics" / "docker"
    (td / "reference").mkdir(parents=True)
    (td / "reference" / "roadmap.md").write_text("# lát cắt roadmap docker\n", encoding="utf-8")
    _write_curriculum(td, _point("cp-001", 1, source_refs=["reference/roadmap.md"]) + _point("cp-002", 2))
    assert "E-CURR-REF-BROKEN" not in _codes(td, v)
