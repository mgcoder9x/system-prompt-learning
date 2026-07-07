"""P10 driver — Task 5.3 / CR-0010 (R8): cmd_curriculum_insert — chèn Curriculum_Point giữa chừng.

Cờ `/curriculum --insert-at <pos> --point <json>`. Chèn tại pos (1..N+1): point mới order=pos, các point
order>=pos dịch +1 (giữ hoán vị 1..N+1 → E-CURR-ORDER); id mới = cp-{max_suffix+1} (duy nhất, ổn định);
current_point (tham chiếu id) + status point cũ GIỮ NGUYÊN (R8.3); vị trí xấu / dup / curriculum thiếu →
từ chối, không đổi (R8.7). transaction-FULL (validator gate E-CURR-*, rollback nếu sai — R8.5). RED-first.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S      # noqa: E402
import validate as V     # noqa: E402
import transaction as TX  # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 6, 3, 0, tzinfo=timezone.utc)
POINTS = json.dumps([{"objective": "Container là gì"}, {"objective": "Image và Dockerfile"}])
CUR_REL = Path("topics") / "docker" / "curriculum.md"


def _fresh(tmp_path):
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)
    c, rep = S.cmd_curriculum(v, SYSTEM, "docker", POINTS, AT)
    assert c, rep.errors
    return v


def _cur(v):
    return S._load_raw(v / CUR_REL)[0]


def _full_errors(v):
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, v, rep, now=AT)
    return [e["error_code"] for e in rep.errors]


def _by_id(cur, pid):
    return next(p for p in cur["points"] if p["id"] == pid)


def test_insert_middle_renumbers_keeps_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    c, rep = S.cmd_curriculum_insert(v, SYSTEM, "docker", 2,
                                     json.dumps({"objective": "Volume và mount"}), AT)
    assert c, rep.errors
    cur = _cur(v)
    assert len(cur["points"]) == 3
    new = _by_id(cur, "cp-003")                 # id = max_suffix+1 (KHÔNG tái dùng order)
    assert new["order"] == 2 and new["status"] == "not_started"
    assert _by_id(cur, "cp-001")["order"] == 1  # trước vị trí chèn: giữ nguyên
    assert _by_id(cur, "cp-002")["order"] == 3  # từ vị trí chèn: dịch +1
    assert cur["current_point"] == "cp-001"     # con trỏ giữ nguyên (R8.3)
    assert _full_errors(v) == []                # hoán vị order hợp lệ, FULL PASS


def test_insert_at_end(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    c, rep = S.cmd_curriculum_insert(v, SYSTEM, "docker", 3,
                                     json.dumps({"objective": "Networking"}), AT)
    assert c, rep.errors
    cur = _cur(v)
    assert _by_id(cur, "cp-003")["order"] == 3
    assert _by_id(cur, "cp-001")["order"] == 1 and _by_id(cur, "cp-002")["order"] == 2
    assert _full_errors(v) == []


def test_insert_at_front_shifts_all(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    c, rep = S.cmd_curriculum_insert(v, SYSTEM, "docker", 1,
                                     json.dumps({"objective": "Vì sao cần container"}), AT)
    assert c, rep.errors
    cur = _cur(v)
    assert _by_id(cur, "cp-003")["order"] == 1
    assert _by_id(cur, "cp-001")["order"] == 2 and _by_id(cur, "cp-002")["order"] == 3
    assert _full_errors(v) == []


def test_insert_keeps_done_status_and_pointer(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    # mô phỏng tiến độ: cp-001 done, current_point=cp-002
    cur = _cur(v)
    body = S._load_raw(v / CUR_REL)[1]
    _by_id(cur, "cp-001")["status"] = "done"
    cur["current_point"] = "cp-002"
    (v / CUR_REL).write_bytes(S._dump_state(cur, body))
    c, rep = S.cmd_curriculum_insert(v, SYSTEM, "docker", 2,
                                     json.dumps({"objective": "Chen giua"}), AT)
    assert c, rep.errors
    cur = _cur(v)
    assert _by_id(cur, "cp-001")["status"] == "done"   # tiến độ giữ nguyên (R8.3)
    assert cur["current_point"] == "cp-002"            # con trỏ giữ nguyên


def test_insert_unique_id_second_time(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v = _fresh(tmp_path)
    S.cmd_curriculum_insert(v, SYSTEM, "docker", 2, json.dumps({"objective": "A"}), AT)  # → cp-003
    c, rep = S.cmd_curriculum_insert(v, SYSTEM, "docker", 2, json.dumps({"objective": "B"}), AT)
    assert c, rep.errors
    ids = {p["id"] for p in _cur(v)["points"]}
    assert ids == {"cp-001", "cp-002", "cp-003", "cp-004"}   # cp-004 duy nhất
    assert _full_errors(v) == []


def test_insert_invalid_position_rejects(tmp_path):
    v = _fresh(tmp_path)
    before = (v / CUR_REL).read_bytes()
    for bad in (0, -1, 4):   # N=2 → hợp lệ 1..3; 4 và <=0 xấu
        with pytest.raises(S.SessionError):
            S.cmd_curriculum_insert(v, SYSTEM, "docker", bad, json.dumps({"objective": "x"}), AT)
    assert (v / CUR_REL).read_bytes() == before, "curriculum không được đổi khi vị trí xấu (R8.7)"


def test_insert_empty_objective_rejects(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_curriculum_insert(v, SYSTEM, "docker", 2, json.dumps({"objective": "   "}), AT)


def test_insert_requires_curriculum(tmp_path):
    v = tmp_path / "vault"
    shutil.copytree(VAULT_SRC, v)   # chưa có curriculum
    with pytest.raises(S.SessionError):
        S.cmd_curriculum_insert(v, SYSTEM, "docker", 1, json.dumps({"objective": "x"}), AT)


def test_insert_backend_exists():
    assert hasattr(S, "cmd_curriculum_insert")
