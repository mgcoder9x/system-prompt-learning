"""P03 — Pydantic schema models (strict). Đây là 'chân lý schema' (spec mục 19).

v2.6/F-A: Card.state ∈ {Learning,Review,Relearning} (không có New).
Ràng buộc "đã-review-chưa" ở ReviewItem theo `log` rỗng, KHÔNG theo state.
strict=True + Literal: bắt lỗi kiểu/enum, KHÔNG âm thầm ép ("2"↛2, 2.0↛2, "done"↛enum).
(Dùng Literal thay Enum vì strict mode nhận string literal trực tiếp từ YAML.)
"""
from __future__ import annotations

import re
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

LessonStatus = Literal["not_started", "in_progress", "learned", "needs_review"]
CardStateT = Literal["Learning", "Review", "Relearning"]
MasteryStateT = Literal["new", "in_review", "need_redo", "mastered"]
ExportPolicyT = Literal["private_full", "shareable_clean", "template_only"]
DatePolicyT = Literal["local_date"]  # spec §5.4: giá trị DUY NHẤT — 'hôm nay' theo utc_offset (không UTC trôi)
SourceKindT = Literal["doc", "link", "repo", "book", "note", "question"]
SourceStatusT = Literal["raw", "processing", "confirmed", "rejected"]
SourceTrustT = Literal["unknown", "low", "medium", "high"]

AXES = ("concept", "explain", "apply", "critique", "teachback")

_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class _Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", populate_by_name=True)


# ---- FSRS card + log ----------------------------------------------------
class Card(_Strict):
    state: CardStateT
    # step: Optional vì py-fsrs đặt step=None ở state Review (step chỉ có nghĩa trong
    # Learning/Relearning). Spec §29 (bảng vá v2.5→v2.6, dòng 1): step ràng buộc theo state,
    # Optional. Tính đúng đắn state↔step do replay INV-08 (cards_equal so step) đảm bảo.
    step: Optional[int] = None
    stability: Optional[float] = None
    difficulty: Optional[float] = None
    due_at_utc: str
    due_date: date
    last_reviewed_at_utc: Optional[str] = None

    @field_validator("due_at_utc", "last_reviewed_at_utc")
    @classmethod
    def _utc_fmt(cls, v):
        if v is not None and not _UTC_RE.match(v):
            raise ValueError(f"datetime UTC canonical sai định dạng: {v!r}")
        return v


class LogEvent(_Strict):
    reviewed_at: str  # ISO offset địa phương, precision giây
    rating: int = Field(ge=1, le=4)


# ---- mastery / evidence -------------------------------------------------
class MasteryAxis(_Strict):
    score: int = Field(ge=0, le=3)
    evidence: list[str] = []


class Mastery(_Strict):
    concept: MasteryAxis
    explain: MasteryAxis
    apply: MasteryAxis
    critique: MasteryAxis
    teachback: MasteryAxis


class OpenGap(_Strict):
    id: str
    desc: str
    detected: date

    @field_validator("id")
    @classmethod
    def _gid(cls, v):
        if not re.match(r"^gap-\S+$", v):
            raise ValueError(f"gap id sai pattern: {v!r}")
        return v


# ---- review item --------------------------------------------------------
class ReviewItem(_Strict):
    id: str
    prompt_ref: str
    fsrs_config_version: int
    created: date
    card: Card
    log: list[LogEvent] = []
    mastery_state: MasteryStateT

    @field_validator("id")
    @classmethod
    def _rid(cls, v):
        if not re.match(r"^rv-\S+$", v):
            raise ValueError(f"review id sai pattern: {v!r}")
        return v

    @model_validator(mode="after")
    def _check_log_vs_card(self):
        empty = len(self.log) == 0
        c = self.card
        if empty:
            if c.stability is not None or c.difficulty is not None or c.last_reviewed_at_utc is not None:
                raise ValueError("item chưa review (log rỗng) phải có stability/difficulty/last_reviewed_at_utc = null")
            if self.mastery_state != "new":
                raise ValueError("log rỗng ⇒ mastery_state phải 'new'")
        else:
            if c.stability is None or c.difficulty is None:
                raise ValueError("item đã review (log không rỗng) phải có stability/difficulty")
            if self.mastery_state == "new":
                raise ValueError("log không rỗng ⇒ mastery_state không được 'new'")
        return self


# ---- lesson_state -------------------------------------------------------
class LessonState(_Strict):
    schema_name: str = Field(alias="schema")
    schema_version: int
    lesson_id: str
    title: str
    status: LessonStatus
    created: date
    updated: date
    objective: str
    prerequisites: list[str] = []
    sections_done: list[str] = []
    sections_pending: list[str] = []
    mastery: Mastery
    open_gaps: list[OpenGap] = []
    review_items: list[ReviewItem] = []
    next_action: str = ""
    last_session: Optional[date] = None

    @field_validator("schema_name")
    @classmethod
    def _schema(cls, v):
        if v != "lesson_state":
            raise ValueError(f"schema phải 'lesson_state', gặp {v!r}")
        return v

    @model_validator(mode="after")
    def _invariants(self):
        if self.updated < self.created:
            raise ValueError("updated < created (INV-05)")
        return self


# ---- vault_state --------------------------------------------------------
class OpenSession(_Strict):
    lesson_id: Optional[str] = None
    started_at: Optional[str] = None
    last_full_validate: Optional[str] = None


class VaultState(_Strict):
    schema_name: str = Field(alias="schema")
    schema_version: int
    utc_offset: str
    date_policy: DatePolicyT = "local_date"
    day_cutoff_hour: int = Field(ge=0, le=23, default=4)
    current_topic: Optional[str] = None
    current_lesson: Optional[str] = None
    export_policy: ExportPolicyT = "private_full"
    open_session: OpenSession = OpenSession()

    @field_validator("schema_name")
    @classmethod
    def _schema(cls, v):
        if v != "vault_state":
            raise ValueError(f"schema phải 'vault_state', gặp {v!r}")
        return v

    @field_validator("utc_offset")
    @classmethod
    def _off(cls, v):
        if not re.match(r"^[+-]\d{2}:\d{2}$", v):
            raise ValueError(f"utc_offset sai định dạng: {v!r}")
        return v


# ---- topic_state views (spec 5.2, 4) -----------------------------------
class ScheduleItem(_Strict):
    lesson_id: str
    item_id: str
    due_date: date
    mastery_state: MasteryStateT


class ReviewScheduleView(_Strict):
    generated_from_hash: str
    items: list[ScheduleItem] = []


class AssessmentView(_Strict):
    generated_from_hash: str
    concept_avg: float
    explain_avg: float
    apply_avg: float
    critique_avg: float
    teachback_avg: float


class LessonIndexEntry(_Strict):
    id: str
    status: LessonStatus


class TopicState(_Strict):
    schema_name: str = Field(alias="schema")
    schema_version: int
    topic_id: str
    title: str
    current_lesson: Optional[str] = None
    has_draft_knowledge: bool = False
    lessons: list[LessonIndexEntry] = []
    created: date
    updated: date
    review_schedule: ReviewScheduleView
    assessment: AssessmentView

    @field_validator("schema_name")
    @classmethod
    def _schema(cls, v):
        if v != "topic_state":
            raise ValueError(f"schema phải 'topic_state', gặp {v!r}")
        return v

    @model_validator(mode="after")
    def _invariants(self):
        if self.updated < self.created:
            raise ValueError("updated < created (INV-05)")
        ids = [e.id for e in self.lessons]
        if len(ids) != len(set(ids)):
            raise ValueError("lesson id trùng trong topic index (INV-04)")
        return self


# ---- sources.md (spec 5.3) ---------------------------------------------
class SourceAnchor(_Strict):
    """Neo trích dẫn trong một nguồn (spec 5.3). Claim B trỏ 'src-XXX#<id>'."""
    id: str
    locator: str = ""
    quote: str
    summary: str = ""
    content_hash: Optional[str] = None


class Source(_Strict):
    id: str
    kind: SourceKindT
    ref: str
    status: SourceStatusT
    trust: SourceTrustT = "unknown"
    scope: str = ""
    added: Optional[date] = None
    anchors: list[SourceAnchor] = []

    @field_validator("id")
    @classmethod
    def _sid(cls, v):
        if not re.match(r"^src-\S+$", v):
            raise ValueError(f"source id sai pattern: {v!r}")
        return v


class Sources(_Strict):
    schema_name: str = Field(alias="schema")
    schema_version: int
    topic_id: str
    sources: list[Source] = []

    @field_validator("schema_name")
    @classmethod
    def _schema(cls, v):
        if v != "sources":
            raise ValueError(f"schema phải 'sources', gặp {v!r}")
        return v

    @model_validator(mode="after")
    def _invariants(self):
        ids = [s.id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source id trùng (INV-04)")
        return self


# ---- curriculum (tính năng curriculum-driven-learning, CR-0007) ---------
CurriculumStatusT = Literal["not_started", "in_progress", "done"]


class CurriculumPoint(_Strict):
    """Một điểm cần học trong giáo trình. Ràng buộc NGỮ NGHĨA (id duy nhất, order hoán vị 1..N,
    objective không rỗng, lesson_id/source_refs trỏ thật) do Curriculum_Validator (validate.py)
    kiểm với mã lỗi RIÊNG — KHÔNG nhét vào model để giữ mã lỗi phân biệt (khác kiểu TopicState)."""
    id: str
    order: int = Field(ge=1)
    objective: str
    status: CurriculumStatusT
    lesson_id: Optional[str] = None
    source_refs: list[str] = []

    @field_validator("id")
    @classmethod
    def _cpid(cls, v):
        if not re.match(r"^cp-\S+$", v):
            raise ValueError(f"curriculum point id sai pattern: {v!r}")
        return v


class Curriculum(_Strict):
    schema_name: str = Field(alias="schema")
    schema_version: int
    topic_id: str
    current_point: str
    created: date
    updated: date
    teachable: bool = False
    points: list[CurriculumPoint] = []

    @field_validator("schema_name")
    @classmethod
    def _schema(cls, v):
        if v != "curriculum":
            raise ValueError(f"schema phải 'curriculum', gặp {v!r}")
        return v

    @model_validator(mode="after")
    def _invariants(self):
        if self.updated < self.created:
            raise ValueError("updated < created (INV-05)")
        return self


# ---- exam_results (bản ghi chấm bài thực hành, CR-0007) -----------------
class ExamResult(_Strict):
    submission_id: str
    ref: str
    target: str
    graded_at: date
    verdict: str

    @field_validator("submission_id")
    @classmethod
    def _exid(cls, v):
        if not re.match(r"^ex-\S+$", v):
            raise ValueError(f"exam submission id sai pattern: {v!r}")
        return v


class ExamResults(_Strict):
    schema_name: str = Field(alias="schema")
    schema_version: int
    topic_id: str
    results: list[ExamResult] = []

    @field_validator("schema_name")
    @classmethod
    def _schema(cls, v):
        if v != "exam_results":
            raise ValueError(f"schema phải 'exam_results', gặp {v!r}")
        return v

    @model_validator(mode="after")
    def _invariants(self):
        ids = [r.submission_id for r in self.results]
        if len(ids) != len(set(ids)):
            raise ValueError("exam submission id trùng (INV-04)")
        return self
