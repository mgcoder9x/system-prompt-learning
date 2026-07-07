"""P10 driver — cmd_learn: tạo topic MỚI + lesson-001 từ template, transaction-FULL (spec 11A.1).

Golden: /learn trên bản sao vault thật → committed=True (validate_staged FULL PASS) + file tạo đúng
+ vault sau đó FULL-validate PASS + con trỏ đồng bộ. Topic đã tồn tại → E-DRIVER (SessionError).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc)


def _fresh_vault(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def test_learn_creates_valid_new_topic(tmp_path):
    v = _fresh_vault(tmp_path)
    committed, rep = S.cmd_learn(v, ROOT, "python", "Python cơ bản",
                                 "Biến và kiểu", "Hiểu biến và kiểu dữ liệu", AT)
    assert committed, f"cmd_learn KHÔNG commit: {rep.errors}"
    # file tạo đúng cấu trúc
    tdir = v / "topics" / "python"
    assert (tdir / "topic_state.md").is_file()
    assert (tdir / "sources.md").is_file()
    ldir = tdir / "lessons" / "lesson-001"
    for name in ("lesson.md", "lesson_state.md", "lesson_notes.md"):
        assert (ldir / name).is_file(), f"thiếu {name}"


def test_learn_result_full_validates(tmp_path):
    v = _fresh_vault(tmp_path)
    committed, _ = S.cmd_learn(v, ROOT, "python", "Python", "Biến", "Hiểu biến", AT)
    assert committed
    rep = V.Report()
    V.validate_full_core(ROOT, v, rep, now=AT)
    assert rep.ok(), f"vault sau /learn KHÔNG PASS FULL: {rep.errors}"


def test_learn_syncs_pointers_and_index(tmp_path):
    v = _fresh_vault(tmp_path)
    S.cmd_learn(v, ROOT, "python", "Python", "Biến", "Hiểu biến", AT)
    vs_raw, _ = S._load_raw(v / "vault_state.md")
    assert vs_raw["current_topic"] == "python"
    assert vs_raw["current_lesson"] == "python/lesson-001"
    ts_raw, _ = S._load_raw(v / "topics" / "python" / "topic_state.md")
    assert ts_raw["current_lesson"] == "python/lesson-001"
    assert [e["id"] for e in ts_raw["lessons"]] == ["python/lesson-001"]


def test_learn_rejects_existing_topic(tmp_path):
    v = _fresh_vault(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_learn(v, ROOT, "docker", "Docker", "x", "y", AT)  # docker đã có trong vault demo


def test_learn_rejects_bad_topic_id(tmp_path):
    v = _fresh_vault(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_learn(v, ROOT, "a/b", "T", "x", "y", AT)  # topic_id không được chứa '/'


# ---- ROBUSTNESS: title/objective chứa ký tự đặc biệt YAML (':','#','\"') → KHÔNG crash, commit + PASS ----
# RED-first (phát hiện từ walkthrough Q5): _fill_template replace THÔ giá trị free-text vào front-matter
# YAML → 'Đệ quy: hàm...' phá YAML → yaml.ScannerError crash. Mục tiêu học có ':' là RẤT thường. Fix: thay
# free-text bằng scalar YAML-safe (json.dumps) trong front-matter; id/date giữ raw; body markdown giữ raw.
def test_learn_special_chars_in_title_objective(tmp_path):
    v = _fresh_vault(tmp_path)
    committed, rep = S.cmd_learn(
        v, ROOT, "recursion",
        'Đệ quy: nền tảng',                       # title có ':'
        'Base case "dừng" # quan trọng',           # lesson_title có '"' và '#'
        "Hiểu đệ quy: hàm tự gọi + điều kiện dừng",  # objective có ':'
        AT)
    assert committed, f"cmd_learn crash/không commit với ký tự đặc biệt: {rep.errors}"
    # giá trị round-trip ĐÚNG (không mất/không lệch)
    raw, _ = S._load_raw(v / "topics" / "recursion" / "lessons" / "lesson-001" / "lesson_state.md")
    assert raw["objective"] == "Hiểu đệ quy: hàm tự gọi + điều kiện dừng"
    ts, _ = S._load_raw(v / "topics" / "recursion" / "topic_state.md")
    assert ts["title"] == "Đệ quy: nền tảng"
    # validator FULL PASS
    rep2 = V.Report(); V.validate_full_core(ROOT, v, rep2, now=AT)
    assert rep2.ok(), rep2.errors


# ---- CR-0005: /learn tạo topic.md có section '## Lộ trình' (roadmap cấp-topic), validate PASS ----
# RED-first: hiện cmd_learn KHÔNG tạo topic.md → test đỏ. Fix: thêm topic.template.md + cmd_learn ghi topic.md.
def test_learn_creates_topic_md_with_roadmap(tmp_path):
    v = _fresh_vault(tmp_path)
    committed, rep = S.cmd_learn(v, ROOT, "python", "Python cơ bản",
                                 "Biến và kiểu", "Hiểu biến và kiểu dữ liệu", AT)
    assert committed, rep.errors
    tmd = v / "topics" / "python" / "topic.md"
    assert tmd.is_file(), "cmd_learn phải tạo topic.md (CR-0005)"
    body = tmd.read_text(encoding="utf-8")
    assert "## Lộ trình" in body, "topic.md phải có section '## Lộ trình'"
    # validator FULL vẫn PASS (topic.md không kích INV-23/26)
    rep2 = V.Report(); V.validate_full_semantic(ROOT, v, rep2, now=AT)
    assert rep2.ok(), rep2.errors
