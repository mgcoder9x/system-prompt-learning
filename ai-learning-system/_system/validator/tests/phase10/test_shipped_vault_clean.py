"""Vault SHIP cho người dùng phải SẠCH + hợp lệ (không chứa dữ liệu demo).

Bối cảnh: trước đây learning_vault ship kèm topic 'docker' — vừa là demo vừa là fixture test → người
dùng mới bối rối 'sao có sẵn bài mình chưa học'. Fix gốc: demo chuyển thành fixture riêng
(validator/tests/fixtures/demo_vault), learning_vault ship RỖNG. Test này KHOÁ trạng thái sạch:
(1) validator PASS (core+semantic) trên vault ship; (2) topics/ RỖNG (khởi đầu trắng); (3) con trỏ null.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402
import session as S    # noqa: E402

SHIPPED = ROOT.parent / "learning_vault"
NOW = datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_shipped_vault_validates_full():
    rep = V.Report()
    V.validate_full_core(ROOT, SHIPPED, rep, now=NOW)
    V.validate_full_semantic(ROOT, SHIPPED, rep, now=NOW)
    assert rep.errors == [], f"vault ship phải PASS full, nhưng lỗi: {rep.errors}"


def test_shipped_vault_topics_empty():
    topics = SHIPPED / "topics"
    assert topics.is_dir(), "phải có thư mục topics/ (khởi đầu trắng, người dùng /learn để tạo)"
    subdirs = [p.name for p in topics.iterdir() if p.is_dir()]
    assert subdirs == [], f"vault ship phải KHÔNG chứa topic demo, nhưng thấy: {subdirs}"


def test_shipped_vault_pointers_null():
    raw = S._load_raw(SHIPPED / "vault_state.md")[0]
    assert raw.get("current_topic") in (None, "null"), f"current_topic phải null: {raw.get('current_topic')}"
    assert raw.get("current_lesson") in (None, "null"), f"current_lesson phải null: {raw.get('current_lesson')}"
