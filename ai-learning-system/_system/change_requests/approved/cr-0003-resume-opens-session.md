# CR-0003 — `/resume` MỞ phiên (ghi `open_session`), không còn "chỉ đọc"

```yaml
id: cr-0003
title: "Chốt mâu thuẫn spec: /resume ghi open_session (§5.4/§11B.2) — commands.md 'chỉ đọc' → 'ghi open_session'"
status: approved
date_opened: 2026-07-03
date_decided: 2026-07-03
version_bump: null            # không đổi schema (open_session đã có trong vault_state)
related_decisions: [DEC-016, DEC-028]
supersedes_part_of: DEC-016   # DEC-016 làm /resume read-only; CR này đảo phần đó
```

## 1. Ghi yêu cầu (§12 bước 1)

Mâu thuẫn nội bộ spec: `commands.md` ghi `/resume | chỉ đọc`, nhưng §5.4 và §11B.2 nói
`/learn, /resume mở phiên → ghi open_session.lesson_id + started_at`. Cần chốt một chiều.

## 2. Phân tích — vấn đề giải quyết (§12 bước 2)

Cơ chế phát-hiện-phiên-chưa-đóng-sổ (§11B.2) chỉ hoạt động khi CÓ lệnh MỞ phiên. `/learn` đã mở
(part 1). Nếu `/resume` KHÔNG mở, thì resume một lesson dở rồi đóng IDE giữa chừng → không cờ nào
báo "chưa /done" ở lần vào sau → mất an toàn UX. Vậy `/resume` phải mở phiên.

## 3. CONFLICT CHECK với `_system/rules/` (§12 bước 3)

- Không mâu thuẫn luật trong `rules/`.
- Bất biến: open_session KHÔNG phải invariant (validator không báo lỗi khi != null, §11B.2) → không phá INV.
- Ghi open_session là transaction-LIGHT (chỉ đụng vault_state front-matter) → OCC/manifest vẫn áp.

## 4. Đánh giá rủi ro (§12 bước 4)

- Đảo phần "read-only" của DEC-016 → `/resume` giờ ghi. Rủi ro: nhỏ (chỉ set 2 field open_session,
  không đụng FSRS/view/claim). Lưới an toàn: LIGHT validate + /done FULL sau.
- Không giảm portability.

## 5. Đề xuất đã tinh chỉnh (§12 bước 5)

`/resume`: đọc current_lesson + next_action (để hiển thị) VÀ set `open_session.lesson_id=current_lesson`,
`started_at=now` trong transaction-LIGHT. Không có current_lesson → no-op (không mở gì).

## 6. Quyết định (§12 bước 6–7)

`approved`. Áp: `commands.md` (`/resume` cột "Ghi vào đâu": chỉ đọc → "vault_state.open_session (LIGHT)")
+ `changelog.md`. cmd_resume chuyển thành write. Không bump VERSION.
