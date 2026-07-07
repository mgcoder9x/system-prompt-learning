"""P10-agent — validation_rules.md liệt kê ĐÚNG tập mã lỗi code thật phát ra (chống trôi doc↔code).

Quét literal E-* trong validate.py + transaction.py + session.py → tập phát ra;
so bằng với error_codes trong validation_rules.md (cả hai chiều).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

_SRC = ["validate.py", "transaction.py", "session.py"]
_RE = re.compile(r"""["'](E-[A-Z0-9]+(?:-[A-Z0-9]+)*)["']""")


def _emitted():
    codes = set()
    for f in _SRC:
        codes |= set(_RE.findall((ROOT / "validator" / f).read_text(encoding="utf-8")))
    return codes


def _documented():
    text = (ROOT / "rules" / "validation_rules.md").read_text(encoding="utf-8")
    data = A.extract_yaml_under_heading(text, "error_codes (máy đọc)", level=3)
    return set(data["error_codes"])


def test_doc_codes_equal_emitted():
    emitted, documented = _emitted(), _documented()
    missing = emitted - documented   # code phát ra nhưng chưa ghi doc
    fictional = documented - emitted  # ghi doc nhưng code không phát
    assert not missing, f"mã phát ra chưa ghi trong validation_rules.md: {sorted(missing)}"
    assert not fictional, f"mã ghi trong doc nhưng code không phát: {sorted(fictional)}"


def test_no_duplicate_in_doc():
    text = (ROOT / "rules" / "validation_rules.md").read_text(encoding="utf-8")
    lst = A.extract_yaml_under_heading(text, "error_codes (máy đọc)", level=3)["error_codes"]
    assert len(lst) == len(set(lst)), "error_codes có mã trùng"
