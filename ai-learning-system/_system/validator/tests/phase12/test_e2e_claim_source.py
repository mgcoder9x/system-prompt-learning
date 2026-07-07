"""P12 (một phần) — E2E hệ CLAIM/NGUỒN ở mức TOÀN VAULT (spec 0.1/5.5/15.1, INV-12/13/15/23).

Trước đây INV-12/13/15 chỉ test ĐƠN VỊ (_check_claims với dict). Test này soạn sources.md (confirmed +
anchor) + lesson_notes.md (## Claims, claim lớp B trỏ anchor) vào vault THẬT rồi chạy validate_full_semantic
TOÀN VAULT → chứng minh pipeline nguồn→claim chạy ghép. Kèm ca ÂM để chắc enforcement thật sự kích.

Soạn file như AI làm trong phiên (claim là nội dung AI-authored, validate ở /done FULL) — không bịa:
shape claim/source bám test_claim_sources.py + models.py + spec 5.5.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
DOCKER = "topics/docker"
LESSON = f"{DOCKER}/lessons/lesson-001"
NOW = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)  # >= mọi ngày trong fixture → INV-05 tất định


def _sources_md(status: str = "confirmed") -> str:
    return (
        "---\n"
        "schema: sources\n"
        "schema_version: 1\n"
        "topic_id: docker\n"
        "sources:\n"
        "  - id: src-001\n"
        "    kind: doc\n"
        '    ref: "https://docs.docker.com/get-started/"\n'
        f"    status: {status}\n"
        "    trust: high\n"
        '    scope: "lesson 1"\n'
        "    added: 2026-06-30\n"
        "    anchors:\n"
        "      - id: a1\n"
        '        locator: "get-started"\n'
        '        quote: "A container is a sandboxed process"\n'
        '        summary: "định nghĩa container"\n'
        "---\n\n# Nguồn — docker\n"
    )


_FENCE = "`" * 3


def _notes_md(claim_body: str, heading: str = "Claims") -> str:
    return (
        "# Ghi chú — Container là gì\n\n"
        "## Tóm tắt ngắn\nContainer cô lập tiến trình, chia sẻ kernel.\n\n"
        f"## {heading}\n\n"
        f"{_FENCE}yaml\n{claim_body}\n{_FENCE}\n"
    )


# claim lớp B hợp lệ, trỏ anchor confirmed
_CLAIM_B_OK = (
    "claims:\n"
    "  - id: clm-001\n"
    "    class: B\n"
    "    status: confirmed\n"
    '    text: "Container là tiến trình cô lập, chia sẻ kernel host."\n'
    '    source_refs: ["src-001#a1"]\n'
    "    premise_refs: []\n"
    "    draft_reason: null\n"
)


def _vault(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _codes(vault: Path) -> list[str]:
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=NOW)
    return [e["error_code"] for e in rep.errors]


def _write(vault: Path, sources: str, notes: str) -> None:
    (vault / DOCKER / "sources.md").write_text(sources, encoding="utf-8")
    (vault / LESSON / "lesson_notes.md").write_text(notes, encoding="utf-8")


# ---- DƯƠNG: nguồn confirmed + claim B hợp lệ → toàn vault FULL PASS ----
def test_confirmed_source_and_class_B_claim_passes(tmp_path):
    v = _vault(tmp_path)
    _write(v, _sources_md("confirmed"), _notes_md(_CLAIM_B_OK))
    codes = _codes(v)
    assert codes == [], f"claim B hợp lệ mà FULL vẫn báo lỗi: {codes}"


# ---- ÂM: nguồn raw dùng làm anchor → E-SRC-RAWUSED (INV-13) ----
def test_raw_source_used_as_anchor(tmp_path):
    v = _vault(tmp_path)
    _write(v, _sources_md("raw"), _notes_md(_CLAIM_B_OK))
    assert "E-SRC-RAWUSED" in _codes(v)


# ---- ÂM: B confirmed không có anchor nguồn → E-CLAIM-NOSRC (INV-12) ----
def test_class_B_without_source_ref(tmp_path):
    v = _vault(tmp_path)
    claim = _CLAIM_B_OK.replace('    source_refs: ["src-001#a1"]\n', "    source_refs: []\n")
    _write(v, _sources_md("confirmed"), _notes_md(claim))
    assert "E-CLAIM-NOSRC" in _codes(v)


# ---- ÂM (khoá hồi quy): B confirmed trỏ nguồn KHÔNG TỒN TẠI (src-999) → E-CLAIM-NOSRC (INV-12) ----
#      ref treo không resolve = không có anchor confirmed hợp lệ; phải bắt, không im lặng.
def test_class_B_dangling_source_ref(tmp_path):
    v = _vault(tmp_path)
    claim = _CLAIM_B_OK.replace('    source_refs: ["src-001#a1"]\n', '    source_refs: ["src-999#a1"]\n')
    _write(v, _sources_md("confirmed"), _notes_md(claim))
    assert "E-CLAIM-NOSRC" in _codes(v)


# ---- ÂM (khoá hồi quy): B confirmed trỏ ANCHOR không tồn tại trong nguồn confirmed → E-CLAIM-NOSRC ----
def test_class_B_dangling_anchor(tmp_path):
    v = _vault(tmp_path)
    claim = _CLAIM_B_OK.replace('    source_refs: ["src-001#a1"]\n', '    source_refs: ["src-001#a99"]\n')
    _write(v, _sources_md("confirmed"), _notes_md(claim))
    assert "E-CLAIM-NOSRC" in _codes(v)


# ---- ÂM: claim thiếu class → E-CLAIM-UNCLASSED (INV-15) ----
def test_claim_missing_class(tmp_path):
    v = _vault(tmp_path)
    claim = _CLAIM_B_OK.replace("    class: B\n", "")
    _write(v, _sources_md("confirmed"), _notes_md(claim))
    assert "E-CLAIM-UNCLASSED" in _codes(v)


# ---- ÂM: claim đặt ngoài '## Claims' → E-CLAIM-LOC (INV-23) ----
def test_claim_outside_claims_section(tmp_path):
    v = _vault(tmp_path)
    _write(v, _sources_md("confirmed"), _notes_md(_CLAIM_B_OK, heading="Ghi chú khác"))
    assert "E-CLAIM-LOC" in _codes(v)
