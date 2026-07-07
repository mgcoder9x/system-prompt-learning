"""P10 driver — GAP: /done phải regen has_draft_knowledge (INV-26/§15.1).

Tái hiện gap: có draft claim trong lesson_notes → /done regen 'core' (không đụng has_draft_knowledge)
→ topic_state.has_draft_knowledge (false) lệch thực tế (true) → FULL validate E-DRAFT-IN-MAP → /done abort.
Fix gốc: regen 'full' (claim_texts) + set has_draft_knowledge trong mọi đường regen view.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)
NOTES = "topics/docker/lessons/lesson-001/lesson_notes.md"
TS = "topics/docker/topic_state.md"

_FENCE = "`" * 3
_DRAFT_NOTES = (
    "# Ghi chú — Container là gì\n\n"
    "## Tóm tắt ngắn\nContainer cô lập tiến trình.\n\n"
    "## Claims\n\n"
    f"{_FENCE}yaml\n"
    "claims:\n"
    "  - id: clm-d1\n"
    "    class: C\n"
    "    status: draft\n"
    '    text: "Giả thuyết chưa nguồn-hoá về namespace."\n'
    "    source_refs: []\n"
    "    premise_refs: []\n"
    '    draft_reason: "chưa có nguồn, dạy chế độ draft"\n'
    f"{_FENCE}\n"
)


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def test_done_with_draft_claim_syncs_has_draft(tmp_path):
    v = _fresh(tmp_path)
    (v / NOTES).write_text(_DRAFT_NOTES, encoding="utf-8")   # AI thêm draft claim trong phiên
    committed, rep = S.cmd_done(v, ROOT, "docker/lesson-001", AT)
    assert committed, f"/done phải đóng được khi có draft claim (regen has_draft): {rep.errors}"
    ts = S._load_raw(v / TS)[0]
    assert ts["has_draft_knowledge"] is True, "has_draft_knowledge phải = true khi có draft"
    rep2 = V.Report()
    V.validate_full_semantic(ROOT, v, rep2, now=AT)
    assert rep2.ok(), f"vault sau /done phải FULL PASS: {rep2.errors}"


def test_done_without_draft_keeps_false(tmp_path):
    v = _fresh(tmp_path)
    committed, rep = S.cmd_done(v, ROOT, "docker/lesson-001", AT)
    assert committed, rep.errors
    ts = S._load_raw(v / TS)[0]
    assert ts["has_draft_knowledge"] is False, "không draft → phải giữ false (fix không set bừa true)"


def test_forget_lesson_with_draft_recomputes_has_draft(tmp_path):
    # Nhánh exclude_lesson_id của fix DEC-027: /forget lesson chứa draft → draft đó KHÔNG còn tính.
    # Không có exclude, _topic_claim_texts đọc notes lesson (file còn trên đĩa lúc regen) → has_draft=true
    # nhưng lesson bị xoá → sau commit actual=0 → E-DRAFT-IN-MAP → /forget kẹt. Test này khoá nhánh đó.
    v = _fresh(tmp_path)
    (v / NOTES).write_text(_DRAFT_NOTES, encoding="utf-8")   # lesson-001 có draft
    committed, rep = S.cmd_forget(v, ROOT, "docker/lesson-001", "dọn dẹp", True, AT)
    assert committed, f"/forget lesson chứa draft phải đóng được (exclude khỏi has_draft): {rep.errors}"
    ts = S._load_raw(v / TS)[0]
    assert ts["has_draft_knowledge"] is False, "draft nằm ở lesson vừa xoá → topic không còn draft"
    rep2 = V.Report()
    V.validate_full_semantic(ROOT, v, rep2, now=AT)
    assert rep2.ok(), f"vault sau /forget phải FULL PASS: {rep2.errors}"
