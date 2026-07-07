"""P10-agent — claim_rules.md khai báo ĐÚNG tập lớp/status mà code thật dùng (chống trôi doc↔code).

Khối máy-đọc `claim_taxonomy` trong rules/claim_rules.md phải khớp CHÍNH XÁC hằng số
validate._CLAIM_CLASSES / _CLAIM_STATUS. Đổi ở code mà quên cập nhật doc (hoặc ngược lại) → đỏ.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402
import validate as V  # noqa: E402


def _taxonomy():
    text = (ROOT / "rules" / "claim_rules.md").read_text(encoding="utf-8")
    data = A.extract_yaml_under_heading(text, "claim_taxonomy (máy đọc)", level=3)
    return data["claim_taxonomy"]


def test_claim_classes_match_code():
    doc = set(_taxonomy()["claim_classes"])
    assert doc == V._CLAIM_CLASSES, (
        f"claim_rules.md classes {sorted(doc)} != validate._CLAIM_CLASSES {sorted(V._CLAIM_CLASSES)}"
    )


def test_claim_statuses_match_code():
    doc = set(_taxonomy()["claim_statuses"])
    assert doc == V._CLAIM_STATUS, (
        f"claim_rules.md statuses {sorted(doc)} != validate._CLAIM_STATUS {sorted(V._CLAIM_STATUS)}"
    )
