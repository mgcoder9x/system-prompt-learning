# CR-0004 — Ép `sources[].added <= today` (toàn vẹn thời gian cho nguồn)

```yaml
id: cr-0004
title: "Mở rộng nguyên tắc 'không dữ-liệu-ngày-tương-lai' (INV-05) sang sources[].added"
status: approved
date_opened: 2026-07-04
date_decided: 2026-07-04
version_bump: null         # không đổi schema (added đã có trong sources.md); chỉ thêm ràng buộc validator
related_decisions: [DEC-029, DEC-044]
related_open_question: "DEC-029 open_question: có ép sources[].added <= today không? → CHỐT: CÓ"
recommendation: "CÓ (lean YES) — xem §6"
```

## 1. Ghi yêu cầu (§12 bước 1)

INV-05 (spec §5.1) ép `created <= updated <= today` cho state file (lesson_state/topic_state).
DEC-029 đã enforce phần `updated <= today` ở validator. Nhưng `sources[].added` (spec §5.3 — ngày
nạp nguồn) hiện KHÔNG bị ràng buộc `<= today`: vault có thể lưu `added` ở TƯƠNG LAI mà validator PASS.

## 2. Phân tích — vấn đề & phân loại (§12 bước 2)

**Bản chất câu hỏi (theo bài học NOTE-012):** đây là "under-enforce so với nguyên-tắc-spec" (đáng fix)
hay "spec cố ý không yêu cầu" (không được tự thêm)?

- Lập luận CÓ (under-enforce): `added` là một DẤU THỜI GIAN của sự kiện thực (nạp nguồn). Nguồn KHÔNG
  thể "được nạp vào ngày mai" — `added` tương lai luôn vô nghĩa / là tampering hoặc lỗi đồng hồ. Nguyên
  tắc toàn-vẹn-thời-gian mà INV-05 thể hiện (determinism, auditability, không dữ-liệu-tương-lai) là
  TỔNG QUÁT, và `added` là dấu thời gian → hợp lý áp cùng. Driver (cmd_source) LUÔN set `added=today`,
  nên cách DUY NHẤT có `added>today` là sửa tay → enforcement bắt đúng tampering.
- Lập luận KHÔNG (spec cố ý bỏ): spec §5.1 liệt kê CỤ THỂ created/updated, KHÔNG nhắc added.
- **Khác biệt then chốt với NOTE-012:** ca claim (NOTE-012) spec **NÓI RÕ** "phạm vi cố ý hẹp" → exemption
  tường minh → KHÔNG thêm. Ca này spec chỉ **KHÔNG NHẮC** added → OMISSION (bỏ sót), không phải exemption.
  Một dấu-thời-gian không-thể-tương-lai bị bỏ khỏi invariant toàn-vẹn-thời-gian → nghiêng "under-enforce".

## 3. CONFLICT CHECK với `_system/rules/` (§12 bước 3)

- Không mâu thuẫn luật trong `rules/`. `validation_rules.md` mã E-SCHEMA đã dùng cho vi phạm ngày (DEC-029).
- Không phá INV khác: chỉ THÊM một điều kiện; không đụng INV-04/12/13.
- Nhất quán DEC-029: dùng CÙNG mốc `today` = ngày lịch thật theo utc_offset (KHÔNG day_cutoff), now bơm được.

## 4. Đánh giá rủi ro (§12 bước 4)

- Rủi ro thấp, hoàn toàn reversible (gỡ 1 check).
- Nợ tất định (giống NOTE-010): đã KIỂM full suite sau implement → 362 passed, KHÔNG test sources nào
  có `added` tương lai so với now → không hồi quy.
- Không giảm portability.

## 5. Đề xuất đã tinh chỉnh (§12 bước 5)

Thêm `_check_source_added_not_future(src_model, rel, today_local, rep)` ở `validate.py`, gọi trong
`_validate_topic` (đường full_core, nơi đã có today_local + parse sources.md). added tương lai → `E-SCHEMA`.

## 6. Quyết định (§12 bước 6–7) — ĐÃ DUYỆT & ÁP

`approved` 2026-07-04 (spec-owner duyệt qua chỉ thị "duyệt theo khuyến nghị"). Đã implement RED-first
(DEC-044): `_check_source_added_not_future` + wire `_validate_topic`; test phase07a_core/test_inv05_source_added.py
(4 test: 2 âm added-tương-lai → E-SCHEMA, 2 dương added hôm-nay/quá-khứ → PASS). full suite 362 passed;
validator full vault thật PASS. Ghi changelog. KHÔNG bump VERSION (không đổi schema).
```
