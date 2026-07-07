# CR-0009 — Mở rộng spec: multi-lesson theo giáo trình + `reference/` + `exam/`

```yaml
id: cr-0009
title: "Sửa spec (§3/§11A/§14 + mục mới): mô tả Curriculum nhiều bài, vùng reference/, vùng exam/"
status: approved
date_opened: 2026-07-05
date_decided: 2026-07-06
version_bump: "v2.6 → v2.7 (đề xuất — thêm khái niệm, không phá cấu trúc cũ)"
related: [spec curriculum-driven-learning (toàn bộ), DEC-055, CR-0007, CR-0008]
recommendation: "SỬA spec bổ sung khái niệm giáo trình/reference/exam; giữ tương thích ngược (bài hiện có vẫn hợp lệ)"
```

## 1. Ghi yêu cầu (§12 bước 1)

Spec hiện (v2.6) hình dung một topic có nhiều lesson (ví dụ Docker 5 lesson) nhưng **không mô tả** cơ chế giáo trình (curriculum), vùng `reference/`, hay vùng `exam/`. Cần bổ sung để tính năng có gốc spec.

## 2. Phân tích (§12 bước 2)

- §3 (cấu trúc topic/lesson): thêm `curriculum.md` + `reference/` vào layout topic.
- §11A (lệnh): thêm mô tả 5 lệnh mới (bám CR-0008).
- §14 (Sessions/dạy): nêu lesson được sinh bám Curriculum_Point + auto-advance sau `learned_gate`.
- Mục mới: **Exam** (`exam/` ngoài vault; bản ghi chấm `exam_results.md`; ranh giới Class D).
- Mục mới: **Curriculum** (định nghĩa points/order/status/teachable + Curriculum_Validator + 9 mã lỗi).

## 3. Tương thích ngược (§12 bước 3)

Chỉ THÊM khái niệm; KHÔNG đổi ngữ nghĩa cũ. Topic không có `curriculum.md` vẫn hợp lệ (curriculum là tùy chọn, chỉ kích khi tồn tại). → bài/vault hiện tại KHÔNG hồi quy. Đề xuất bump **v2.7** (minor, thêm tính năng).

## 4. Rủi ro (§12 bước 4)

Trung. Rủi ro chính: spec-code lệch → dùng drift-guard (validation_rules error_codes ⊇ mã mới; commands↔registry). Đổi spec là thay đổi "hiến pháp" → cần owner duyệt kỹ + ghi changelog + bump VERSION spec.

## 5. Đề xuất (§12 bước 5)

Sửa spec + bump v2.7 SAU khi code (CR-0007/0008) đã XANH (spec phản ánh đúng cái đã hiện thực + kiểm-được), theo Task 11. Tránh spec "hứa" trước code.

## 6. Quyết định (§12 bước 6–7) — ĐÃ DUYỆT

`approved` 2026-07-06 (owner qua tín hiệu "duyệt theo khuyến nghị từng bước"). Áp SAU khi code CR-0007/0008 đã XANH (spec phản ánh đúng cái đã hiện thực + kiểm-được, không "hứa" trước code). Đã sửa:
- **Tiêu đề + dòng trạng thái**: v2.6 → **v2.7** (2026-07-06).
- **§3.2**: thêm `curriculum.md` + `reference/` + `exam_results.md` vào layout topic (đều TÙY CHỌN, tương thích ngược).
- **§3.4 (mới)**: vùng `reference/` (chỉ .md, on-demand) + vùng `exam/` (NGOÀI vault, bài nộp có thể code; chỉ `exam_results.md` metadata trong vault — diễn giải INV-17).
- **§3.5 (mới)**: khái niệm Curriculum/Curriculum_Point (points/order/status/teachable), `topic_state.lessons[]` vẫn nguồn sự thật index (INV-25), Curriculum_Validator + 7 mã lỗi Class A.
- **§11A.2**: thêm 5 lệnh `/collect` `/curriculum` (+`--check`) `/next-lesson` `/grade`.
- **§14 bước 4b (mới)**: auto-advance giáo trình sau `learned_gate`.

**KHÔNG bump `_system/VERSION`** (=1): curriculum/exam dùng `schema_version: 1` (additive), không đổi cấu trúc dữ liệu on-disk → không cần migration. Version tài liệu spec (semver v2.7) tách khỏi schema_version dữ liệu (DEV-004). Ghi changelog (cột VERSION v2.6→v2.7) + DEV-006 (đổi spec).
