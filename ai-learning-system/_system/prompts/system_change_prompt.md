# System Change Prompt — Quy trình sửa hệ thống (spec 12)

> Nạp khi intent = `system_change` (hoặc lệnh `/system`). Luật gốc: **yêu cầu sửa hệ thống KHÔNG BAO GIỜ
> áp dụng ngay.** Áp nóng luật/prompt/schema là vi phạm nghiêm trọng.

## Quy trình 7 bước (spec 12 — bám verbatim)

1. **Ghi yêu cầu** vào `_system/change_requests/pending/<id>.md`.
2. **Phân tích**: yêu cầu này giải quyết vấn đề gì.
3. **CONFLICT CHECK** — đối chiếu với MỌI luật trong `_system/rules/`:
   - Mâu thuẫn luật cũ → liệt kê **cặp mâu thuẫn cụ thể** (luật nào, dòng nào).
   - Trùng lặp → chỉ ra.
   - Phá vỡ một bất biến (spec 10.2) → **CHẶN**, nêu rõ bất biến nào.
4. **Đánh giá rủi ro**: drift, làm AI khó tiếp tục, giảm portability.
5. **Viết lại** thành đề xuất rõ ràng hơn câu thô ban đầu.
6. **Trình người dùng xác nhận.**
7. **Sau xác nhận**: move `pending/ → approved/`, áp dụng, ghi `changelog.md` (ngày, lý do, file đụng tới);
   **tăng `_system/VERSION` nếu đổi schema**.

Bước 3 (conflict check) là mấu chốt: giữ `_system/rules/` không tích lũy mâu thuẫn ngầm theo thời gian.

## Ràng buộc kèm theo

- `/system <đề xuất>` chỉ TẠO change request ở `pending/`, không thực thi (spec 11A).
- Thao tác duyệt/áp dụng đụng file `_system/` cũng phải qua Write Transaction + validate trước khi commit (spec 10.3).
- Đổi tập lệnh, mã lỗi, mapping grade→rating, claim taxonomy, schema... đều là `system_change` → phải qua đây,
  và sẽ làm đỏ drift-guard tương ứng nếu doc/code lệch (buộc cập nhật đồng bộ).
- Refresh reference repo (nếu có) cũng là `system_change`: nêu lý do + diff/rủi ro, không âm thầm đổi luật vì upstream đổi (spec 16.2).

## Vòng đời trạng thái

```yaml
change_request:
  states: [pending, approved, rejected]
  log: changelog.md
  never_apply_immediately: true
```
