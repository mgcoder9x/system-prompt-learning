# CR-0006 — Ghi mỗi buổi ÔN TẬP vào `lesson.md ## Sessions` (KHÔNG tạo file .md riêng mỗi buổi)

```yaml
id: cr-0006
title: "Ghi transcript buổi ôn: TÁI DÙNG lesson.md '## Sessions' thay vì tạo file .md/buổi"
status: approved
date_opened: 2026-07-04
date_decided: 2026-07-04
version_bump: null
related: [yêu cầu người dùng 'vào ôn → tạo 1 file md + hỏi câu ôn đầu', DEC-051]
recommendation: "TÁI DÙNG ## Sessions (KHÔNG tạo file/buổi) — nhu cầu đã đáp ứng, tránh trùng lặp/xung đột"
```

## 1. Ghi yêu cầu (§12 bước 1)

Hôm sau vào topic (hoặc 'ôn tập') → hỏi câu ôn đầu; tương tác xong câu 1 → câu 2; có nơi ghi lại buổi ôn.

## 2. Phân tích — nhu cầu ĐÃ được mô hình hoá (§12 bước 2)

Spec §14 đã có: mỗi buổi (dạy/ôn) = block `### Session <ngày>` trong `lesson.md › ## Sessions` (dòng
1142); `/resume`,`/status` đọc "## Sessions buổi GẦN NHẤT" (dòng 1026/1383); hỏi MỘT câu/lượt = nhịp §14.
→ Nơi ghi câu ôn + tương tác ĐÃ tồn tại + đã validate (AST §844).

## 3. CONFLICT CHECK — vì sao KHÔNG tạo file riêng (§12 bước 3)

File `.md/buổi` riêng: xung đột INV-25 (index lessons[]↔dir), TRÙNG LẶP ## Sessions (nguồn-thứ-2, anti-drift
DEC-005/012), phá giả định /resume/status. → nặng, rủi ro cao, giá trị thêm ≈ 0.

## 4. Rủi ro (§12 bước 4)

'File/buổi' = trung-cao; 'tái dùng ## Sessions' = ~0 (đã validate).

## 5. Đề xuất (§12 bước 5)

KHÔNG tạo file riêng. Khi ôn: AI thêm block `### Session <ngày> — ôn tập` vào `## Sessions`. `/review` lo FSRS.
(Alias `/ôn` = `/review`: tùy chọn, để CR registry riêng nếu cần — CHƯA làm.)

## 6. Quyết định (§12 bước 6–7) — ĐÃ DUYỆT & ÁP

`approved` 2026-07-04 (owner: "Duyệt"). Áp (DEC-051): sync `rules/review_rules.md` mục "Ghi buổi ôn tập"
(buổi ôn → block `### Session — ôn tập` trong ## Sessions; cấm tạo file riêng; hỏi một-câu/lượt). KHÔNG code
mới / KHÔNG artifact mới (cơ chế ## Sessions đã có + validate). Alias `/ôn` HOÃN (tùy chọn UX). full suite 378 passed.
```
