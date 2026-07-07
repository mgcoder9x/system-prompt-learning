"""P10-agent — nhất quán _system/rules/*.md ↔ hằng số code (chống trôi single-source-of-truth).

review_rules.grade_to_rating == fsrs_adapter.MAP_GRADE_TO_RATING;
teaching_rules.learned_gate == validate._GATE; anchored_examples ≥3/trục (spec 9.5).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A       # noqa: E402
import fsrs_adapter as FA  # noqa: E402
import validate as V     # noqa: E402

RULES = ROOT / "rules"
AXES = ("concept", "explain", "apply", "critique", "teachback")


def _yaml_under(fname, heading):
    text = (RULES / fname).read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, heading, level=3)


# ---- grade→rating docs khớp code -------------------------------------
def test_grade_to_rating_matches_code():
    data = _yaml_under("review_rules.md", "grade_to_rating (máy đọc)")
    mapping = data["grade_to_rating"]
    assert set(mapping) == set(FA.MAP_GRADE_TO_RATING), "grade keys lệch code"
    for g, r in mapping.items():
        assert FA.MAP_GRADE_TO_RATING[g].value == r, f"grade {g}: doc {r} != code {FA.MAP_GRADE_TO_RATING[g].value}"


# ---- learned_gate docs khớp code -------------------------------------
def test_learned_gate_matches_code():
    data = _yaml_under("teaching_rules.md", "learned_gate (máy đọc)")
    assert data["learned_gate"] == V._GATE


# ---- anchored examples: ≥3/trục, đủ field (spec 9.5) -----------------
def test_anchored_examples_min_3_per_axis():
    data = _yaml_under("teaching_rules.md", "anchored_examples (máy đọc)")
    ex = data["anchored_examples"]
    for ax in AXES:
        assert ax in ex, f"thiếu trục {ax}"
        assert len(ex[ax]) >= 3, f"trục {ax} < 3 ví dụ neo (spec 9.5)"
        for e in ex[ax]:
            assert {"answer", "grade", "reason"} <= set(e), f"{ax}: ví dụ thiếu field"
            assert 0 <= e["grade"] <= 3, f"{ax}: grade ngoài 0..3"
