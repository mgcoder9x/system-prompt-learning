"""P10 tests — CLI session.py (spec 10.5: /review /done là LỆNH SHELL, dán report nguyên văn).

Kiểm cả hai đường: gọi main(argv) in-process (nhanh, đọc exit-code + JSON) và một lần chạy
subprocess thật (chứng minh chạy được như lệnh shell độc lập môi trường).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session          # noqa: E402
import validate as V    # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = "2026-07-02T17:00:00+07:00"

LS_REL = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"


def _copy_vault(tmp_path) -> Path:
    dst = tmp_path / "learning_vault"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _rv(vault, *a):
    return session.main(["review", "--system", str(SYSTEM), "--vault", str(vault),
                         "--lesson", "docker/lesson-001", *a])


# ---- 1. review happy → exit 0, JSON committed+pass --------------------
def test_cli_review_happy(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["committed"] is True and out["pass"] is True
    assert out["command"] == "review"
    # end-to-end: validator thật trên vault đã commit
    rep = V.Report(); V.validate_full_core(SYSTEM, vault, rep, now=datetime.fromisoformat(AT))
    assert rep.ok()


# ---- 2. done happy → exit 0 -------------------------------------------
def test_cli_done_happy(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    code = session.main(["done", "--system", str(SYSTEM), "--vault", str(vault),
                         "--lesson", "docker/lesson-001", "--at", AT, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["committed"] is True and out["pass"] is True


# ---- 3. grade sai → exit 1, E-REVIEW-BADGRADE, file không đổi ----------
def test_cli_bad_grade(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    before = (vault / LS_REL).read_bytes()
    code = _rv(vault, "--item", "rv-001", "--grade", "5", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-REVIEW-BADGRADE"
    assert (vault / LS_REL).read_bytes() == before


# ---- 4. item lạ → exit 1, E-DRIVER, file không đổi --------------------
def test_cli_unknown_item(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    before = (vault / LS_REL).read_bytes()
    code = _rv(vault, "--item", "rv-999", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 1 and out["errors"][0]["error_code"] == "E-DRIVER"
    assert (vault / LS_REL).read_bytes() == before


# ---- 5. --at naive → exit 2, E-ARG ------------------------------------
def test_cli_naive_at(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", "2026-07-02T17:00:00", "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 2 and out["errors"][0]["error_code"] == "E-ARG"


# ---- 5b. forget cần --confirm: thiếu → exit 1 E-DRIVER, file còn nguyên
def test_cli_forget_requires_confirm(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    code = session.main(["forget", "--system", str(SYSTEM), "--vault", str(vault),
                         "--lesson", "docker/lesson-001", "--reason", "x", "--at", AT, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1 and out["errors"][0]["error_code"] == "E-DRIVER"
    assert (vault / LS_REL).exists()  # chưa xoá gì


def test_cli_forget_confirmed(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    code = session.main(["forget", "--system", str(SYSTEM), "--vault", str(vault),
                         "--lesson", "docker/lesson-001", "--reason", "làm lại",
                         "--confirm", "--at", AT, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["committed"] is True and out["pass"] is True
    assert not (vault / LS_REL.parent).exists()  # lesson dir đã bị prune


# ---- 5c. file non-UTF-8 → driver BÁO E-IO-ENCODING sạch (không crash), cả write lẫn read-only ----
_BAD = b"\xff\xfe khong phai utf-8 \x00\x81"


def test_cli_review_non_utf8_reports_io_encoding(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    (vault / LS_REL).write_bytes(_BAD)                    # lesson_state hỏng encoding
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-IO-ENCODING"


def test_cli_status_non_utf8_reports_io_encoding(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    (vault / LS_REL).write_bytes(_BAD)
    code = session.main(["status", "--system", str(SYSTEM), "--vault", str(vault), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-IO-ENCODING"


# ---- 6. subprocess thật: chạy như lệnh shell độc lập ------------------
def test_cli_real_subprocess(tmp_path):
    vault = _copy_vault(tmp_path)
    cmd = [sys.executable, str(ROOT / "validator" / "session.py"), "review",
           "--system", str(SYSTEM), "--vault", str(vault),
           "--lesson", "docker/lesson-001", "--item", "rv-001",
           "--grade", "2", "--at", AT, "--json"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    out = json.loads(r.stdout)
    assert out["committed"] is True and out["pass"] is True


# ---- ROBUSTNESS (pilot vòng 4): file on-disk hỏng → mã lỗi SẠCH, KHÔNG crash traceback ----
# RED-first: driver regen re-parse file lesson_state → nếu file bị sửa tay hỏng (schema/YAML/thiếu
# front-matter) thì ValidationError/YAMLError/IndexError THOÁT dạng stack trace thô (main() không bắt).
# Bản chất: tầng đọc-parse của driver thiếu biên lỗi (validator thì có). Fix: SchemaError ở _load_raw +
# _lesson_model_from_raw → main() báo E-SCHEMA/E-SCHEMA-YAML sạch (spec §10.4/§10.6/§19).
def test_cli_review_corrupt_schema_reports_clean(tmp_path, capsys):
    """mastery score ngoài 0..3 (sửa tay) → E-SCHEMA sạch, không traceback."""
    vault = _copy_vault(tmp_path)
    p = vault / LS_REL
    p.write_text(p.read_text(encoding="utf-8").replace("concept: {score: 0", "concept: {score: 99"),
                 encoding="utf-8")
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)   # parse được = KHÔNG crash traceback
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA", out
    assert out["committed"] is False


def test_cli_review_broken_yaml_reports_clean(tmp_path, capsys):
    """front-matter YAML hỏng (sửa tay) → E-SCHEMA-YAML sạch, không traceback."""
    vault = _copy_vault(tmp_path)
    p = vault / LS_REL
    p.write_text("---\nschema: lesson_state\nbad: [unclosed\n---\nbody\n", encoding="utf-8")
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA-YAML", out
    assert out["committed"] is False


def test_cli_review_missing_frontmatter_reports_clean(tmp_path, capsys):
    """file thiếu front-matter '---' (sửa tay) → E-SCHEMA sạch, không IndexError traceback."""
    vault = _copy_vault(tmp_path)
    p = vault / LS_REL
    p.write_text("# chỉ có body, không có front-matter\n", encoding="utf-8")
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA", out
    assert out["committed"] is False


# ---- ROBUSTNESS (pilot vòng 5): vault_state SAI KIỂU (YAML hợp lệ, kiểu sai) → E-SCHEMA sạch ----
# RED-first: lệnh đọc thao tác trên raw dict vault_state, giả định kiểu field (open_session.get,
# "/" in current_lesson) → sai kiểu gây AttributeError/TypeError THÔ (main không bắt). Bản chất:
# driver đọc vault_state không qua model. Fix: _load_vault_state validate qua M.VaultState → E-SCHEMA.
VS_REL = Path("vault_state.md")


def _corrupt_open_session_to_str(vault):
    p = vault / VS_REL
    t = p.read_text(encoding="utf-8")
    t = t.replace("open_session:\n  lesson_id: null\n  started_at: null\n  last_full_validate: null",
                  'open_session: "notadict"')
    p.write_text(t, encoding="utf-8")


def _corrupt_current_lesson_to_int(vault):
    p = vault / VS_REL
    t = p.read_text(encoding="utf-8").replace("current_lesson: docker/lesson-001", "current_lesson: 12345")
    p.write_text(t, encoding="utf-8")


def test_cli_status_vault_state_wrong_type_reports_clean(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    _corrupt_open_session_to_str(vault)   # open_session là chuỗi thay vì mapping
    code = session.main(["status", "--system", str(SYSTEM), "--vault", str(vault), "--json"])
    out = json.loads(capsys.readouterr().out)   # parse được = không crash traceback
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA", out


def test_cli_resume_vault_state_wrong_type_reports_clean(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    _corrupt_current_lesson_to_int(vault)   # current_lesson là int thay vì str
    code = session.main(["resume", "--system", str(SYSTEM), "--vault", str(vault), "--at", AT, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA", out


# ---- ROBUSTNESS (pilot vòng 6): topic_state/lesson_state authored-collection SAI KIỂU → E-SCHEMA sạch ----
# RED-first: driver iterate topic_state.lessons + lesson_state.review_items (raw) TRƯỚC regen/post-validate.
# Nếu chúng sai kiểu (YAML hợp lệ, không phải list-of-mapping) → AttributeError/KeyError thô. Fix:
# _load_topic_state (validate lessons qua LessonIndexEntry) + guard review_items + validate target lesson.
TS_REL = Path("topics") / "docker" / "topic_state.md"


def _corrupt_topic_lessons_to_str(vault):
    p = vault / TS_REL
    t = p.read_text(encoding="utf-8").replace(
        "lessons:\n  - id: docker/lesson-001\n    status: in_progress", 'lessons: "notalist"')
    p.write_text(t, encoding="utf-8")


def test_cli_done_topic_lessons_wrong_type_reports_clean(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    _corrupt_topic_lessons_to_str(vault)   # topic_state.lessons là chuỗi thay vì list
    code = session.main(["done", "--system", str(SYSTEM), "--vault", str(vault),
                         "--lesson", "docker/lesson-001", "--at", AT, "--json"])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA", out
    assert out["committed"] is False


def test_cli_review_topic_lessons_wrong_type_reports_clean(tmp_path, capsys):
    vault = _copy_vault(tmp_path)
    _corrupt_topic_lessons_to_str(vault)
    code = _rv(vault, "--item", "rv-001", "--grade", "2", "--at", AT, "--json")
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["errors"][0]["error_code"] == "E-SCHEMA", out
    assert out["committed"] is False
