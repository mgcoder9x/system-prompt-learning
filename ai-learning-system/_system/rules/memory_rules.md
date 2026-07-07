# Memory Rules — Bộ nhớ dạng file & nạp ngữ cảnh (spec §74–78, §11B.1, §15.1)

> Nguồn: yêu cầu bộ nhớ (§74–78), trình tự boot chống tràn token (§11B.1), draft-vs-confirmed (§15.1/0.1).
> Khối máy-đọc `context_boot` được test giữ khớp danh sách nạp spec §11B.1. Đây là luật HÀNH VI của AI
> (phần lớn process-enforced); guard ở mức khớp danh sách boot + presence.

## 1. Bộ nhớ = file, không phải ngữ cảnh hội thoại (spec §74–78)

- Trạng thái sống nằm trong `*_state.md` (vault/topic/lesson), cập nhật liên tục, chống trôi ngữ cảnh.
- Bất kỳ phiên AI nào đọc các file trạng thái vào là hiểu ngay "đang học gì, ở đâu, đã hiểu gì, còn vướng gì"
  và tiếp tục đúng — KHÔNG dựa vào trí nhớ hội thoại của một phiên.
- Mọi file nạp làm nền để sinh thay đổi phải ghi `expected_read_hash` (§10.3) để phát hiện sửa-tay (E-STALE-CONTEXT).

## 2. Trình tự nạp ngữ cảnh khi `/resume` hoặc `/status` (spec §11B.1 — chống tràn token)

`lesson.md` phình to theo thời gian (toàn transcript). Nạp cả file → loãng ("lost in the middle") + tốn cost.
AI **CHỈ được nạp**:
1. Các file `*_state.md` (vault_state, topic_state, lesson_state) — nguồn trạng thái.
2. `lesson_notes.md` — cốt lõi đã chắt.
3. **CHỈ** section `## Sessions` của buổi **GẦN NHẤT** trong `lesson.md`.

Session cũ = archive làm **bằng chứng cho validator**, KHÔNG nạp vào context trừ khi có lệnh tra cứu cụ thể
(vd `/ask` về điểm cũ). Không ảnh hưởng tính đúng: validator vẫn đọc toàn bộ khi chạy FULL; chỉ cửa sổ ngữ
cảnh của AI được giữ gọn.

## 3. Trí nhớ mô hình KHÔNG phải kiến thức chính thức (spec §15.1, §0.1)

- Điều AI nói "từ trí nhớ mô hình" ≠ điều đã có nguồn. Chưa có nguồn vẫn dạy được ở chế độ **draft**
  (claim `status: draft`, có `draft_reason`, hiển thị "chưa kiểm nguồn"), nhưng **cấm** vào `## Knowledge Map`.
- Chỉ claim `status: confirmed` có nguồn confirmed mới thành kiến thức chính thức. **Không bịa nguồn.**

### context_boot (máy đọc)

```yaml
context_boot:
  load_only: [state_files, lesson_notes, latest_sessions_only]   # spec §11B.1
  never_load_full_transcript: true
  old_sessions_role: archive_evidence_for_validator
```
