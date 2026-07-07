```yaml
repo_id: "fsrs"
repo_url: "https://github.com/open-spaced-repetition/py-fsrs"
role: "install_dependency"
used_for: ["review_engine"]
install_location: "_system/.venv"
source_location: null
license: "MIT"
version_or_commit: "6.3.1"
lock_source: "requirements.txt"      # pip-compile --generate-hashes (có hash); cài: pip install --require-hashes
uv_version: null
reference_commit: null
refresh_policy: "manual only via change request"
why: "Chuẩn SR hiện đại (DSR); runtime chỉ typing-extensions; API Scheduler/Card/Rating/ReviewLog."
risks:
  - "due tính bên trong review_card từ stability float → cross-platform boundary (xem SPIKE F-B)."
  - "State enum KHÔNG có 'New' (xem SPIKE F-A)."
  - "review_datetime BẮT BUỘC aware-UTC, reject cả naive lẫn +07:00."
rollback: "pip uninstall fsrs; xoá .venv; pin lại version cũ trong requirements.txt."
verified_at: 2026-07-01
```

## SPIKE P01.0 — Kết quả khảo sát API (fsrs 6.3.1, 2026-07-01)

| Câu hỏi | Kết quả thật |
|---|---|
| Q1 `review_card` trả gì | `(Card, ReviewLog)`. `Card.due` là `datetime` **tính SẴN bên trong** từ stability. |
| Q2 formula interval public | **KHÔNG có** hàm `next_interval(stability)`. Có `get_card_retrievability`, `reschedule_card(card, review_logs)`. |
| Q3 parameters | **21 weights** (FSRS-6) — đã copy vào `fsrs_config.yaml`. `enable_fuzzing` mặc định **True** → phải set False. |
| Q4 Card mới | `state=State.Learning` (step=0), `stability=None`, `difficulty=None`, `last_review=None`, `due=now`. **KHÔNG có State.New.** `card_id` sinh theo timestamp (phi tất định). |
| Q5 review_datetime | **BẮT BUỘC aware-UTC**; raise `ValueError` cho cả naive lẫn aware +07:00. |
| Serialize | `Card.to_dict/from_dict/to_json/from_json` OK; round-trip due khớp. |
| Determinism | `enable_fuzzing=False` → 2 lần chạy cùng `due` + `stability`. |
| `State` enum | `{Learning:1, Review:2, Relearning:3}` — **không có New**. |
| `reschedule_card` | `(card, review_logs:list[ReviewLog]) -> Card` — có thể dùng làm primitive replay. |

## Hai phát hiện ảnh hưởng SPEC (cần chốt trước khi code adapter/schema)

- **F-A (schema):** py-fsrs KHÔNG có `State.New`. Spec v2.5 (5.1/6.2) giả định `card.state==New`. Phải đổi: enum = `Learning|Review|Relearning`; "chưa review" = `last_review is None` / `log == []` / `stability is None`.
- **F-B (determinism):** `due` do `review_card` tính nội bộ từ stability (transcendental float); KHÔNG có hook quantize-trước-due. Spec v2.5 (8.3/INV-08) đòi "quantize stability TRƯỚC khi tính due" + so `due_at_utc` exact → **không khả thi sạch** cross-platform. Cần chuyển sang so theo `due_date` (ngày) làm chuẩn cho Review-state.

→ Cả hai đề xuất gói vào change request nâng spec **v2.6** (xem chat).
