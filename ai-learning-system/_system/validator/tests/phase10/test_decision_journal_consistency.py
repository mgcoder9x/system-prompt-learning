"""P10-agent — Decision journal drift-guard: index.yaml ↔ các file .md phải KHỚP.

BỐI CẢNH (vì sao guard này là chống-drift GỐC nhất):
Nhật ký `_system/decisions/` là BỘ NHỚ XUYÊN-SUỐT mà START_HERE (bước 3) bắt mọi AI phiên sau đọc để không
lặp lỗi / không quyết lại điều đã chốt — tức XƯƠNG SỐNG chống-drift. Mọi artifact máy-đọc khác (schemas,
rules, router, claims, registry, handoff, anti_drift) ĐỀU đã có drift-guard; DUY NHẤT nhật ký này trước đây
KHÔNG có → nó tự trôi mà không ai bắt. Phiên 2026-07-08 gặp drift THẬT: NOTE-038 có dòng trong index.yaml
nhưng THIẾU khối trong notes.md. Guard này "canh chính người-gác".

KIỂM:
1. Song ánh: mỗi id heading '## <ID> —' trong .md ⇔ đúng 1 entry trong index.yaml (không orphan 2 chiều).
2. id DUY NHẤT (không tái dùng) trên toàn nhật ký (README quy ước: id vĩnh viễn, không dùng lại).
3. Đặt ĐÚNG file theo tiền tố: DEC→decisions.md, DEV→deviations.md, TRD→tradeoffs.md, NOTE→notes.md.
4. index.yaml hợp lệ + mỗi entry đủ field bắt buộc + type khớp tiền tố id.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]          # .../_system
DECISIONS = ROOT / "decisions"

_PREFIX_FILE = {"DEC": "decisions.md", "DEV": "deviations.md",
                "TRD": "tradeoffs.md", "NOTE": "notes.md"}
_PREFIX_TYPE = {"DEC": "decision", "DEV": "deviation", "TRD": "tradeoff", "NOTE": "note"}
_ID_HEADING = re.compile(r"^##\s+((?:DEC|DEV|TRD|NOTE)-\d+)\b", re.MULTILINE)
_REQUIRED_FIELDS = {"id", "type", "status", "verified", "method", "title"}


def _index():
    d = yaml.safe_load((DECISIONS / "index.yaml").read_text(encoding="utf-8"))
    return d["entries"]


def _md_ids(fname: str) -> list[str]:
    return _ID_HEADING.findall((DECISIONS / fname).read_text(encoding="utf-8"))


def _all_md_ids() -> dict[str, str]:
    """id -> file chứa nó (theo heading '## <id> —')."""
    out: dict[str, str] = {}
    for fname in _PREFIX_FILE.values():
        for _id in _md_ids(fname):
            out[_id] = fname   # nếu trùng sẽ bị test_no_duplicate bắt riêng
    return out


def test_index_valid_and_fields():
    entries = _index()
    assert entries, "index.yaml không có entry nào"
    for e in entries:
        missing = _REQUIRED_FIELDS - set(e)
        assert not missing, f"entry {e.get('id')!r} thiếu field {sorted(missing)}"


def test_no_duplicate_ids():
    # index
    idx_ids = [e["id"] for e in _index()]
    dup_idx = sorted({i for i in idx_ids if idx_ids.count(i) > 1})
    assert not dup_idx, f"index.yaml trùng id: {dup_idx}"
    # .md headings
    for fname in _PREFIX_FILE.values():
        ids = _md_ids(fname)
        dup = sorted({i for i in ids if ids.count(i) > 1})
        assert not dup, f"{fname} trùng heading id: {dup}"


def test_index_md_bijection():
    """Song ánh 2 chiều: index.yaml id-set == .md heading id-set (bắt đúng lớp NOTE-038)."""
    idx_ids = {e["id"] for e in _index()}
    md_ids = set(_all_md_ids())
    only_index = sorted(idx_ids - md_ids)
    only_md = sorted(md_ids - idx_ids)
    assert not only_index, f"id CÓ trong index.yaml nhưng THIẾU khối .md: {only_index}"
    assert not only_md, f"id CÓ khối .md nhưng THIẾU dòng index.yaml: {only_md}"


def test_prefix_placed_in_right_file():
    """DEC→decisions.md, DEV→deviations.md, TRD→tradeoffs.md, NOTE→notes.md (không lẫn file)."""
    for _id, fname in _all_md_ids().items():
        prefix = _id.split("-", 1)[0]
        assert _PREFIX_FILE[prefix] == fname, f"{_id} nằm sai file: {fname} (phải ở {_PREFIX_FILE[prefix]})"


def test_index_type_matches_prefix():
    for e in _index():
        prefix = e["id"].split("-", 1)[0]
        assert e["type"] == _PREFIX_TYPE[prefix], \
            f"{e['id']} có type={e['type']!r} không khớp tiền tố (phải {_PREFIX_TYPE[prefix]!r})"
