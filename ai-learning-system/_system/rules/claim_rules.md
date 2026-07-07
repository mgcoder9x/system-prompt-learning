# Claim Rules — Phân lớp khẳng định & luật cứng (spec 0.1, 5.5)

> Khôi phục ngày 2026-07-03: file này (và test drift-guard của nó) bị thiếu trên bản sao máy
> hiện tại sau khi di chuyển workspace — xem `_system/decisions/notes.md` NOTE-006. Nội dung được
> dựng lại **bám nguồn xác minh được**: bảng lớp A/B/C/D lấy verbatim từ spec mục 0.1; taxonomy
> máy-đọc bám hằng số code `validate._CLAIM_CLASSES` / `_CLAIM_STATUS`; mã lỗi/INV bám `validation_rules.md`.

Nguồn sự thật cho **cách phân lớp và ràng buộc claim**. Đổi bảng này PHẢI qua change request (spec 12).
Khối máy-đọc `claim_taxonomy` được test kiểm khớp **CHÍNH XÁC** với hằng số code
(`validator/validate.py`: `_CLAIM_CLASSES`, `_CLAIM_STATUS`) — đổi ở code mà quên cập nhật đây → test đỏ.

## Phạm vi (spec 5.5 — cố ý hẹp để khả thi)

Mọi claim trong mục `## Claims` của `lesson_notes.md` và `topic.md` phải mang `class` + `status`.
Chỉ claim `status: confirmed` mới là **kiến thức chính thức**; `status: draft` là ghi chú làm việc
chưa nguồn-hoá. Hội thoại/transcript trong `lesson.md` KHÔNG phải claim. Claim ngoài vùng cho phép → `E-CLAIM-LOC` (INV-23).

## Bốn lớp khẳng định (spec 0.1 — verbatim)

| Lớp | Loại khẳng định | Cách kiểm | Mức đảm bảo |
|-----|-----------------|-----------|-------------|
| **A** | Sự thật cấu trúc/tính toán | Validator dạng code | Đúng tuyệt đối |
| **B** | Kiến thức bám nguồn | Phải trỏ tới anchor trong `sources.md` | Đúng nếu trích dẫn tồn tại và đúng phạm vi |
| **C** | Suy luận của AI | Phải liệt kê tiền đề (đều là A hoặc B) | Hợp lệ nếu suy luận từ tiền đề hợp lệ |
| **D** | Phán đoán năng lực người học | Rubric rời rạc + bằng chứng trích nguyên văn | Tái lập được, không tuyên bố chân lý |

## Hai trạng thái (spec 0.1 / 15.1)

- `draft` — ghi chú chưa nguồn-hoá: được kiểm cấu trúc, **cấm** vào `## Knowledge Map`, **cấm** làm tiền đề
  chắc chắn; **bắt buộc** có `draft_reason` (`E-CLAIM-DRAFTREASON` nếu thiếu, INV-15).
- `confirmed` — khẳng định chính thức: áp đầy đủ luật lớp bên dưới.

## Luật cứng (spec 0.1 / mục 9.x — mỗi luật một mã lỗi kiểm được)

- Mọi claim trong `## Claims` phải đủ `id/class/status/text`; thiếu/không hợp lệ → `E-CLAIM-UNCLASSED` (INV-15).
- Claim `confirmed` lớp **B** không có anchor nguồn `confirmed` → `E-CLAIM-NOSRC` (INV-12).
- Không dùng nguồn `raw`/`rejected` làm anchor → `E-SRC-RAWUSED` (INV-13).
- Claim `confirmed` lớp **C** có tiền đề thuộc lớp D hoặc tiền đề `draft` → `E-CLAIM-WEAKBASE` (INV-14).
  (Mọi tiền đề phải là claim A/B `confirmed`.)
- Claim `draft` xuất hiện trong `## Knowledge Map`, hoặc cờ `has_draft_knowledge` sai → `E-DRAFT-IN-MAP` (INV-26).
- Trạng thái "đã hiểu" (lớp D) **không bao giờ** được nâng thành sự thật (lớp A).

## Giới hạn cố hữu (spec 0.3 — trung thực, không tô hồng)

Validator chỉ kiểm **liên kết/cấu trúc**, KHÔNG kiểm ngữ nghĩa: với B nó xác nhận anchor *tồn tại*
chứ không xác nhận `quote` chống đỡ claim; với C nó xác nhận *có liệt kê* tiền đề chứ không xác nhận
suy luận hợp lệ. Lớp D KHÔNG được enforce "tái lập" — rubric chỉ *giảm* phương sai, không *khử*.

### claim_taxonomy (máy đọc)

```yaml
claim_taxonomy:
  claim_classes: [A, B, C, D]
  claim_statuses: [draft, confirmed]
```
