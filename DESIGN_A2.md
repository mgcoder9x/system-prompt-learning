# DESIGN_A2 — Kiến trúc "App local-first nhúng kernel" + Đo chất lượng dạy (QĐ-3)

> Trạng thái: **BẢN THIẾT KẾ ĐỂ VALIDATE — CHƯA CODE.** Ngày: 2026-07-09.
> Phương pháp: design-first → owner đọc/valid → mới lập spec triển khai → RED-first.
> Ràng buộc gốc đã chốt (PRODUCT_THESIS §3; NOTE-043/044/045):
> **QĐ-1 = A** (người học cuối) · **QĐ-2 = A2** (app local-first nhúng kernel làm service tin cậy + tự
> điều phối LLM) · **QĐ-3 = C3** (cổng-quá-trình + retention). Kernel `_system/` GIỮ nguyên (moat).
> Tài liệu này nằm NGOÀI cây governed (DEC-079) → không ảnh hưởng test suite (520 passed).

## 1. Mục tiêu & phi-mục-tiêu

**Mục tiêu:** một ứng dụng cho NGƯỜI HỌC CUỐI, chạy local-first, trong đó **chính sản phẩm** (không phải
AI của người dùng) chạy kernel validator/transaction một cách tin cậy; LLM chỉ ĐỀ XUẤT nội dung dạy/hỏi,
còn mọi GHI trạng thái (đặc biệt "learned") phải đi qua kernel (validate PASS + evidence).

**Phi-mục-tiêu (ở pha này):** không rebuild kernel; không cloud SaaS; không MCP-first (MCP để pha sau, kênh
phụ); không hứa "máy đảm bảo hiểu thật" (chỉ đo proxy).

## 2. Bất biến cốt lõi (trust boundary) — điều KHÔNG được vi phạm

> **INV-A2-1 (Kernel-là-chân-lý-thực-thi):** Mọi thay đổi vault đi qua kernel transaction; sản phẩm gọi
> `validate.py`/`session.py` THẬT và đọc kết quả — KHÔNG để LLM "tự nhận PASS". Đây là bản dịch của
> "validator là chân lý" sang tầng sản phẩm: trước đây phụ thuộc AI tự giác chạy; nay ORCHESTRATOR ép chạy.

> **INV-A2-2 (LLM không có quyền GHI):** LLM chỉ sinh văn bản (câu hỏi, giải thích, đề xuất chấm). Việc
> ghi lesson/curriculum/blueprint/mark-learned do ORCHESTRATOR thực hiện QUA kernel, sau khi kernel validate.
> LLM không bao giờ chạm file vault trực tiếp.

> **INV-A2-3 (Evidence là lời THẬT của người học):** Dẫn chứng đưa vào cổng hiểu phải trích verbatim từ
> input người học (chống E-ASSESS-FAKEQUOTE). LLM không được bịa câu trả lời thay người học.

Ba bất biến này là "phần bản chất" giải QĐ-2 + trục 1 của QĐ-3. Chúng phải được ép bằng CODE (orchestrator +
kernel), không bằng lời nhắc LLM.

## 3. Sơ đồ thành phần (text)

```
┌──────────────────────────────────────────────────────────────────┐
│  UI (người học cuối) — chat học + bảng tiến độ/ôn tập              │  NEW
│   • hiển thị câu hỏi 1-mỗi-lượt, ô trả lời, lịch ôn, KPI retention │
├──────────────────────────────────────────────────────────────────┤
│  ORCHESTRATOR (bộ điều phối, "não sản phẩm")                      │  NEW
│   • vòng dạy Socratic: gọi LLM sinh câu hỏi → nhận trả lời THẬT    │
│   • chấm 5 trục (đề xuất bởi LLM) → dựng evidence verbatim         │
│   • GỌI KERNEL cho MỌI ghi (learn/curriculum/next-lesson/review/  │
│     done/grade/blueprint) — ép INV-A2-1/2/3                        │
│   • tính KPI QĐ-3 (M1 cổng, M2 retention) từ kết quả kernel        │
├───────────────┬──────────────────────────────┬───────────────────┤
│ LLM ADAPTER   │  KERNEL-AS-TRUSTED-SERVICE    │  VAULT (markdown) │
│ (BYO-key/     │  = _system/ hiện tại, NGUYÊN  │  learning_vault/  │
│  local model) │  VẸN: validate.py/session.py/ │  (dữ liệu người   │
│  NEW (mỏng)   │  transaction/FSRS  ← REUSE    │  học)  ← REUSE    │
└───────────────┴──────────────────────────────┴───────────────────┘
```

## 4. REUSE vs NEW (ranh giới rõ)

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| validator/ (INV, validate.py, session.py 15 lệnh) | **REUSE nguyên vẹn** | Là moat; 520 test bảo vệ |
| transaction engine, FSRS adapter, views, schemas, rules | **REUSE nguyên vẹn** | Không đụng |
| governance (change-request, decision journal, anti-drift) | **REUSE** | Tiếp tục dùng cho mọi thay đổi |
| vault markdown | **REUSE** | Local-first, privacy giữ nguyên |
| Orchestrator (vòng dạy + ép kernel + tính KPI) | **NEW** | Trái tim sản phẩm; nơi ép INV-A2-* |
| LLM adapter | **NEW (mỏng)** | Trừu tượng hoá nhà cung cấp; BYO-key |
| UI | **NEW** | Chat học + tiến độ + ôn |

## 5. Ánh xạ vòng dạy → lệnh kernel sẵn có (không cần lệnh mới ở pha đầu)

| Bước học | Lệnh kernel REUSE |
|---|---|
| Tạo chủ đề + bài đầu | `session.py learn` |
| Khung bắt buộc + duyệt | `session.py blueprint (--approve)` |
| Dựng/chèn/gắn giáo trình | `session.py curriculum (--insert-at / --set-area-refs)` |
| Sinh bài cho điểm hiện tại | `session.py next-lesson` |
| Chốt "learned" (cổng hiểu) | `session.py done` (FULL-validate) |
| Ôn theo lịch | `session.py review` + `schedule` |
| Toàn vẹn | `validate.py --scope full` sau mỗi ghi |

→ Orchestrator chủ yếu ĐIỀU PHỐI các lệnh này; giá trị mới nằm ở vòng dạy + đo lường, không ở việc thêm lệnh.
