"""P12 E2E — Task 10: nghiệm thu vòng học-theo-giáo-trình tất định + bảo toàn bất biến.

Chuỗi THẬT trên vault tmp (mọi bước ghi PASS FULL):
  collect → curriculum → check(PASS) → next-lesson → (mô phỏng học qua learned_gate) → done →
  AUTO-ADVANCE (cp-001 done, current_point → cp-002) → next-lesson-2 (lesson cho cp-002).

Đây là 'hợp đồng nghiệm thu' cuối: chứng minh cả vòng khớp spec v2.7 (§3.5/§14 bước 4b) + auto-advance
đường learned=True chạy THẬT (không chỉ unit như DEC-065). + test bảo toàn bất biến (10.2).
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
AT = datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc)   # 10:00 +07
DONE_AT = datetime(2026, 7, 6, 5, 0, tzinfo=timezone.utc)  # 12:00 +07
POINTS = json.dumps([{"objective": "Container là gì"}, {"objective": "Image và Dockerfile"}])

# transcript chứa đủ 5 câu-quote (quote ⊆ transcript → không E-ASSESS-FAKEQUOTE)
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


def _full_errors(vault: Path, now=AT):
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, vault, rep, now=now)
    return [e["error_code"] for e in rep.errors]


def _make_lesson_learned(vault: Path, lesson_rel: str):
    """Mô phỏng AI dạy tới learned_gate: ghi lesson_state status=learned + mastery đạt ngưỡng +
    lesson.md có Sessions + transcript + 1 evidence/trục (quote ⊆ transcript). Giữ review_items."""
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


def test_e2e_curriculum_full_cycle(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    cur_path = v / "topics" / "docker" / "curriculum.md"

    # 1) collect: lát cắt tài liệu tham chiếu
    c, rep, ref = S.cmd_collect(v, SYSTEM, "docker", "container-basics",
                                "# Container\nChia sẻ kernel, nhẹ hơn máy ảo.\n", AT)
    assert c, rep.errors
    assert (v / "topics" / "docker" / "reference" / "container-basics.md").is_file()

    # 2) curriculum: dựng 2 điểm, teachable
    c, rep = S.cmd_curriculum(v, SYSTEM, "docker", POINTS, AT)
    assert c, rep.errors
    cur = S._load_raw(cur_path)[0]
    assert cur["teachable"] is True and len(cur["points"]) == 2
    assert cur["current_point"] == "cp-001"

    # 3) check: PASS (không mã curriculum/exam)
    errs = _full_errors(v)
    assert not [e for e in errs if e.startswith("E-CURR") or e.startswith("E-EXAM")], errs

    # 4) next-lesson: sinh lesson cho cp-001 (demo có lesson-001 → lesson-002)
    c, rep = S.cmd_next_lesson(v, SYSTEM, "docker", AT)
    assert c, rep.errors
    cur = S._load_raw(cur_path)[0]
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["lesson_id"] == "docker/lesson-002"
    assert cur["current_point"] == "cp-001"          # chưa /done → con trỏ chưa dời

    # 5) mô phỏng học qua learned_gate cho lesson-002
    _make_lesson_learned(v, "lesson-002")
    assert "E-GATE-FAIL" not in _full_errors(v, now=DONE_AT)  # lesson-002 thật sự qua cổng

    # 6) done: đóng sổ + AUTO-ADVANCE (learned=True path THẬT)
    c, rep = S.cmd_done(v, SYSTEM, "docker/lesson-002", done_at=DONE_AT)
    assert c, rep.errors
    cur = S._load_raw(cur_path)[0]
    cp1 = next(p for p in cur["points"] if p["id"] == "cp-001")
    assert cp1["status"] == "done", "cp-001 phải done sau /done qua gate (auto-advance)"
    assert cur["current_point"] == "cp-002", "current_point phải dời sang điểm kế chưa-done"

    # 7) next-lesson lần 2: sinh lesson cho cp-002
    c, rep = S.cmd_next_lesson(v, SYSTEM, "docker", DONE_AT)
    assert c, rep.errors
    cur = S._load_raw(cur_path)[0]
    cp2 = next(p for p in cur["points"] if p["id"] == "cp-002")
    assert cp2["lesson_id"] == "docker/lesson-003"

    # toàn vẹn FULL cuối chuỗi
    assert _full_errors(v, now=DONE_AT) == [], "vault phải PASS full sau trọn vòng giáo trình"


def test_e2e_invariants_preserved_with_curriculum(tmp_path, monkeypatch):
    """10.2: vault CÓ curriculum + exam_results vẫn PASS INV-16/17/18/25 (không mã lỗi nào)."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    S.cmd_curriculum(v, SYSTEM, "docker", POINTS, AT)
    # exam: bài nộp NGOÀI vault + grade
    sub = tmp_path / "exam" / "docker" / "sol.py"
    sub.parent.mkdir(parents=True, exist_ok=True)
    sub.write_text("print('ok')\n", encoding="utf-8")
    c, rep = S.cmd_grade(v, SYSTEM, "docker", "ex-001", str(sub), target="cp-001", verdict="pass", at=AT)
    assert c, rep.errors
    assert _full_errors(v) == [], "vault có curriculum + exam_results phải PASS toàn bộ bất biến"
