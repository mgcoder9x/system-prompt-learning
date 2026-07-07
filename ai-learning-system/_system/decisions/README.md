# Decision Journal — Nhật ký quyết định AI (xuyên suốt, để kiểm chứng)

> Thư mục này là **bộ nhớ dài hạn có kiểm chứng** cho mọi quyết định mà AI đưa ra trong quá
> trình xây dựng `ai-learning-system`. Mục tiêu: sản phẩm thương mại, an toàn, lâu dài → phải
> **truy vết được** vì sao hệ thống thành ra như hiện tại, không dựa vào trí nhớ hội thoại.

## Vì sao tồn tại (4 việc theo yêu cầu)

| File | Việc | Nội dung |
|------|------|----------|
| `decisions.md` | (1) | Các quyết định AI **tự ra** mà spec KHÔNG nói |
| `deviations.md` | (2) | Những chỗ AI **phải đổi** so với yêu cầu/spec ban đầu |
| `tradeoffs.md` | (3) | Các **trade-off** AI phải cân nhắc (kèm phương án bị loại) |
| `notes.md` | (4) | **Bất kỳ điều gì** AI sau nên biết (trạng thái, cạm bẫy, môi trường) |
| `index.yaml` | — | Bảng **máy-đọc** cuộn toàn bộ entry (id/type/status/verified) để AI quét nhanh |

## Nguyên tắc bất di bất dịch (bám kỷ luật dự án)

1. **KHÔNG bịa, KHÔNG suy đoán.** Mỗi entry phải có `evidence` trỏ tới nguồn kiểm chứng được:
   đường dẫn file + dòng, tên test, hoặc lệnh đã chạy. Không có bằng chứng → không được ghi là fact.
2. **Trung thực về mức kiểm chứng.** Trường `verified`:
   - `verified: true` + `method: read-source` → đã đọc trực tiếp mã nguồn/ file trong phiên.
   - `verified: true` + `method: ran-test|ran-command` → đã chạy thật và thấy output.
   - `verified: false` + `method: transcript` → chỉ dựa trên nhật ký phiên trước (`end.md`), CHƯA
     chạy lại trong phiên hiện tại. **Phải nói rõ**, không được tô hồng.
3. **Append-only theo tinh thần.** Không xoá lịch sử. Khi một quyết định bị thay thế → đặt
   `status: superseded`, thêm `superseded_by: <id>`, giữ nguyên entry cũ để truy vết.
4. **Fix tận gốc, không fix ngọn.** Entry mô tả sửa lỗi phải nêu **nguyên nhân gốc** đã kiểm chứng,
   không chỉ triệu chứng.
5. **ID không tái sử dụng.** Mỗi entry một ID vĩnh viễn.

## Lược đồ entry (schema — dùng cho mọi file)

Mỗi entry là một khối YAML fenced (theo đúng quy ước máy-đọc của dự án), kèm phần diễn giải người-đọc.

```yaml
id: <DEC|DEV|TRD|NOTE>-NNN        # tiền tố theo loại; số tăng dần, không tái dùng
type: decision|deviation|tradeoff|note
date: YYYY-MM-DD
title: "một dòng tóm tắt"
spec_ref: "nguồn spec liên quan; hoặc 'none (spec silent)'"
summary: "quyết định/đổi/đánh đổi là gì"
rationale: "vì sao — bám bản chất"
alternatives: ["phương án bị loại (bắt buộc cho tradeoff)"]     # optional
evidence:                          # BẮT BUỘC — trỏ tới thứ kiểm chứng được
  - "path/to/file.py:Lxx  (mô tả)"
  - "tên_test hoặc lệnh đã chạy"
verified: true|false
method: read-source|ran-test|ran-command|transcript
status: active|superseded|open-question
reversible: "cách hoàn tác / rollback nếu có"
superseded_by: <id>                # optional, chỉ khi status=superseded
```

## Quy trình cập nhật (cho AI ở phiên sau)

1. Đọc `index.yaml` trước để nắm toàn cảnh (rẻ, nhanh).
2. Trước khi khẳng định bất cứ điều gì trong nhật ký này là "đúng hiện tại", **kiểm chứng lại**
   (đọc source / chạy test) rồi mới nâng `verified` hoặc thêm entry mới.
3. Khi thêm entry: ghi vào file loại tương ứng **và** thêm dòng cuộn vào `index.yaml`.
4. Nếu phát hiện entry cũ sai/lỗi thời: KHÔNG xoá — chuyển `status`, liên kết `superseded_by`.

## Ranh giới an toàn với validator (INV-18)

Thư mục này nằm trong `_system/` nên bị INV-18 (E-MIX-DATA) quét. Đã kiểm chứng an toàn:
tên các file ở đây (`README.md`, `decisions.md`, `deviations.md`, `tradeoffs.md`, `notes.md`,
`index.yaml`) **không** trùng `_SYSTEM_DATA_NAMES` và thư mục không tên `topics/`
→ không kích E-MIX-DATA. **Cấm** đặt file tên `lesson.md`, `topic.md`, `*_state.md`, `sources.md`,
`lesson_notes.md` trong thư mục này (xem `validator/validate.py` hằng `_SYSTEM_DATA_NAMES`).
