"""P10-agent — schemas/*.schema.md khai báo ĐÚNG tập field của model pydantic (chống trôi doc↔code).

Với mỗi schema, khối máy-đọc `schema_fields` (required/optional, tên khóa document = alias nếu có)
phải khớp CHÍNH XÁC `Model.model_fields`. Thêm/bớt/đổi tên/đổi bắt-buộc field ở models.py mà quên
cập nhật schemas/ (hoặc ngược lại) → đỏ. 'Chân lý schema' vẫn ở models.py; đây là hợp đồng doc bám nó.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402
import models as M  # noqa: E402

SCHEMAS_DIR = ROOT / "schemas"

MODEL_BY_SCHEMA = {
    "lesson_state": M.LessonState,
    "vault_state": M.VaultState,
    "topic_state": M.TopicState,
    "sources": M.Sources,
    "review_item": M.ReviewItem,
    "curriculum": M.Curriculum,          # CR-0007
    "exam_results": M.ExamResults,       # CR-0007
    "blueprint": M.Blueprint,            # CR-0011
}


def _model_fields(model):
    """Tập (required, optional) khóa DOCUMENT-facing: alias nếu có, else tên field."""
    req, opt = set(), set()
    for name, fi in model.model_fields.items():
        key = fi.alias or name
        (req if fi.is_required() else opt).add(key)
    return req, opt


def _doc_fields(schema):
    text = (SCHEMAS_DIR / f"{schema}.schema.md").read_text(encoding="utf-8")
    block = A.extract_yaml_under_heading(text, "schema_fields (máy đọc)", level=3)
    sf = block["schema_fields"]
    return set(sf["required"]), set(sf["optional"]), sf


def test_all_schema_docs_present():
    for schema in MODEL_BY_SCHEMA:
        assert (SCHEMAS_DIR / f"{schema}.schema.md").is_file(), f"thiếu schemas/{schema}.schema.md"


@pytest.mark.parametrize("schema", sorted(MODEL_BY_SCHEMA))
def test_schema_doc_matches_model(schema):
    model = MODEL_BY_SCHEMA[schema]
    m_req, m_opt = _model_fields(model)
    d_req, d_opt, sf = _doc_fields(schema)
    assert sf["model"] == model.__name__, f"{schema}: model name doc={sf['model']!r} != {model.__name__!r}"
    assert d_req == m_req, f"{schema} required lệch: doc-thừa={sorted(d_req - m_req)}, model-thiếu-ở-doc={sorted(m_req - d_req)}"
    assert d_opt == m_opt, f"{schema} optional lệch: doc-thừa={sorted(d_opt - m_opt)}, model-thiếu-ở-doc={sorted(m_opt - d_opt)}"
