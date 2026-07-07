# CR-0001 — Vá spec theo SPIKE FSRS thật (v2.5 → v2.6)

```yaml
id: cr-0001
title: "Sửa spec cho khớp API py-fsrs 6.3.1 thật (F-A + F-B)"
status: approved
date_opened: 2026-07-01
date_decided: 2026-07-01
date_documented: 2026-07-03        # ghi hồi tố đúng quy trình §12
version_bump: "v2.5 -> v2.6 (schema)"
retroactive: true                  # thay đổi đã áp trong spec v2.6; CR này hợp thức hoá vết
related_decisions: [DEV-001, DEV-002, DEV-003]
```

## 1. Ghi yêu cầu (§12 bước 1)

Spec v2.5 giả định API FSRS mà py-fsrs 6.3.1 thực tế KHÔNG cung cấp → phải sửa spec cho khớp thư viện thật
(dùng của họ, không tự chế). Ghi hồi tố vì đã áp trong v2.6.

## 2. Phân tích — vấn đề giải quyết (§12 bước 2)

- **F-A (schema):** py-fsrs KHÔNG có `State.New`; spec v2.5 (5.1/6.2) giả định `card.state == New`.
- **F-B (determinism):** `due` do `review_card` tính nội bộ từ `stability` (float siêu việt), KHÔNG có hook
  quantize-trước-due; spec v2.5 (8.3/INV-08) đòi quantize stability TRƯỚC khi tính due + so `due_at_utc` exact
  → không khả thi sạch cross-platform.

## 3. Conflict check với `_system/rules/` (§12 bước 3)

- Thời điểm áp (2026-07-01) `rules/` chưa dựng → không mâu thuẫn luật hiện có.
- **Bất biến bị chạm:** INV-08 (replay khớp). Không phá — mà *tinh chỉnh định nghĩa*: so trạng thái Review
  theo `due_date` (ngày) thay vì `due_at_utc` exact. Kiểm-được vẫn giữ (replay + so due_date).
- Không trùng lặp luật khác.

## 4. Đánh giá rủi ro (§12 bước 4)

- Rủi ro: float transcendental lệch cross-platform. **Giảm** bằng cách chuẩn hoá trục so về `due_date`.
- Không giảm portability; không làm AI khó tiếp tục (mô hình rõ ràng hơn).

## 5. Đề xuất đã tinh chỉnh (§12 bước 5)

- Enum trạng thái card = `Learning | Review | Relearning` (bỏ New).
- "Chưa review" = `log == []` / `stability is None` / `last_reviewed_at_utc is None` (KHÔNG theo state).
- Trục so lịch cho Review-state = `due_date`; item Learning/Relearning vẫn theo `due_at_utc <= now`.

## 6. Quyết định (§12 bước 6–7)

`approved` — đã áp trong spec **v2.6** (2026-07-01). Ghi `changelog.md`. Bump VERSION schema v2.5 → v2.6.

## 7. Bằng chứng kiểm chứng (không bịa)

- `PROMPT_LEARNING_SYSTEM.md` header: "vá theo SPIKE FSRS thật v2.6 ngày 2026-07-01 (F-A ...; F-B ...)".
- `validator/models.py` docstring + `CardStateT = Literal["Learning","Review","Relearning"]`; `Card.due_date`;
  `ReviewItem._check_log_vs_card` (chưa-review theo `log`).
- `repo_lab/repo_evaluations/fsrs.md`: SPIKE F-A/F-B + risks.
