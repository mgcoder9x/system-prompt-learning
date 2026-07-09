# SPEC_PHASE1_ORCHESTRATOR — Bộ điều phối tối thiểu (headless)

> Trạng thái: **SPEC ĐỂ VALIDATE — CHƯA CODE.** Ngày: 2026-07-09. Máy: ENDGAME.
> Phương pháp: spec rõ → owner valid → RED-first → code. Ràng buộc gốc: DESIGN_A2 (QĐ-1=A, QĐ-2=A2,
> QĐ-3=C3; SD-1 local-web, SD-2 import in-process, SD-3 BYO-key, SD-4 offline-kernel; M1/M2). Kernel
> `_system/` GIỮ NGUYÊN. Tài liệu + code Phase 1 nằm NGOÀI cây governed (DEC-079) → KHÔNG đụng suite 520.

## 1. Mục tiêu & phi-mục-tiêu

**Mục tiêu Phase 1:** một module `orchestrator` **headless** (không UI, không mạng) chứng minh — bằng test —
rằng **chính sản phẩm** (không phải LLM) ép kernel: một "buổi dạy" tối thiểu nhận (câu hỏi, câu-trả-lời-người-học),
dựng Evidence **verbatim**, rồi CHỐT "learned" **CHỈ QUA kernel** và **CHỈ KHI kernel validate PASS**. Đây là
lời-hứa-cốt-lõi QĐ-2 biến thành code kiểm-được.

**Phi-mục-tiêu (Phase 1):** KHÔNG UI (Phase 3); KHÔNG LLM thật/mạng (Phase 1 dùng **LLM stub tất định inject**);
KHÔNG M2 retention (Phase 2); KHÔNG đóng gói (Phase 4); KHÔNG đổi kernel.

## 2. Bất biến → Requirement TESTABLE (đây là "kịch bản test chuẩn")

| ID | Bất biến (DESIGN_A2) | Requirement kiểm-được |
|---|---|---|
| **R-ORCH-1** | INV-A2-1 kernel-là-chân-lý-thực-thi | Orchestrator KHÔNG tự nhận "learned". "learned" chỉ đúng khi `session.cmd_done(...)` trả `committed=True` VÀ `report.ok()`. IF kernel trả `committed=False` → orchestrator SHALL báo not-learned + trả nguyên `report.errors` (không nuốt lỗi). |
| **R-ORCH-2** | INV-A2-2 (SỬA GỐC theo DEC-081 — trust model thật) | Orchestrator ĐƯỢC author NỘI DUNG DẠY (transcript + evidence trong `lesson.md`) — đó là vai AI hợp lệ (kernel KHÔNG có lệnh ghi nội dung dạy; `cmd_done` docstring: "việc AI trong phiên"). NHƯNG: (a) MỌI chuyển-trạng-thái (learned/done/advance) CHỈ qua lệnh kernel; (b) orchestrator SHALL KHÔNG tự set `lesson_state.status=learned` rồi bỏ qua `cmd_done`; (c) phán quyết "learned" CHỈ hợp lệ khi `cmd_done` COMMIT (FULL-validate PASS). Kernel là cổng, không phải thiện chí orchestrator. |
| **R-ORCH-3** | INV-A2-3 evidence là lời THẬT | Evidence đưa vào lesson SHALL có `quote` là **chuỗi con verbatim** của câu-trả-lời-người-học đã nhập. IF một evidence-đề-xuất (kể cả do LLM sinh) KHÔNG phải substring của input người học → orchestrator SHALL từ chối evidence đó (không đẩy vào lesson), KHÔNG tự sửa lời người học. |
| **R-ORCH-4** | Trung thực Class D | Orchestrator SHALL KHÔNG "chấm hộ" đạt-cổng khi chưa đủ điều kiện: quyết định learned/not do **kernel `done` (FULL-validate)** phán, orchestrator chỉ chuyển tiếp. |

> R-ORCH-1..4 phải ép bằng CODE + TEST, không bằng lời nhắc. Đây là "phần bản chất" của QĐ-2 + trục-1 QĐ-3 (M1).

## 3. Giao diện tối thiểu (đề xuất — owner valid)

```
class LLMStub(Protocol):            # Phase 1: tất định, KHÔNG mạng (Phase 4 thay bằng adapter thật)
    def propose_question(self, context) -> str: ...
    def propose_evidence(self, answer_text, axis) -> str: ...   # PHẢI được orchestrator kiểm verbatim

class TeachingSession:
    def __init__(self, vault, system, llm: LLMStub, at): ...
    def open(self, topic_id) -> None                 # gọi kernel cmd_learn/next_lesson nếu cần
    def ask(self) -> str                              # lấy câu hỏi từ llm (không ghi vault)
    def submit_answer(self, learner_text: str) -> None
        # ghi transcript vào lesson.md ## Sessions QUA kernel; dựng Evidence:
        #   với mỗi trục, lấy llm.propose_evidence → KIỂM substring(verbatim) trong learner_text
        #   → CHỈ giữ evidence verbatim; loại (và log) evidence không-verbatim (R-ORCH-3)
    def try_finalize(self) -> tuple[bool, "Report"]
        # gọi kernel session.cmd_done → trả (committed and report.ok(), report)  (R-ORCH-1/4)
```

- **LLM là dependency INJECTED** (Phase 1 = stub tất định) → test không cần mạng, tất định.
- Orchestrator KHÔNG có đường ghi file vault nào ngoài việc gọi `session.*` (R-ORCH-2).

## 4. Ánh xạ kernel (grounded — API đã được 520 test dùng)

| Việc orchestrator | Hàm kernel REUSE (in-process import) |
|---|---|
| Mở chủ đề/bài | `session.cmd_learn(...)` / `session.cmd_next_lesson(...)` → `(committed, report)` |
| Ghi nội dung buổi dạy + evidence | ghi qua đường lesson do kernel kiểm (transaction) — KHÔNG mở file trực tiếp |
| Chốt learned | `session.cmd_done(...)` → `(committed, report)` (FULL-validate: gate INV-07 + E-ASSESS-FAKEQUOTE) |
| Xác nhận toàn vẹn | `validate.validate_full_semantic(...)` đọc `report.ok()` |

> Lưu ý thiết kế cần chốt ở spec-review: cách orchestrator ĐƯA evidence/transcript vào lesson.md để `cmd_done`
> kiểm — hoặc (a) orchestrator tự author lesson.md ## Sessions rồi cmd_done validate, hoặc (b) kernel cần một
> điểm-vào ghi-evidence. Phase 1 CHỌN (a) nếu khả thi KHÔNG đổi kernel; nếu (a) đòi đổi kernel → dừng, mở
> change-request §12 (KHÔNG sửa nóng kernel). Đây là điểm RỦI RO cần kiểm TRƯỚC khi code (xem §6).

## 5. Kịch bản test RED-first (viết trước, phải ĐỎ khi chưa có orchestrator)

1. `test_finalize_requires_kernel_commit` — kernel `done` trả committed=False (gate fail giả lập) → `try_finalize()` trả `(False, report)` với `report.errors` nguyên vẹn (R-ORCH-1/4).
2. `test_happy_path_learned` — input người học đủ 5 trục + evidence verbatim → `try_finalize()` trả `(True, report)` + `validate_full_semantic` PASS (R-ORCH-1).
3. `test_reject_non_verbatim_evidence` — llm.propose_evidence trả chuỗi KHÔNG có trong answer → evidence bị loại; lesson KHÔNG chứa quote bịa; nếu cố đẩy → `E-ASSESS-FAKEQUOTE` khi validate (R-ORCH-3).
4. `test_orchestrator_never_writes_vault_directly` — sau buổi dạy, tập file vault đổi == tập file trong transaction_log (không có ghi ngoài-transaction) (R-ORCH-2).
5. `test_deterministic_no_network` — chạy 2 lần với cùng LLMStub + cùng `at` → cùng kết quả (tất định, offline).

> Teeth: mỗi test kỳ-vọng-chặn phải ĐỎ nếu orchestrator thiếu cơ chế ép (vd bỏ kiểm verbatim → test 3 đỏ).

## 6. Rủi ro PHẢI kiểm TRƯỚC khi code (spec-review gate)

- **R1 — ĐÃ GIẢI (DEC-081, đọc code thật):** author `lesson.md` (## Sessions + transcript + 1 evidence/trục,
  quote ⊆ transcript) + `lesson_state`(status=learned+mastery) TRỰC TIẾP rồi `cmd_done` FULL-validate là ĐỦ —
  **KHÔNG đổi kernel** (bằng chứng: test `_make_lesson_learned` làm đúng vậy, PASS). Cải tiến "ghi nội dung dạy
  transactional" là kernel-change tương lai qua CR §12, NGOÀI scope Phase 1.
- **R2 — Vị trí code:** `product/orchestrator/` (mới, NGOÀI `ai-learning-system/` kernel) + test-suite RIÊNG →
  KHÔNG đụng suite 520 của kernel. Kernel import qua sys.path (như test hiện có).
- **R3 — Không tự-fetch mạng** (đúng ethos): LLM stub Phase 1; adapter thật Phase 4.

## 7. Tiêu chí ĐẠT Phase 1

- 5 test §5 xanh (RED→GREEN, teeth-verified).
- Suite kernel **vẫn 520 passed** (orchestrator test tách riêng, không đụng governed tree).
- `validate --scope full` trên vault dùng-thử → pass:true (orchestrator không làm hỏng toàn vẹn).
- Không có đường ghi vault nào ngoài kernel (R-ORCH-2 test xanh).
- KHÔNG đổi kernel; nếu buộc phải đổi → đã đi qua change-request §12.

## 8. Cần owner VALIDATE trước khi RED-first
1. Duyệt **giao diện §3** (TeachingSession + LLMStub inject) — hay đổi hình dạng?
2. Duyệt **§4 lưu ý (a)**: orchestrator tự author lesson.md rồi `cmd_done` validate (KHÔNG đổi kernel) — đồng ý hướng này? (Nếu phải đổi kernel → tôi mở CR trước.)
3. Duyệt **vị trí code `product/orchestrator/`** tách khỏi kernel.

> Sau khi bạn duyệt §8, tôi sẽ: (1) đọc `cmd_done`/luồng evidence THẬT để chốt R1 (không đoán), (2) viết 5 test
> RED-first, (3) code orchestrator tối thiểu cho tới GREEN, (4) verify suite kernel vẫn 520 + validate PASS,
> (5) ghi nhật ký. Chưa đụng code tới lúc đó.
