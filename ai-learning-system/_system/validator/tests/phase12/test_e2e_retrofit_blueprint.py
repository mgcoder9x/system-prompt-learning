"""P12 E2E — CR-0015: retrofit area_refs giải quyết NOTE-039 (curriculum-first → áp-khung-về-sau).

Kịch bản CHỨNG MINH ngõ cụt NOTE-039 được giải:
  1. curriculum teachable 2 điểm KHÔNG area_refs (dựng TRƯỚC — curriculum-first).
  2. blueprint DRAFT 2 mảng bắt buộc.
  3. approve LÚC NÀY → FAIL (điểm chưa map → E-BP-POINT-OUTSIDE / E-BP-AREA-UNCOVERED) — đúng ngõ cụt cũ.
  4. RETROFIT: /curriculum --set-area-refs từng điểm (dưới blueprint draft → cổng phủ tắt → commit OK).
  5. approve lại → PASS (phủ đủ). validate --scope full PASS + next-lesson chạy.
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


def test_retrofit_curriculum_then_approve(tmp_path):
    v = _fresh(tmp_path)
    # 1. curriculum-first: teachable 2 điểm, KHÔNG area_refs
    pts = json.dumps([{"objective": "Linux"}, {"objective": "Image"}])
    c, r = S.cmd_curriculum(v, ROOT, "docker", pts, AT)
    assert c, r.errors
    assert _full_ok(v)  # không blueprint → PASS

    # 2. blueprint DRAFT 2 mảng bắt buộc (ma-001, ma-002)
    c, r = S.cmd_blueprint(v, ROOT, "docker",
                           json.dumps([{"title": "Linux nền tảng"}, {"title": "Container & Image"}]), AT)
    assert c, r.errors
    assert _full_ok(v)  # draft → cổng phủ tắt → PASS dù điểm chưa map

    # 3. approve LÚC NÀY → FAIL (ngõ cụt NOTE-039: điểm teachable chưa map area)
    c, r = S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    assert not c
    assert any(e["error_code"] in ("E-BP-POINT-OUTSIDE", "E-BP-AREA-UNCOVERED") for e in r.errors), r.errors
    assert S._load_raw(v / "topics" / "docker" / "blueprint.md")[0]["status"] == "draft"  # rollback → giữ draft

    # 4. RETROFIT dưới blueprint draft (cổng phủ tắt → mỗi bước commit OK)
    c, r = S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-001", json.dumps(["ma-001"]), AT)
    assert c, r.errors
    c, r = S.cmd_curriculum_set_area_refs(v, ROOT, "docker", "cp-002", json.dumps(["ma-002"]), AT)
    assert c, r.errors

    # 5. approve LẠI → PASS (phủ đủ)
    c, r = S.cmd_blueprint_approve(v, ROOT, "docker", AT)
    assert c, r.errors
    assert S._load_raw(v / "topics" / "docker" / "blueprint.md")[0]["status"] == "approved"
    assert _full_ok(v)  # phủ đủ dưới approved → validate full PASS

    # 6. dạy tiếp được (next-lesson transaction-FULL PASS) — ngõ cụt đã giải
    c, r = S.cmd_next_lesson(v, ROOT, "docker", AT)
    assert c, r.errors
    assert _full_ok(v)
