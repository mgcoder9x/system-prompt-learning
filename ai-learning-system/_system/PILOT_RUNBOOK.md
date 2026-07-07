# Pilot Runbook — Nghiệm thu bán-thủ-công P12 (người + AI + validator)

> Vì sao là runbook (không phải test tự động): P12 có phần **tất định** (đã tự động hoá — xem
> `validator/tests/phase12/`) và phần **phán đoán AI** (dạy thật, chấm rubric từ hội thoại, cross-AI
> handoff). Phần sau KHÔNG auto-test được — giả lập bằng code sẽ là **bịa**. Runbook này biến nó thành
> quy trình người+AI chạy được, có checkpoint validator thật. Bám Definition-of-Done của
> `implementation/PHASE_12_PILOT_E2E.md` + nhịp ngày §11B.

## 0. Ranh giới bảo đảm (đọc trước — §0.3, KHÔNG hứa quá)

- **Class A (validator đảm bảo tuyệt đối):** file tồn tại/schema/ngày/ID/tham chiếu/replay FSRS/view/
  index/transaction. Nếu `validate.py` PASS → các thứ này ĐÚNG 100%.
- **Class B/C (audit được, không phải chân lý):** claim bám nguồn/suy luận — validator chỉ xác nhận
  *liên kết tồn tại*, KHÔNG xác nhận nội dung đúng.
- **Class D (chỉ người kiểm):** "người học đã thật sự hiểu chưa", chất lượng chấm rubric — validator
  KHÔNG đảm bảo. Phòng tuyến cuối là **con người tự đọc transcript + tự chạy `validate.py`**.

## 1. Chuẩn bị môi trường (một lần)

Chạy trong thư mục `_system/`:

```text
python -m venv .venv
.venv\Scripts\python -m pip install --require-hashes -r requirements.txt
.venv\Scripts\python -m pip install pytest
.venv\Scripts\python -m pytest validator\tests -q        # kỳ vọng: toàn bộ PASS
```

Quy ước lệnh bên dưới: chạy từ `_system/`, `PY = .venv\Scripts\python`, vault ở `..\learning_vault`.
Mọi `--at` phải ISO-8601 **aware** (có offset), vd `2026-07-02T17:00:00+07:00`.

## 2. Kịch bản pilot — một topic thật (§11B)

Sau **mỗi bước GHI**, BẮT BUỘC chạy `/validate` FULL và **dán report nguyên văn** (không tự nói PASS).

```text
# (vào) trạng thái hiện tại
PY validator\session.py status  --system . --vault ..\learning_vault

# tạo topic mới (AI đã hỏi calibrate Q1–Q3 trong chat trước khi gọi lệnh)
PY validator\session.py learn   --system . --vault ..\learning_vault ^
     --topic docker --title "Docker" --lesson-title "Container là gì" ^
     --objective "Hiểu container giải quyết gì và khác máy ảo ra sao"
PY validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json

# (AI DẠY trong chat: First Principles → Feynman → Socrates → teach-back; hỏi MỘT câu/lượt)
#   → AI soạn evidence/claim vào lesson.md / lesson_notes.md theo §5.5 (draft nếu chưa nguồn)

# nạp nguồn (raw) rồi AI xử lý → confirmed + anchor trong chat/edit
PY validator\session.py source  --system . --vault ..\learning_vault ^
     --topic docker --ref "https://docs.docker.com/get-started/" --kind link --scope "lesson 1"
PY validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json

# ôn item tới hạn (chấm grade 0..3)
PY validator\session.py schedule --system . --vault ..\learning_vault      # xem due
PY validator\session.py review  --system . --vault ..\learning_vault ^
     --lesson docker/lesson-001 --item rv-001 --grade 2 --at 2026-07-02T17:00:00+07:00

# (ra) đóng sổ — transaction FULL
PY validator\session.py done    --system . --vault ..\learning_vault --lesson docker/lesson-001
```

**Checkpoint mỗi bước ghi:** `validate.py ... --json` → `"pass": true`. FAIL → đọc mã lỗi, sửa GỐC, KHÔNG bỏ qua.

## 3. Cross-AI handoff (bài test "stateless") — DoD PHASE_12

```text
1. Kết thúc "phiên AI 1" bằng /done (open_session.lesson_id = null).
2. Mở "phiên AI 2" (model/context MỚI). Chỉ cho đọc _system/ + learning_vault/. KHÔNG cung cấp lịch sử chat.
3. Phiên 2 chạy:  PY validator\session.py status  --system . --vault ..\learning_vault
   → PHẢI ra đúng: topic/lesson hiện tại + số câu due + cảnh báo open_session nếu có.
4. Phiên 2 chạy:  PY validator\session.py resume  --system . --vault ..\learning_vault
   → PHẢI tiếp đúng next_action mà KHÔNG hỏi lại từ đầu.
ĐẠT nếu phiên 2 tiếp tục đúng chỉ nhờ đọc file. TRƯỢT nếu phải hỏi lại → trạng thái chưa self-describing
→ bổ sung next_action/notes (KHÔNG vá bằng cách cho AI đoán — cạm bẫy PHASE_12).

> **[AUTO] Phần TẤT ĐỊNH của bài test này đã được tự động hoá** (`phase12/test_stateless_handoff.py`):
> phiên-1 `/resume` mở phiên → COPY vault sang **path tuyệt đối khác** (giả lập máy khác) → phiên-2 đọc
> nguội bằng `status`/`resume` khôi phục ĐÚNG topic/lesson + `open_session` + `next_action` (đã kiểm "có
> răng" bằng sentinel next_action round-trip). **Phần CÒN cần người:** đánh giá phiên-2 (AI/model khác) có
> DẠY TIẾP đúng nội dung không — Class D, validator không đảm bảo.
```

## 4. Kiểm chứng cam kết cốt lõi (thủ công lặp lại phần đã auto-test)

```text
# Determinism: chạy 2 lần, output --json phải GIỐNG HỆT
PY validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json > r1.txt
PY validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json > r2.txt
fc r1.txt r2.txt          # (Windows) phải "no differences"

# LƯU Ý (DEC-029): validate.py mặc định 'today' = ĐỒNG HỒ THẬT (INV-05: created <= updated <= today —
#   ngày lịch thật theo utc_offset, KHÔNG day_cutoff). Để audit TÁI LẬP TUYỆT ĐỐI (không lệ đồng hồ / không
#   lệ mốc nửa đêm), truyền --at cố định:
#   PY validator\validate.py --system . --vault ..\learning_vault --level full --scope full ^
#        --at 2026-07-02T17:00:00+07:00 --json

# Portability: copy learning_vault sang thư mục/máy khác rồi validate → vẫn PASS
#   (chứng minh INV-16: không đường dẫn tuyệt đối theo-máy)

# Chống giả mạo FSRS: sửa TAY due_date (hoặc stability) của 1 review item đã ôn → validate FULL
#   → PHẢI báo E-REVIEW-MISCALC. (LƯU Ý F-B: sửa due_at_utc của thẻ Review KHÔNG bị bắt — dùng due_date.)
```

## 5. Definition of Done (bám PHASE_12; [AUTO]=đã có test, [MANUAL]=chạy tay theo runbook)

```text
[AUTO]   validate sau mỗi lệnh ghi → PASS         (phase12/test_cli_loop_composition, test_p12_acceptance)
[AUTO]   determinism: validate 2 lần giống hệt     (test_p12_acceptance::test_determinism_*)
[AUTO]   tamper due_date/last_reviewed → MISCALC    (test_p12_acceptance::test_tamper_*)
[AUTO]   portability: vault ở path khác → PASS      (test_p12_acceptance::test_portability_across_paths)
[AUTO]   claim/nguồn: B confirmed hợp lệ + ca âm     (test_e2e_claim_source)
[AUTO]   handoff (nền tất định): phiên-2 đọc nguội ở PATH KHÁC → status/resume khôi phục đúng
         topic/lesson + open_session + next_action   (test_stateless_handoff; teeth: sentinel)
[AUTO]   INV-05 updated<=today (chống state 'từ tương lai')  (phase07a_core/test_inv05_updated_today)
[MANUAL] cross-AI handoff (tầng DẠY): phiên 2 (AI/model khác) DẠY TIẾP đúng chỉ nhờ đọc file (mục 3 — cần 2 phiên AI thật)
[MANUAL] chất lượng dạy + chấm rubric (Class D)      (con người đánh giá; validator KHÔNG đảm bảo)
```

## 6. Lệnh dùng trong pilot

Drift-guard: mọi lệnh dưới đây phải tồn tại trong CLI thật (test `phase12/test_pilot_runbook.py`).

### pilot_commands (máy đọc)

```yaml
pilot_commands: [status, learn, source, schedule, review, done, resume, gaps, forget, validate]
```
