"""P09 — Sinh view tất định từ nguồn sự thật (spec mục 4 + 7).

Nguồn nuôi view = danh sách lesson_state của topic. View KHÔNG tự tham chiếu vòng:
miền băm loại tuyệt đối các field view (generated_from_hash/review_schedule/assessment).

- build_review_schedule: miền băm 4 field {lesson_id,item_id,due_date,mastery_state}
  theo thứ tự (lesson_id asc, rv.id asc); items xuất ra sắp (due_date, lesson_id, item_id).
  v2.6/F-B: due_at_utc KHÔNG vào hash (không bit-identical cross-CPU).
- build_assessment: chỉ lesson status ∈ {learned, needs_review}; miền băm {lesson_id,status,mastery{trục:score}};
  avg 5 trục làm tròn 1 chữ số. avg là float → CHỈ ở output view, KHÔNG vào hash (hash chỉ chứa int score).
"""
from __future__ import annotations

from canonical import canonical_hash
import md_ast as _A  # count_draft_claims (has_draft_knowledge, INV-26)

AXES = ("concept", "explain", "apply", "critique", "teachback")


def _iter_source_order(lessons):
    """Duyệt (lesson, review_item) theo (lesson_id asc, rv.id asc) — thứ tự miền băm."""
    for lesson in sorted(lessons, key=lambda L: L.lesson_id):
        for rv in sorted(lesson.review_items, key=lambda r: r.id):
            yield lesson, rv


def build_review_schedule(lessons) -> dict:
    hash_data = [
        {
            "lesson_id": lesson.lesson_id,
            "item_id": rv.id,
            "due_date": rv.card.due_date,     # date → isoformat khi hash
            "mastery_state": rv.mastery_state,
        }
        for lesson, rv in _iter_source_order(lessons)
    ]
    items = [dict(d) for d in hash_data]
    items.sort(key=lambda x: (x["due_date"], x["lesson_id"], x["item_id"]))
    return {"generated_from_hash": canonical_hash(hash_data), "items": items}


def build_assessment(lessons) -> dict:
    incl = [
        L for L in sorted(lessons, key=lambda L: L.lesson_id)
        if L.status in ("learned", "needs_review")
    ]
    hash_data = [
        {
            "lesson_id": L.lesson_id,
            "status": L.status,
            "mastery": {ax: getattr(L.mastery, ax).score for ax in AXES},
        }
        for L in incl
    ]
    out = {"generated_from_hash": canonical_hash(hash_data)}
    n = len(incl)
    for ax in AXES:
        out[f"{ax}_avg"] = (
            round(sum(getattr(L.mastery, ax).score for L in incl) / n, 1) if n else 0.0
        )
    return out


def build_has_draft_knowledge(claim_texts) -> bool:
    """has_draft_knowledge (spec mục 4, INV-26): còn claim status=draft trong topic.md +
    lesson_notes.md của topic. Là VIEW tính trực tiếp, AI không sửa tay."""
    return _A.count_draft_claims(claim_texts or []) > 0


def regen_all(lessons, stage: str = "core", claim_texts=None) -> dict:
    """Sinh lại toàn bộ view (bước REGEN của transaction-FULL).

    stage='core' (GĐ1): review_schedule + assessment (không cần claim parser).
    stage='full' (GĐ2): thêm has_draft_knowledge — tính từ `claim_texts` (list nội dung
    topic.md + lesson_notes.md của topic) bằng md_ast.count_draft_claims (P04b).
    """
    views = {
        "review_schedule": build_review_schedule(lessons),
        "assessment": build_assessment(lessons),
    }
    if stage == "full":
        views["has_draft_knowledge"] = build_has_draft_knowledge(claim_texts)
    return views
