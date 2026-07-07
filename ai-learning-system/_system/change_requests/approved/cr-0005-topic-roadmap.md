# CR-0005 — Thêm section `## Lộ trình` vào `topic.md` (lộ trình điểm cần học của topic)

```yaml
id: cr-0005
title: "Lộ trình học cấp-topic: section '## Lộ trình' trong topic.md (điểm cần học + trạng thái)"
status: approved
date_opened: 2026-07-04
date_decided: 2026-07-04
version_bump: null         # KHÔNG đổi schema (topic.md là content optional, không front-matter state)
related: [yêu cầu người dùng 'nó phải lên rõ lộ trình các điểm cần học', DEC-050]
recommendation: "CÓ, light-touch: convention prose + AI-authored, KHÔNG nâng thành INV cứng (v1)"
```

## 1. Ghi yêu cầu (§12 bước 1)

Người học muốn khi học một topic thì thấy RÕ "lộ trình các điểm cần học" của topic đó (syllabus).

## 2. Phân tích — vấn đề & phân loại (§12 bước 2)

Spec HIỆN KHÔNG có "lộ trình cấp-topic" (sections_pending = giai-đoạn-dạy; Knowledge Map = kiến-thức-đã-chốt).
→ TÍNH NĂNG MỚI thật. `topic.md` (content cấp-topic, optional, không front-matter) là chỗ tự nhiên.

## 3. CONFLICT CHECK (§12 bước 3)

Không mâu thuẫn rules/. `## Lộ trình` không chứa fenced `claims:` → không kích INV-23. topic.md không bị ép
heading bắt buộc (khác lesson.md §844). Portability OK (prose).

## 4. Rủi ro (§12 bước 4)

Light-touch: rất thấp. KHÔNG nâng thành INV cứng (tránh coupling lộ-trình↔lessons).

## 5. Đề xuất (§12 bước 5)

`## Lộ trình` trong topic.md, bullet `- [todo|doing|done] <điểm>`; AI soạn khi /learn + dạy. Tạo topic.md
từ template lúc /learn. KHÔNG INV cứng v1.

## 6. Quyết định (§12 bước 6–7) — ĐÃ DUYỆT & ÁP

`approved` 2026-07-04 (owner: "Duyệt"). Đã implement (DEC-050): thêm `templates/topic_template/topic.template.md`
(`## Lộ trình` + `## Knowledge Map`); cmd_learn ghi `topic.md` (body raw subst); sync `rules/teaching_rules.md`;
RED-first test `test_session_learn.py::test_learn_creates_topic_md_with_roadmap` (topic.md có `## Lộ trình` +
validate PASS). full suite 378 passed. KHÔNG bump VERSION (không đổi schema).
```
