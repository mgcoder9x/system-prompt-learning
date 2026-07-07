"""P08 tests — transaction engine (fault injection, spec 10.3/10.3a/b).

Cơ chế (begin/stage/commit/recover/OCC/retry) test bằng file .txt thuần để cô lập khỏi validator.
validate_staged + INV-11 test riêng.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import transaction as TX  # noqa: E402
import validate as V      # noqa: E402
import vault_io as VIO    # noqa: E402


def w(root: Path, rel: str, content: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def rd(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


# ---- cơ chế: happy path -------------------------------------------------
def test_happy_commit(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    w(tmp_path, "a.txt", "old")
    h = VIO.content_hash(tmp_path / "a.txt")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"new", expected_read_hash=h)])
    tx.stage()
    tx.occ_recheck()
    tx.commit()
    assert rd(tmp_path, "a.txt") == "new"
    assert not (tmp_path / ".tx" / tx.tx_id).exists()      # .tx đã dọn
    assert (tmp_path / "transaction_log.md").is_file()      # log materialize


def test_tx_dir_under_root_same_fs(tmp_path):
    """Cross-device guard: .tx phải NẰM TRONG root (cùng filesystem với đích)."""
    tx = TX.Transaction(tmp_path)
    assert tx.tx_dir.parent.name == TX.TX_DIRNAME
    assert str(tx.tx_dir).startswith(str(tmp_path))


# ---- cơ chế: fail validate → abort -------------------------------------
def test_fail_then_abort_leaves_real_file(tmp_path):
    w(tmp_path, "a.txt", "keep")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"staged-but-never-committed")])
    tx.stage()
    tx.abort()  # giả lập validate FAIL → abort trước 'committing'
    assert rd(tmp_path, "a.txt") == "keep"                 # file thật KHÔNG đổi
    assert tx.manifest["state"] == "aborted"


# ---- cơ chế: crash giữa commit → recover roll-forward ------------------
def test_crash_during_commit_then_recover(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    for n in ("a", "b", "c"):
        w(tmp_path, f"{n}.txt", f"{n}0")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"a1"), TX.Write("b.txt", b"b1"), TX.Write("c.txt", b"c1")])
    tx.stage()

    orig = TX._replace_with_retry
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:            # crash khi replace file thứ 2 (b.txt, thứ tự a,b,c)
            raise RuntimeError("boom: mô phỏng crash giữa committing")
        return orig(src, dst)

    monkeypatch.setattr(TX, "_replace_with_retry", flaky)
    with pytest.raises(RuntimeError):
        tx.commit()
    monkeypatch.setattr(TX, "_replace_with_retry", orig)   # khôi phục cho recover

    handled = TX.recover(tmp_path)
    assert tx.tx_id in handled
    assert (rd(tmp_path, "a.txt"), rd(tmp_path, "b.txt"), rd(tmp_path, "c.txt")) == ("a1", "b1", "c1")
    assert not (tmp_path / ".tx" / tx.tx_id).exists()


# ---- atomic manifest ----------------------------------------------------
def test_atomic_manifest_no_tmp_left(tmp_path):
    p = tmp_path / "m.json"
    TX.atomic_write_manifest(p, {"tx_id": "x", "state": "prepared"})
    assert not (tmp_path / "m.tmp").exists()
    assert json.loads(p.read_text(encoding="utf-8"))["state"] == "prepared"


def test_manifest_tmp_fallback_when_main_corrupt(tmp_path):
    p = tmp_path / "manifest.json"
    p.write_text("{ broken json ", encoding="utf-8")             # bản chính rách
    p.with_suffix(".tmp").write_text(json.dumps({"tx_id": "y", "state": "committing"}),
                                     encoding="utf-8")
    m = TX._read_manifest(p)
    assert m is not None and m["state"] == "committing"


# ---- OCC hai mốc --------------------------------------------------------
def test_stale_context_between_read_and_begin(tmp_path):
    w(tmp_path, "a.txt", "v1")
    stale = VIO.content_hash(tmp_path / "a.txt")
    w(tmp_path, "a.txt", "v2")                                    # người dùng sửa sau T-read
    tx = TX.Transaction(tmp_path, level="light")
    with pytest.raises(TX.TxError) as ei:
        tx.begin([TX.Write("a.txt", b"v3", expected_read_hash=stale)])
    assert ei.value.code == "E-STALE-CONTEXT"
    # begin thất bại TRƯỚC khi manifest bền vững → phải DỌN .tx/<id> dở (không để orphan backup rò rỉ)
    assert not tx.tx_dir.exists(), "begin lỗi phải dọn tx_dir dở (staged/backup chưa có manifest)"


def test_concurrent_edit_between_begin_and_commit(tmp_path):
    w(tmp_path, "a.txt", "v1")
    h = VIO.content_hash(tmp_path / "a.txt")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"v3", expected_read_hash=h)])
    tx.stage()
    w(tmp_path, "a.txt", "hand-edit")                            # sửa tay trong lúc tx chạy
    with pytest.raises(TX.TxError) as ei:
        tx.occ_recheck()
    assert ei.value.code == "E-CONCURRENT-EDIT"
    # spec §10.3: lệch OCC mốc-2 → ABORT (không để manifest kẹt 'prepared' → .tx treo mãi, rò rỉ)
    assert tx.manifest["state"] == "aborted"
    assert rd(tmp_path, "a.txt") == "hand-edit"                  # file thật GIỮ bản sửa tay (không ghi đè)


# ---- retry rename (cloud-lock) -----------------------------------------
def test_replace_retry_succeeds_after_4_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    src = tmp_path / "s"; src.write_text("x", encoding="utf-8")
    dst = tmp_path / "d"
    orig = os.replace
    calls = {"n": 0}

    def flaky(a, b):
        calls["n"] += 1
        if calls["n"] <= 4:
            raise PermissionError("WinError 32 giả lập cloud lock")
        return orig(a, b)

    monkeypatch.setattr(TX, "_os_replace", flaky)
    TX._replace_with_retry(src, dst)
    assert dst.read_text(encoding="utf-8") == "x" and calls["n"] == 5


def test_replace_retry_exhausts_to_tx_partial(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    src = tmp_path / "s"; src.write_text("x", encoding="utf-8")
    dst = tmp_path / "d"

    def always_fail(a, b):
        raise PermissionError("khoá mãi")

    monkeypatch.setattr(TX, "_os_replace", always_fail)
    with pytest.raises(TX.TxError) as ei:
        TX._replace_with_retry(src, dst)
    assert ei.value.code == "E-TX-PARTIAL"


# ---- multi-root ---------------------------------------------------------
def test_multiroot_missing_sibling_manifest(tmp_path):
    root = tmp_path / "vault"; root.mkdir()
    w(root, "a.txt", "A0")
    tx = TX.Transaction(root, level="light", sibling_roots=["_system"])
    tx.begin([TX.Write("a.txt", b"A1")])
    tx.stage()
    tx.manifest["state"] = "committing"; tx._save()              # giả lập dở dang
    with pytest.raises(TX.TxError) as ei:
        TX.recover(root, all_roots={"vault": root})              # thiếu manifest _system
    assert ei.value.code == "E-TX-PARTIAL"


# ---- INV-11 (E-REVIEW-LOST) --------------------------------------------
def test_review_lost_without_tombstone():
    rep = V.Report()
    V.check_review_not_lost({"rv-001": "in_review"}, {}, [], rep, "lesson")
    assert "E-REVIEW-LOST" in {e["error_code"] for e in rep.errors}


def test_review_lost_allowed_with_tombstone():
    rep = V.Report()
    V.check_review_not_lost({"rv-001": "need_redo"}, {}, ["rv-001"], rep)
    assert rep.ok()


def test_review_new_vanish_is_allowed():
    rep = V.Report()
    V.check_review_not_lost({"rv-001": "new"}, {}, [], rep)      # 'new' không được bảo vệ
    assert rep.ok()


LESSON_STATE_TEXT = """---
schema: lesson_state
schema_version: 1
lesson_id: docker/lesson-001
title: x
status: in_progress
created: 2026-06-30
updated: 2026-06-30
objective: x
mastery:
  concept: {score: 0, evidence: []}
  explain: {score: 0, evidence: []}
  apply: {score: 0, evidence: []}
  critique: {score: 0, evidence: []}
  teachback: {score: 0, evidence: []}
review_items:
  - id: rv-001
    prompt_ref: lesson.md#q1
    fsrs_config_version: 1
    created: 2026-06-30
    card: {state: Learning, step: 0, stability: null, difficulty: null, due_at_utc: "2026-06-30T03:00:00Z", due_date: 2026-06-30, last_reviewed_at_utc: null}
    log: []
    mastery_state: new
---
"""


def test_extract_review_states():
    assert V.extract_review_states(LESSON_STATE_TEXT) == {"rv-001": "new"}


# ---- validate_staged (overlay) -----------------------------------------
VAULT_STATE = """---
schema: vault_state
schema_version: 1
utc_offset: "+07:00"
day_cutoff_hour: 4
current_topic: docker
current_lesson: docker/lesson-001
---
"""
TOPIC_STATE = """---
schema: topic_state
schema_version: 1
topic_id: docker
title: Docker
current_lesson: docker/lesson-001
has_draft_knowledge: false
lessons:
  - id: docker/lesson-001
    status: in_progress
created: 2026-06-30
updated: 2026-06-30
review_schedule:
  generated_from_hash: "sha256:PENDING"
  items: []
assessment:
  generated_from_hash: "sha256:PENDING"
  concept_avg: 0.0
  explain_avg: 0.0
  apply_avg: 0.0
  critique_avg: 0.0
  teachback_avg: 0.0
---
"""
LESSON_MD = """# Lesson

## Mục tiêu
x

## Sessions
### S
#### Question q1
"?"
"""
L_STATE_REL = "topics/docker/lessons/lesson-001/lesson_state.md"
L_MD_REL = "topics/docker/lessons/lesson-001/lesson.md"


def build_min_vault(root: Path):
    w(root, "vault_state.md", VAULT_STATE)
    w(root, "topics/docker/topic_state.md", TOPIC_STATE)
    w(root, L_STATE_REL, LESSON_STATE_TEXT)
    w(root, L_MD_REL, LESSON_MD)


def test_validate_staged_light_pass(tmp_path):
    build_min_vault(tmp_path)
    tx = TX.Transaction(tmp_path, level="light")
    new_body = (LESSON_MD + "\n## Hỏi phụ\n- thêm\n").encode("utf-8")
    tx.begin([TX.Write(L_MD_REL, new_body)])
    tx.stage()
    rep = tx.validate_staged(ROOT, level="light")
    assert rep.ok(), rep.errors
    assert rd(tmp_path, L_MD_REL) == LESSON_MD             # file thật CHƯA đổi (mới staged)


def test_validate_staged_light_fail(tmp_path):
    build_min_vault(tmp_path)
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write(L_MD_REL, b"# broken\n\nkhong co heading bat buoc\n")])
    tx.stage()
    rep = tx.validate_staged(ROOT, level="light")
    assert not rep.ok()
    assert "E-LESSON-HEADING" in {e["error_code"] for e in rep.errors}


# ---- crash SAU replace-hết-file, TRƯỚC ghi log → recover finalize -------
def test_crash_after_commit_before_log_then_recover(tmp_path, monkeypatch):
    """Ca self-declared còn thiếu test: state=committed đã lưu, file đã replace,
    nhưng crash trước _materialize_log/cleanup. recover() phải finalize log/tombstone + dọn .tx."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    w(tmp_path, "a.txt", "old")
    h = VIO.content_hash(tmp_path / "a.txt")
    tx = TX.Transaction(tmp_path, level="light")
    tomb = TX.Tombstone(op="delete", scope="lesson", lesson_id="docker/lesson-001",
                        item_ids=["rv-001"], reason="test", at="2026-06-30T00:00:00Z",
                        confirmed_by_user=True)
    tx.begin([TX.Write("a.txt", b"new", expected_read_hash=h)], tombstones=[tomb])
    tx.stage()

    orig = TX._materialize_log

    def crash(root, manifest):
        raise RuntimeError("crash trước khi ghi log")

    monkeypatch.setattr(TX, "_materialize_log", crash)
    with pytest.raises(RuntimeError):
        tx.commit()

    # file thật đã đổi (replace xong), state=committed persisted, nhưng log CHƯA ghi & .tx còn
    assert rd(tmp_path, "a.txt") == "new"
    assert not (tmp_path / "transaction_log.md").exists()
    assert tx.tx_dir.exists()

    # recover phải bắt được ca 'committed' còn sót và finalize
    monkeypatch.setattr(TX, "_materialize_log", orig)
    handled = TX.recover(tmp_path)
    assert tx.tx_id in handled
    log = (tmp_path / "transaction_log.md").read_text(encoding="utf-8")
    assert "tombstone" in log and "rv-001" in log      # tombstone bền vững → materialize được
    assert not tx.tx_dir.exists()                        # đã cleanup


# ---- KHOÁ an-toàn (pilot vòng 7): ranh giới roll-forward + chống clobber khi recover ----
# Hai thuộc-tính-an-toàn-dữ-liệu cốt lõi CHƯA có test canh. Khoá lại (regression-lock) — nếu refactor
# phá, phải ĐỎ ngay.
def test_prepared_crash_not_recovered_vault_stays_old(tmp_path):
    """RANH GIỚI all-or-nothing: transaction crash ở 'prepared' (CHƯA tới quyết-định-commit) → recovery
    KHÔNG roll-forward (chỉ scan committing/interrupted/committed). Vault GIỮ bản CŨ (nothing).
    Nếu recovery lỡ commit tx 'prepared' (chưa validate/chưa occ-recheck-2) = thảm hoạ dữ liệu → test này canh."""
    w(tmp_path, "a.txt", "old")
    h = VIO.content_hash(tmp_path / "a.txt")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"new", expected_read_hash=h)])
    tx.stage()
    assert tx.manifest["state"] == "prepared"          # chưa gọi commit() → chưa 'committing'
    handled = TX.recover(tmp_path)
    assert handled == []                                # recovery BỎ QUA tx chưa-quyết-commit
    assert rd(tmp_path, "a.txt") == "old"               # vault GIỮ bản cũ (all-or-nothing: nothing)
    assert (tmp_path / ".tx" / tx.tx_id).exists()       # .tx orphan còn (recovery không đụng)


def test_recover_refuses_when_target_externally_modified(tmp_path, monkeypatch):
    """CHỐNG CLOBBER: trong cửa sổ crash (state=committing), target bị sửa-ngoài → hash LẠ (không phải
    staged/before/backup). recover() phải raise E-TX-PARTIAL (cần xử lý tay), KHÔNG ghi đè bản sửa tay."""
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    w(tmp_path, "a.txt", "old")
    h = VIO.content_hash(tmp_path / "a.txt")
    tx = TX.Transaction(tmp_path, level="light")
    tx.begin([TX.Write("a.txt", b"new", expected_read_hash=h)])
    tx.stage()
    tx.manifest["state"] = "committing"; tx._save()     # mô phỏng crash GIỮA commit
    w(tmp_path, "a.txt", "hand-edit-trong-cua-so-crash")  # target bị sửa ngoài → hash lạ
    with pytest.raises(TX.TxError) as ei:
        TX.recover(tmp_path)
    assert ei.value.code == "E-TX-PARTIAL"              # recovery TỪ CHỐI, không clobber
    assert rd(tmp_path, "a.txt") == "hand-edit-trong-cua-so-crash"  # bản sửa tay GIỮ nguyên
