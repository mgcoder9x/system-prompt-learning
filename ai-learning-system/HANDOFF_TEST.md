# HANDOFF TEST — Prompt cho AI KHÁC (dán toàn bộ file này cho AI đó)

> **Mục đích:** Kiểm chứng tuyên bố cốt lõi của hệ thống này: *"Copy trọn thư mục sang máy/AI khác thì
> VẪN vận hành đúng, dữ liệu vẫn được bảo đảm toàn vẹn."* Bạn (AI nhận prompt này) là **đối tượng test**.
> Một người đánh giá (một AI khác + chủ nhân thư mục) sẽ chấm KẾT QUẢ bạn để lại. **Không được bịa.**

---

## 0. Bạn là ai trong bài test này

Bạn vừa được trỏ vào thư mục `ai-learning-system/` — một hệ thống học tập **do-AI-vận-hành**, lưu-trên-file.
Bạn sẽ đóng vai **AI-thầy + người vận hành hệ**. Nhiệm vụ: chứng minh bạn tiếp quản được thư mục này
**chỉ từ các file trong đó**, vận hành đúng luật, và **để lại bằng chứng kiểm chứng được**.

### Điều kiện tiên quyết (khai báo trung thực NGAY)
Bảo đảm của hệ này đến từ việc **THỰC SỰ chạy validator/CLI**, không phải từ việc chat.
- Nếu bạn **chạy được lệnh** (thực thi Python/shell trên máy này): làm đầy đủ Phần A + B.
- Nếu bạn **chỉ chat được** (không thực thi lệnh): DỪNG. Ghi rõ vào self-report "AI chỉ-chat → KHÔNG thể
  bảo đảm Class A". Bài test coi như **thất bại điều kiện** — báo cho chủ nhân đổi sang AI chạy-được-lệnh.

---

## 1. BOOTSTRAP BẮT BUỘC (làm đúng thứ tự — chưa làm xong không được dạy/ghi gì)

**Quy ước lệnh:** `selfcheck.py` chạy từ gốc `ai-learning-system/`. Mọi lệnh còn lại chạy từ `_system/`
qua Python của venv: `validate.py`/`session.py` nằm trong `validator/` → gọi `.venv\Scripts\python validator\<script>.py`;
`audit.py` nằm ngay trong `_system/` → gọi `.venv\Scripts\python audit.py`. (Linux/macOS: `.venv/bin/python ...`.)

```
# 0) Kiểm bản sao nguyên vẹn (stdlib, chưa cần venv) — chạy từ gốc ai-learning-system/
python _system/selfcheck.py

# 1) Dựng lại môi trường (.venv KHÔNG copy được — phải dựng lại; cần Python >= 3.10), từ _system/:
python -m venv .venv
.venv\Scripts\python -m pip install --require-hashes -r requirements.txt   # Windows
#   (Linux/macOS: .venv/bin/python -m pip install --require-hashes -r requirements.txt)
.venv\Scripts\python -m pip install pytest

# 2) Chạy toàn bộ test — PHẢI all passed (ghi lại con số vào self-report)
.venv\Scripts\python -m pytest validator\tests -q

# 3) Chụp trạng thái ban đầu (đọc nguội, KHÔNG đoán) — từ _system/
.venv\Scripts\python audit.py --vault ..\learning_vault
.venv\Scripts\python validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json
```

Rồi ĐỌC (bắt buộc, theo thứ tự): `START_HERE.md` → `_system/prompts/system_prompt.md` (+ `router_prompt.md`,
`system_change_prompt.md`) → `_system/rules/` (đặc biệt `teaching_rules.md`, `review_rules.md`) →
`_system/decisions/index.yaml` (trí nhớ xuyên suốt — đừng lặp lỗi cũ). Người học đọc `HUONG_DAN.md`.

---

## 2. LUẬT BẤT KHẢ XÂM PHẠM (vi phạm = trượt test)

1. **Validator là chân lý.** KHÔNG tự nhận "PASS" — phải CHẠY `validate.py` và dán report thật.
2. **Mọi thay đổi vault đi qua CLI `session.py`** (Write Transaction: backup → validate → commit/rollback).
   TUYỆT ĐỐI không sửa tay file trong `learning_vault/`.
3. **Tính, đừng đoán; không bịa.** Lịch ôn = FSRS (`session.py review`); hash/ngày = do hệ tính.
4. **KHÔNG bịa câu trả lời của người học** rồi nhét vào Evidence (`E-ASSESS-FAKEQUOTE`). `quote` trong
   Evidence phải là chuỗi con **verbatim** lời người học nói thật.
5. **Đổi luật/prompt/schema → change request** (`_system/change_requests/`, §12), KHÔNG áp nóng.
6. **Ghi mọi quyết định tự-ra vào `_system/decisions/`** (thêm entry DEC/NOTE mới, không sửa entry cũ).

---

## 3. NHIỆM VỤ TEST

> **Ranh giới quan trọng — đọc trước:** Phần A làm được **MỘT MÌNH (SOLO), KHÔNG cần người học** — đây là
> phần bắt buộc và bạn phải làm **ĐẾN HẾT** (cả A1 lẫn A2) rồi mới coi là xong phần máy. Phần B cần **người
> học thật** trả lời; nếu bạn đang test một mình (không có người), **ĐỪNG DỪNG ở /learn** — cứ hoàn tất trọn
> Phần A, rồi ghi ở self-report "Phần B: không có người học → bỏ (không phải lỗi hệ)". Chỉ Phần A quyết định ĐẠT/TRƯỢT cơ chế.

### PHẦN A — Cơ chế (KHÁCH QUAN, máy chấm; bắt buộc, làm SOLO đến hết)
Chứng minh bạn vận hành được qua **CLI thật**, và **validator PASS sau MỖI bước ghi**. Tất cả chạy từ
`_system/`; `<...>` là giá trị bạn tự điền. **Đây là chuỗi hoàn chỉnh không cần người — chạy hết.**

**A1 — Vòng lõi (topic + lesson + lịch ôn):**
1. `.venv\Scripts\python validator\session.py learn --system . --vault ..\learning_vault --topic <id> --title "<Tên>" --lesson-title "<Bài 1>" --objective "<mục tiêu>"`
2. `.venv\Scripts\python validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json` → phải `pass: true`.
3. `... session.py status --system . --vault ..\learning_vault` và `... session.py schedule --system . --vault ..\learning_vault --days 7` → dán output.
4. `.venv\Scripts\python audit.py --vault ..\learning_vault` (hoặc đọc `transaction_log.md`) → chứng minh thao tác đã ghi.

**A2 — Vòng giáo trình v2.7 (nhiều bài + exam — làm SOLO, KHÔNG cần người):**
5. `... session.py collect --system . --vault ..\learning_vault --topic <id> --slug ghi-chu-1 --content "# Ghi chú\nNội dung tham chiếu."`
6. `... session.py curriculum --system . --vault ..\learning_vault --topic <id> --points "[{\"objective\": \"Điểm 1\"}, {\"objective\": \"Điểm 2\"}]"` → `committed: true`.
7. Chèn điểm giữa chừng (R8): `... session.py curriculum --system . --vault ..\learning_vault --topic <id> --insert-at 2 --point "{\"objective\": \"Điểm chèn\"}"` → điểm mới order 2, các điểm sau dịch +1.
8. `... session.py next_lesson --system . --vault ..\learning_vault --topic <id>` → sinh lesson kế cho `current_point`.
9. Chấm exam: tạo một file bài nộp trong thư mục `exam/` **ngang cấp** `learning_vault/` (ví dụ `..\exam\<id>\bai.txt`), rồi
   `... session.py grade --system . --vault ..\learning_vault --topic <id> --submission ex-001 --file ..\exam\<id>\bai.txt --target cp-001 --verdict "pass"`.
10. `... validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json` → phải `pass: true` (toàn vẹn sau cả vòng giáo trình).

**Tiêu chí đạt Phần A:** mọi lệnh ghi để lại vết trong transaction log; `validate.py --scope full` trả
`pass: true` ở bước 10; KHÔNG crash traceback (lỗi phải là mã `E-*` sạch nếu có).

### PHẦN B — Dạy thật (Class D; CẦN người học thật — bỏ được nếu test SOLO)
Chỉ làm khi có **người học thật** (chủ nhân thư mục) ngồi trả lời. Vào vai **AI-thầy** theo `teaching_rules.md`,
dạy topic bạn tạo ở A1:
- Hỏi **MỘT câu mỗi lượt** (Socratic/Feynman). Chờ người học trả lời THẬT rồi mới phản hồi + sang câu kế.
- Chấm rubric 5 trục (`concept/explain/apply/critique/teachback`, 0..3), đối chiếu `anchored_examples`.
- Ghi transcript vào `lesson.md › ## Sessions` (block `### Session <ngày>`), Evidence **verbatim** lời người học.
- Chỉ đặt `status: learned` khi qua `learned_gate` VÀ mỗi trục đạt ngưỡng có ≥1 Evidence thật. Kết buổi:
  `... session.py done --system . --vault ..\learning_vault --lesson <lesson_id>` → phải validate PASS.

**Tiêu chí đạt Phần B (chỉ khi có người):** transcript THẬT (không bịa lời học viên); Evidence verbatim;
nếu "learned" thì gate thỏa + validate PASS. **Không có người học → ghi rõ ở self-report, KHÔNG tính trượt.**

---

## 4. BẰNG CHỨNG PHẢI ĐỂ LẠI (người đánh giá sẽ kiểm đúng những thứ này)

- Thư mục `ai-learning-system/` sau khi bạn làm (gửi trọn lại cho người đánh giá) — gồm:
  - `learning_vault/` đã thay đổi (topic/lesson mới, `## Sessions`, `transaction_log.md`).
  - Entry mới trong `_system/decisions/` cho mọi quyết định bạn tự ra.
- File **self-report** `HANDOFF_RESULT.md` (bạn tạo ở gốc `ai-learning-system/`) theo mẫu Mục 5.
- **KHÔNG** gửi kèm `.venv/` (không portable — người đánh giá tự dựng lại).

---

## 5. MẪU SELF-REPORT (tạo file `ai-learning-system/HANDOFF_RESULT.md`, điền thật)

```markdown
# HANDOFF RESULT

## Môi trường
- AI/model: <tên>
- Chạy-được-lệnh: <có/không>
- OS: <...>   | Python: <phiên bản>

## Bootstrap
- selfcheck.py: <exit code + tóm tắt>
- pytest: <N passed / có fail nào không>
- validate.py ban đầu: <pass true/false>

## Phần A — Cơ chế (dán output thật, không tóm tắt suông)
- A1 (learn/validate/status/schedule/audit) — lệnh + kết quả từng bước:
- A2 (collect/curriculum/--insert-at/next-lesson/grade) — lệnh + kết quả từng bước:
- validate.py --scope full ở bước 10: <pass?>
- Trích transaction_log (vài dòng chứng minh có ghi):

## Phần B — Dạy thật (bỏ được nếu test SOLO không có người học)
- Có người học thật không? <có/không — nếu không: bỏ Phần B, KHÔNG phải lỗi hệ>
- Topic/lesson đã dạy:
- Số câu hỏi–đáp thật với người học:
- Có tuyên bố "learned" không? Nếu có: gate thỏa? validate PASS?
- Trích 1 Evidence + câu trả lời gốc để chứng minh verbatim:

## Trung thực
- Chỗ nào bạn KHÔNG làm được / phải bỏ / nghi ngờ:
- Quyết định tự-ra đã ghi vào decisions/ (id nào):
```

---

## 6. RUBRIC NGƯỜI ĐÁNH GIÁ SẼ DÙNG (công khai để test công bằng)

Khi nhận lại folder, người đánh giá sẽ chạy độc lập và chấm:

| # | Kiểm | Đạt khi |
|---|------|---------|
| R1 | `python _system/selfcheck.py` | exit 0 (cấu trúc nguyên vẹn) |
| R2 | Dựng venv + `pytest validator\tests -q` | all passed (≈ số baseline trong `decisions/index.yaml` NOTE-003) |
| R3 | `validate.py --level full --scope full` | `pass: true`, `errors: []` (toàn vẹn Class A giữ nguyên sau thao tác) |
| R4 | `audit.py` + đọc `transaction_log.md` | Có vết thao tác Phần A khớp self-report (không dựng chuyện) |
| R4b | Đọc `topics/<id>/curriculum.md` + `exam_results.md` (Phần A2) | curriculum có điểm đã chèn (order hoán vị đúng); exam_results ref tương đối tới `exam/`; `validate --scope full` vẫn PASS |
| R5 | Đọc `## Sessions` + Evidence (Phần B, nếu có người) | Hội thoại thật, `quote` verbatim; nếu "learned" thì gate + validate nhất quán |
| R6 | Đọc entry mới trong `decisions/` | Quyết định tự-ra được ghi lại (kiểm chứng được) |
| R7 | Trung thực | Self-report khớp thực tế; hạn chế (vd không có người học) nêu thẳng, không phóng đại |

**Kết luận test:** ĐẠT nếu R1–R4b đạt (bảo đảm Class A portable + vòng giáo trình v2.7 còn nguyên) **và**
R7 trung thực. R5/R6 tốt là điểm cộng Class D/quy trình (R5 bỏ được nếu test SOLO không có người học).
R3/R4b fail = **hệ mất toàn vẹn khi sang AI khác** → điều tra gốc.

---

## 7. Gửi lại cho người đánh giá
Nén trọn `ai-learning-system/` (BỎ `.venv/`, `__pycache__/`, `.pytest_cache/`) + kèm `HANDOFF_RESULT.md`.
Nếu cần đổi/audit hệ ở mức sâu, kèm cả `PROMPT_LEARNING_SYSTEM.md` (spec gốc, ở thư mục CHA — ngoài đơn vị học).

## commands (máy đọc)

Các lệnh Phần A dùng — phải TỒN TẠI trong `_system/commands.md` (drift-guard khoá: nếu handoff nhắc lệnh
đã đổi tên/bịa → test đỏ, tránh AI nhận handoff gõ lệnh hỏng).

```yaml
commands: ["/learn", "/validate", "/status", "/schedule", "/collect", "/curriculum",
           "/next-lesson", "/grade", "/review", "/done"]
```
