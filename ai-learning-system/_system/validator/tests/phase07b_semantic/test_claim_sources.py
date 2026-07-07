"""P07b-2b tests — nguồn của claim: INV-12 (E-CLAIM-NOSRC) + INV-13 (E-SRC-RAWUSED).

Gồm cả kiểm model Source mở rộng (trust/scope/added/anchors, spec 5.3) parse được.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402
import models as M    # noqa: E402


def _src(sid, status, anchors=()):
    return M.Source(id=sid, kind="doc", ref="x", status=status,
                    anchors=[M.SourceAnchor(**a) for a in anchors])


def _B(sid_refs, cid="clm-b"):
    return {"id": cid, "class": "B", "status": "confirmed", "text": "t",
            "source_refs": list(sid_refs), "premise_refs": [], "draft_reason": None}


def _codes(claims, sources):
    rep = V.Report()
    V._check_claims([(c, "topic.md") for c in claims], rep, sources)
    return [e["error_code"] for e in rep.errors]


# ---- model: Source mở rộng parse được (đầy đủ + tối thiểu) ------------
def test_source_model_full_and_minimal():
    full = M.Sources(**{
        "schema": "sources", "schema_version": 1, "topic_id": "docker",
        "sources": [{
            "id": "src-001", "kind": "doc", "ref": "https://x", "status": "confirmed",
            "trust": "high", "scope": "lesson 1", "added": date(2026, 6, 30),
            "anchors": [{"id": "a2", "locator": "trang 3", "quote": "trích nguyên văn",
                         "summary": "ý ngắn", "content_hash": "sha256:abc"}],
        }],
    })
    assert full.sources[0].anchors[0].quote == "trích nguyên văn"
    # tối thiểu (id/kind/ref/status) vẫn hợp lệ nhờ default
    mini = M.Sources(**{"schema": "sources", "schema_version": 1, "topic_id": "docker",
                        "sources": [{"id": "src-002", "kind": "note", "ref": "r", "status": "raw"}]})
    assert mini.sources[0].trust == "unknown" and mini.sources[0].anchors == []


# ---- INV-12: B confirmed có anchor confirmed hợp lệ → sạch -----------
def test_B_valid_anchor():
    sources = {"src-1": _src("src-1", "confirmed", anchors=[{"id": "a1", "quote": "q"}])}
    assert _codes([_B(["src-1#a1"])], sources) == []


# ---- INV-12: B confirmed thiếu source_refs → E-CLAIM-NOSRC -----------
def test_B_no_refs():
    assert "E-CLAIM-NOSRC" in _codes([_B([])], {})


# ---- INV-12: anchor trỏ nguồn 'processing' (không confirmed) → NOSRC --
def test_B_anchor_processing_source():
    sources = {"src-1": _src("src-1", "processing", anchors=[{"id": "a1", "quote": "q"}])}
    codes = _codes([_B(["src-1#a1"])], sources)
    assert "E-CLAIM-NOSRC" in codes
    assert "E-SRC-RAWUSED" not in codes  # processing không phải raw/rejected


# ---- INV-12: anchor id không tồn tại trên nguồn confirmed → NOSRC ----
def test_B_anchor_missing():
    sources = {"src-1": _src("src-1", "confirmed", anchors=[{"id": "aX", "quote": "q"}])}
    assert "E-CLAIM-NOSRC" in _codes([_B(["src-1#a1"])], sources)


# ---- INV-12: anchor tồn tại nhưng quote rỗng → NOSRC -----------------
def test_B_anchor_empty_quote():
    sources = {"src-1": _src("src-1", "confirmed", anchors=[{"id": "a1", "quote": "   "}])}
    assert "E-CLAIM-NOSRC" in _codes([_B(["src-1#a1"])], sources)


# ---- INV-13: dùng nguồn raw làm anchor → E-SRC-RAWUSED ---------------
def test_raw_source_used():
    sources = {"src-1": _src("src-1", "raw", anchors=[{"id": "a1", "quote": "q"}])}
    assert "E-SRC-RAWUSED" in _codes([_B(["src-1#a1"])], sources)


# ---- INV-13: nguồn rejected → E-SRC-RAWUSED --------------------------
def test_rejected_source_used():
    sources = {"src-1": _src("src-1", "rejected", anchors=[{"id": "a1", "quote": "q"}])}
    assert "E-SRC-RAWUSED" in _codes([_B(["src-1#a1"])], sources)
