"""P10 tests — session driver /review chạy transaction-FULL thật (spec 11A, 10.3, 14).

Nguyên tắc test:
- Dùng VAULT DEMO thật (learning_vault) copy sang tmp → mọi bất biến GĐ1 áp dụng.
- Sau commit PHẢI validate_full_core(vault) PASS (validator là chân lý, không tự nhận PASS).
- Fault-injection: ép driver ghi card SAI → validator ABORT → file thật không đổi.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session          # noqa: E402
import validate as V    # noqa: E402
import fsrs_adapter as FA  # noqa: E402
import transaction as TX  # noqa: E402
import vault_io as VIO    # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
TZ7 = timezone(timedelta(hours=7))
REVIEWED_AT = datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc)  # 17:00 +07 → local 2026-07-02

LS_REL = Path("topics") / "docker" / "lessons" / "lesson-001" / "lesson_state.md"
TS_REL = Path("topics") / "docker" / "topic_state.md"


def _copy_vault(tmp_path) -> Path:
    dst = tmp_path / "learning_vault"
    shutil.copytree(VAULT_SRC, dst)
    return dst


def _raw(vault: Path, rel: Path) -> dict:
    raw, _ = session._load_raw(vault / rel)
    return raw


def _validate_ok(vault: Path):
    rep = V.Report()
    V.validate_full_core(SYSTEM, vault, rep, now=REVIEWED_AT)
    return rep


# ---- 1. review lần đầu (grade Good) commit + validate PASS -------------
def test_first_review_commits_and_validates(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)

    committed, rep = session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                                        grade=2, reviewed_at=REVIEWED_AT)
    assert committed is True, rep.errors
    assert rep.ok()

    ls = _raw(vault, LS_REL)
    item = ls["review_items"][0]
    assert len(item["log"]) == 1
    assert item["mastery_state"] != "new"
    assert item["card"]["stability"] is not None
    assert item["card"]["last_reviewed_at_utc"] is not None

    ts = _raw(vault, TS_REL)
    sched_item = ts["review_schedule"]["items"][0]
    assert sched_item["mastery_state"] == item["mastery_state"]

    # end-to-end: validator thật trên vault đã commit
    assert _validate_ok(vault).ok()


# ---- 2. tất định: 2 vault song song → bytes GIỐNG HỆT ------------------
def test_determinism_byte_identical(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    v1 = _copy_vault(tmp_path / "a")
    v2 = _copy_vault(tmp_path / "b")

    session.cmd_review(v1, SYSTEM, "docker/lesson-001", "rv-001", grade=2, reviewed_at=REVIEWED_AT)
    session.cmd_review(v2, SYSTEM, "docker/lesson-001", "rv-001", grade=2, reviewed_at=REVIEWED_AT)

    assert (v1 / LS_REL).read_bytes() == (v2 / LS_REL).read_bytes()
    assert (v1 / TS_REL).read_bytes() == (v2 / TS_REL).read_bytes()


# ---- 3. validator là LƯỚI AN TOÀN: card sai → ABORT, file không đổi ----
def test_validator_safety_net_bad_card_aborts(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    before_ls = (vault / LS_REL).read_bytes()
    before_ts = (vault / TS_REL).read_bytes()

    orig_review = FA.review

    def bad_review(*a, **k):
        ev, card = orig_review(*a, **k)
        card = dict(card)
        card["stability"] = (card["stability"] or 0.0) + 100.0  # lệch chủ ý
        return ev, card

    monkeypatch.setattr(FA, "review", bad_review)

    committed, rep = session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                                        grade=2, reviewed_at=REVIEWED_AT)
    assert committed is False
    assert any(e["error_code"] == "E-REVIEW-MISCALC" for e in rep.errors), rep.errors
    # file thật KHÔNG đổi
    assert (vault / LS_REL).read_bytes() == before_ls
    assert (vault / TS_REL).read_bytes() == before_ts


# ---- 4. grade sai (5) → EReviewBadGrade, không transaction -------------
def test_bad_grade_raises_no_transaction(tmp_path):
    vault = _copy_vault(tmp_path)
    before = (vault / LS_REL).read_bytes()
    with pytest.raises(FA.EReviewBadGrade):
        session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                           grade=5, reviewed_at=REVIEWED_AT)
    assert (vault / LS_REL).read_bytes() == before
    assert not (vault / ".tx").exists()


# ---- 5. OCC: file đổi giữa đọc-context và begin → E-STALE-CONTEXT ------
def test_occ_stale_context(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)

    orig_begin = TX.Transaction.begin

    def begin_after_tamper(self, writes, tombstones=None):
        # mô phỏng sửa tay file đích SAU khi driver đã chụp expected_read_hash
        (self.root / writes[0].target).write_text("tampered\n", encoding="utf-8")
        return orig_begin(self, writes, tombstones)

    monkeypatch.setattr(TX.Transaction, "begin", begin_after_tamper)

    with pytest.raises(TX.TxError) as ei:
        session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                           grade=2, reviewed_at=REVIEWED_AT)
    assert ei.value.code == "E-STALE-CONTEXT"


# ---- 6. item không tồn tại → SessionError ------------------------------
def test_unknown_item_raises(tmp_path):
    vault = _copy_vault(tmp_path)
    with pytest.raises(session.SessionError):
        session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-999",
                           grade=2, reviewed_at=REVIEWED_AT)


# ---- 7. INV-05: updated >= created sau commit --------------------------
def test_inv05_updated_ge_created(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)
    session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001", grade=2, reviewed_at=REVIEWED_AT)
    ls = _raw(vault, LS_REL)
    assert ls["updated"] >= ls["created"]


# ---- 1b. review grade Easy → card vào state Review (step=None) ----------
# RED-first (pilot vòng 3): grade 3 (Easy) đẩy Learning step0 → Review. py-fsrs đặt card.step=None
# ở state Review (step chỉ có nghĩa trong Learning/Relearning). Model Card.step khai `int` (bắt buộc)
# → _regen_topic_views re-parse LessonState CRASH ValidationError. Spec §29 (bảng vá v2.5→v2.6, dòng 1):
# step PHẢI Optional, ràng buộc theo state. Fix gốc: Card.step -> Optional[int].
def test_review_easy_enters_review_state_step_none(tmp_path, monkeypatch):
    monkeypatch.setattr(TX, "_sleep", lambda s: None)
    vault = _copy_vault(tmp_path)

    committed, rep = session.cmd_review(vault, SYSTEM, "docker/lesson-001", "rv-001",
                                        grade=3, reviewed_at=REVIEWED_AT)
    assert committed is True, rep.errors
    assert rep.ok()

    ls = _raw(vault, LS_REL)
    card = ls["review_items"][0]["card"]
    assert card["state"] == "Review", card
    assert card["step"] is None, "py-fsrs đặt step=None khi vào Review"

    # validator FULL độc lập PHẢI PASS (card step=None hợp lệ + replay INV-08 khớp)
    rep2 = _validate_ok(vault)
    assert rep2.ok(), rep2.errors
