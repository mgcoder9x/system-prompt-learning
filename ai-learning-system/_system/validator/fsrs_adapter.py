"""P01 — FSRS adapter (fsrs 6.3.1). Thuần hàm, không I/O file (trừ load_config).

Quyết định theo SPIKE (v2.6):
- F-A: py-fsrs KHÔNG có State.New. Thẻ mới = State.Learning, stability/difficulty=None, last_review=None.
       "Chưa review" nhận biết bằng log rỗng (last_reviewed_at_utc is None).
- F-B: due tính nội bộ review_card từ float transcendental → KHÔNG bit-identical cross-CPU.
       due_date (ngày local) là trục so khớp chuẩn cho Review; Learning/Relearning dùng bước cố định
       (deterministic) nên due_at_utc so exact được. due_at_utc KHÔNG vào hash view.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
import math

import yaml
from fsrs import Scheduler, Card, Rating, State

# ---- config -------------------------------------------------------------
MAP_GRADE_TO_RATING = {0: Rating.Again, 1: Rating.Hard, 2: Rating.Good, 3: Rating.Easy}


class EReviewBadGrade(ValueError):
    pass


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_scheduler(cfg: dict) -> Scheduler:
    return Scheduler(
        parameters=tuple(cfg["parameters"]),
        desired_retention=cfg["desired_retention"],
        learning_steps=tuple(timedelta(seconds=s) for s in cfg["learning_steps_seconds"]),
        relearning_steps=tuple(timedelta(seconds=s) for s in cfg["relearning_steps_seconds"]),
        maximum_interval=cfg["maximum_interval_days"],
        enable_fuzzing=False,  # BẮT BUỘC — bỏ qua giá trị cfg để chống tái lập lỗi
    )


# ---- datetime helpers ---------------------------------------------------
def _parse_offset(utc_offset: str) -> timezone:
    sign = 1 if utc_offset[0] == "+" else -1
    hh, mm = utc_offset[1:].split(":")
    return timezone(sign * timedelta(hours=int(hh), minutes=int(mm)))


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(timezone.utc).replace(microsecond=0)


def due_at_utc_str(dt: datetime) -> str:
    return to_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def due_date_local(dt: datetime, utc_offset: str) -> date:
    return dt.astimezone(_parse_offset(utc_offset)).date()


def canonical_reviewed_at(dt: datetime, utc_offset: str) -> str:
    """Chuẩn hoá log event: offset địa phương, precision GIÂY (spec 8.5).
    Đảm bảo audit text khớp bất kể caller đưa UTC hay có microsecond."""
    if dt.tzinfo is None:
        raise ValueError("reviewed_at must be timezone-aware")
    return dt.astimezone(_parse_offset(utc_offset)).replace(microsecond=0).isoformat()


def _round(v, nd: int):
    return None if v is None else round(v, nd)


# ---- card <-> storage dict ---------------------------------------------
def card_to_dict(card: Card, utc_offset: str, round_decimals: int = 4) -> dict:
    return {
        "state": card.state.name,  # Learning|Review|Relearning
        "step": card.step,
        "stability": _round(card.stability, round_decimals),
        "difficulty": _round(card.difficulty, round_decimals),
        "due_at_utc": due_at_utc_str(card.due),
        "due_date": due_date_local(card.due, utc_offset).isoformat(),
        "last_reviewed_at_utc": None if card.last_review is None else due_at_utc_str(card.last_review),
    }


# ---- core ops -----------------------------------------------------------
def new_item_card(created_at: datetime, utc_offset: str, round_decimals: int = 4) -> dict:
    """Thẻ chưa review: State.Learning, stability/difficulty None, due = created."""
    c = Card(state=State.Learning, step=0, due=to_utc(created_at))
    d = card_to_dict(c, utc_offset, round_decimals)
    d["last_reviewed_at_utc"] = None
    return d


def replay(created_at: datetime, log_events: list[dict], cfg: dict, utc_offset: str) -> dict:
    """Replay từ thẻ mới (created) áp tuần tự log → card dict. Nguồn của INV-08.

    log_events: [{"reviewed_at": iso_str_with_offset, "rating": 1..4}]
    LƯU Ý: import từ initial_card (thẻ seed trạng thái khác) — DEFERRED (chưa hỗ trợ ở GĐ1);
    hiện mọi item luôn khởi tạo từ thẻ mới tại `created_at`. P11/cache KHÔNG được giả định initial_card tồn tại.
    """
    sched = build_scheduler(cfg)
    nd = cfg["serialization"]["round_decimals"]
    card = Card(state=State.Learning, step=0, due=to_utc(created_at))
    for ev in log_events:
        reviewed = datetime.fromisoformat(ev["reviewed_at"])
        rating = Rating(ev["rating"])
        card, _ = sched.review_card(card, rating, to_utc(reviewed))
    return card_to_dict(card, utc_offset, nd)


def review(created_at: datetime, log_events: list[dict], grade: int,
           reviewed_at: datetime, cfg: dict, utc_offset: str) -> tuple[dict, dict]:
    """Chấm 1 lượt: trả (log_event_mới, card_dict_mới). grade 0..3.
    log event được canonicalize (offset địa phương, giây) để audit text ổn định."""
    if grade not in MAP_GRADE_TO_RATING:
        raise EReviewBadGrade(f"grade {grade} ngoài 0..3")
    new_event = {
        "reviewed_at": canonical_reviewed_at(reviewed_at, utc_offset),
        "rating": MAP_GRADE_TO_RATING[grade].value,
    }
    new_log = log_events + [new_event]
    card = replay(created_at, new_log, cfg, utc_offset)
    return new_event, card


def derive_mastery(card: dict, log: list[dict], cfg: dict) -> str:
    """F-A: 'new' = log rỗng (không dùng State.New vì py-fsrs không có)."""
    if not log:
        return "new"
    last_rating = log[-1]["rating"]
    if last_rating == Rating.Again.value or card["state"] == "Relearning":
        return "need_redo"
    if card["state"] == "Review" and (card["stability"] or 0) >= cfg["mastered_stability_days"]:
        return "mastered"
    return "in_review"


def cards_equal(a: dict, b: dict, abs_tol: float = 1e-4) -> bool:
    """So khớp replay (INV-08).
    - stability/difficulty: math.isclose(abs_tol) (chịu float drift).
    - due_date: exact (trục chuẩn cho Review, F-B).
    - due_at_utc: exact CHỈ khi Learning/Relearning (bước cố định, deterministic);
      ở Review bỏ qua due_at_utc (chỉ tin due_date).
    """
    def _close(x, y):
        if x is None and y is None:
            return True
        if x is None or y is None:
            return False
        return math.isclose(x, y, abs_tol=abs_tol)

    if a["state"] != b["state"] or a["step"] != b["step"]:
        return False
    if not _close(a["stability"], b["stability"]) or not _close(a["difficulty"], b["difficulty"]):
        return False
    if a["last_reviewed_at_utc"] != b["last_reviewed_at_utc"]:
        return False  # timeline audit phải khớp (deterministic từ log)
    if a["due_date"] != b["due_date"]:
        return False
    if a["state"] in ("Learning", "Relearning") and a["due_at_utc"] != b["due_at_utc"]:
        return False
    return True
