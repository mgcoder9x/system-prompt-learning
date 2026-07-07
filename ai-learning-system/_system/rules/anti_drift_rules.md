# Anti-Drift Rules — Chống trôi hệ thống (spec §17, §18)

> Nguồn: spec §17 "Nguyên Tắc Chống Drift". Khối máy-đọc `anti_drift.code_enforced` được test
> `phase10/test_anti_drift_memory_consistency.py` giữ khớp: mọi `code` phải nằm trong tập mã lỗi thật
> (`validation_rules.md` → `error_codes`). Thêm rủi ro code-enforced mà bịa mã không tồn tại → test đỏ.

## Nguyên tắc (spec §17 — verbatim)

- Mỗi file có mục đích rõ; mỗi `*_state.md` có front-matter ở đầu.
- Mọi cập nhật ghi ngày; không đổi mục tiêu học nếu chưa ghi lý do.
- Không đánh dấu hoàn thành nếu chưa qua cổng (§9.3).
- Không để AI đoán trạng thái khi file đã có dữ liệu.
- Không áp change request khi chưa routing/đánh giá/xác nhận/kiểm xung đột (§12).
- Không xóa review item chưa hoàn thành khi chuyển bài (INV-11).
- Không trộn `_system/` và `learning_vault/` (INV-16..18).
- Không đường dẫn tuyệt đối trong vault (INV-16).
- **Không tự tuyên bố "đã valid" — phải chạy validator và dán kết quả (§10.1).**
- Không nâng khẳng định lớp D thành lớp A.

## Hai lớp cưỡng chế (trung thực về cái gì code chặn được)

**Code-enforced** — validator có mã lỗi chặn thật; **process-enforced** — chỉ chặn bằng quy trình/con
người, KHÔNG có mã code (đúng giới hạn cố hữu §0.3: LLM có thể nói dối, phòng tuyến cuối là người dùng chạy validator).

### anti_drift (máy đọc)

```yaml
anti_drift:
  code_enforced:
    - {risk: "xóa review item chưa xong khi chuyển bài", inv: "INV-11", code: "E-REVIEW-LOST"}
    - {risk: "trộn code/dependency vào vault", inv: "INV-17", code: "E-MIX-CODE"}
    - {risk: "trộn dữ liệu học vào _system", inv: "INV-18", code: "E-MIX-DATA"}
    - {risk: "đường dẫn tuyệt đối trong vault", inv: "INV-16", code: "E-PORT-ABSPATH"}
    - {risk: "đánh dấu learned khi chưa qua cổng", inv: "INV-07", code: "E-GATE-FAIL"}
  process_enforced:
    - "tự tuyên bố đã valid mà chưa chạy validator (§10.1) — con người là phòng tuyến cuối"
    - "áp change request khi chưa routing/đánh giá/xác nhận/kiểm xung đột (§12)"
    - "nâng khẳng định lớp D thành lớp A (§0.1)"
    - "để AI đoán trạng thái khi file đã có dữ liệu"
    - "đổi mục tiêu học mà không ghi lý do/ngày"
```
