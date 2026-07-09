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

## 6. Sub-quyết-định kiến trúc (KHUYẾN NGHỊ + lý do — owner VALIDATE, chưa chốt)

Đây là các lựa chọn nhỏ hơn QĐ-1/2/3, cần bạn duyệt trước khi lập spec. Mỗi cái nêu phương án + lý do chính xác.

### SD-1 — Hình thái đóng gói: Desktop app vs Local-web (localhost) vs TUI
| Phương án | Mô tả | Đánh đổi |
|---|---|---|
| **Local-web (localhost)** ⭐ | 1 tiến trình Python (orchestrator + kernel) phục vụ UI trên trình duyệt `localhost` | Nhúng kernel Python NGUYÊN BẢN (không cầu nối ngôn ngữ); local-first/privacy; UI cross-platform nhanh. Cần Python runtime (khắc phục: bundle PyInstaller/embeddable) |
| Desktop (Tauri/Electron) | Vỏ desktop + webview | Gọn hơn khi cài, nhưng THÊM tầng Rust/Node vẫn phải gọi kernel Python → 2 runtime, phức tạp hơn |
| TUI (terminal) | Giao diện dòng lệnh đẹp | Nhanh làm nhưng nhóm A (người học phổ thông) ngại terminal |

**Khuyến nghị: Local-web (localhost).** Lý do: kernel là Python → nhúng in-process là tự nhiên nhất (SD-2);
`localhost` giữ đúng ethos local-first/privacy (dữ liệu không rời máy); UI trình duyệt dựng nhanh, đa nền tảng.
Đánh đổi (cần Python trên máy) xử lý bằng đóng gói ở pha sau, KHÔNG chặn MVP.

### SD-2 — Cách nhúng kernel: subprocess CLI vs import in-process
**Khuyến nghị: IMPORT IN-PROCESS các hàm đã có** (`session.cmd_*`, `validate.validate_full_semantic`, ...).
Lý do CHÍNH XÁC (grounded, không đoán): đây **đúng API mà 520 test đang gọi** — test import `session as S` /
`validate as V` rồi gọi `S.cmd_learn(...) → (committed, report)`. Dùng lại đúng API đã-được-test = không tạo
hợp đồng mới, không phải parse lại JSON. Đánh đổi: orchestrator chung tiến trình với kernel → **ràng buộc:
orchestrator TUYỆT ĐỐI chỉ ghi vault qua hàm kernel (transaction), không bao giờ tự mở file vault** (chính là
INV-A2-2). Subprocess vẫn để dành cho biên cách ly nếu sau cần (vd chạy kernel version khác).

### SD-3 — LLM adapter: BYO-key vs local model
**Khuyến nghị: interface adapter mỏng, MVP dùng BYO-key, tùy chọn local model (Ollama).** Lý do: BYO-key →
bạn không gánh chi phí suy luận, người dùng tự kiểm soát; local model → privacy/offline trọn vẹn. Adapter
trừu tượng cả hai sau một interface (1 hàm `propose(prompt)->text`). **Ranh giới trung thực bắt buộc ghi cho
người dùng:** chất lượng DẠY (Class D) phụ thuộc model họ mang; sản phẩm đảm bảo TOÀN VẸN (Class A) bất kể
model, KHÔNG đảm bảo model dạy hay. Đây là điều kiện phân biệt "cái máy bảo đảm" vs "cái tùy LLM".

### SD-4 — Offline: cái gì chạy khi mất mạng
Kernel (validate/transaction/FSRS/review/schedule) **chạy hoàn toàn offline** (chỉ file local). Chỉ khâu
LLM sinh nội dung mới cần mạng (trừ khi dùng local model). ⇒ **Ôn tập (retention) chạy offline được**; chỉ
"học nội dung mới" cần LLM. Ghi rõ cho người dùng: mất mạng vẫn ôn được, chỉ không sinh bài mới (nếu BYO-key cloud).

## 7. Định nghĩa CHÍNH XÁC 2 metric QĐ-3 = C3 (proxy, KHÔNG phải "chứng minh hiểu")

> Ranh giới trung thực (nhắc lại): KHÔNG metric nào "chứng minh người học hiểu thật". M1 đo TÍNH TOÀN VẸN của
> cổng chốt; M2 đo ĐỘ BỀN GỢI NHỚ. Cùng nhau là PROXY MẠNH, máy-đo-được — khớp "validator là chân lý".

### M1 — Cổng-quá-trình (integrity lúc chốt "learned") — ĐÃ được kernel ép sẵn
- **Định nghĩa (đã hiện thực):** `status=learned` chỉ cấp khi `learned_gate` PASS: mỗi trong 5 trục
  (concept/explain/apply/critique/teachback) ≥ ngưỡng VÀ mỗi trục có ≥1 Evidence mà `quote` là **chuỗi con
  verbatim** của input THẬT người học (chống bịa `E-ASSESS-FAKEQUOTE`). Ép bởi `session.py done` (FULL-validate).
- **Metric sản phẩm (mới = PHƠI BÀY, không phải luật mới):** hiển thị trạng thái cổng như `/test` đã báo
  (trục nào đạt/thiếu, còn thiếu mấy Evidence). KPI: "tỉ lệ chốt-bài qua cổng ngay" + "trục hay tắc nhất".
- **Rủi ro/độ cứng:** M1 = **bất biến đã enforce** (vi phạm → transaction abort), KHÔNG phải KPI mềm. Điểm
  yếu đã biết: "phủ blueprint THÔ" (1 điểm phủ cả mảng lớn) → tinh chỉnh độ-sâu là hạng mục M1 tương lai
  (cần thiết kế riêng + có thể là INV mới qua change-request; KHÔNG làm ở MVP).

### M2 — Retention (độ bền theo thời gian) — TÍNH TỪ log FSRS sẵn có (read-only)
- **Định nghĩa:** từ `lesson_state.review_items[].log` (FSRS), tính:
  - `retention_rate(window)` = (số item ôn ĐÚNG [grade ≥ 2: good/easy] tại các mốc tới hạn trong cửa sổ) /
    (số item tới hạn & đã ôn trong cửa sổ), cho cửa sổ 7/30/90 ngày.
  - phụ trợ: tăng trưởng `stability` trung bình; số item đạt trạng thái `mastered`.
- **Tính chất:** chỉ báo TRỄ (cần ôn qua thời gian); tính **tất định, offline** từ dữ liệu đã có; KHÔNG cần
  INV mới → hiện thực an toàn dưới dạng **báo cáo CHỈ-ĐỌC** (khuôn như `audit.py`), rủi ro thấp.
- **Ranh giới:** M2 đo GỢI NHỚ (recall) — proxy của retention, KHÔNG phải "hiểu sâu".

**Hệ quả triển khai QĐ-3:** MVP KHÔNG cần INV mới hay đổi schema — M1 đã enforce; M2 là báo-cáo-đọc. Đây là
lý do C3 khả thi sớm mà không phá kernel.

## 8. Rủi ro + giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Đóng gói Python cho người dùng phổ thông | Trung bình | PyInstaller/python embeddable; pha đóng gói tách riêng, không chặn MVP |
| Chất lượng LLM dao động (Class D) | Cao (bản chất) | Ghi trung thực; đề xuất model tốt; cổng M1 đảm bảo TOÀN VẸN bất kể model |
| Orchestrator in-process làm hỏng vault | Cao nếu sai | Ép INV-A2-2: chỉ ghi qua hàm kernel/transaction; thêm test "orchestrator không mở file vault trực tiếp" |
| Scope creep (UI đẹp trước khi lõi vững) | Trung bình | Theo pha; Phase 1 headless trước, UI sau |
| Lệch "portable đa-AI" (MCP) | Thấp | MCP là kênh PHỤ (QĐ-2); kernel vẫn portable, thêm MCP sau không phá |

## 9. Kế hoạch validate theo pha (design-first → RED-first mỗi pha)

- **Phase 0 — Validate design (ĐANG Ở ĐÂY):** owner đọc DESIGN_A2 + duyệt SD-1..4 + định nghĩa M1/M2. CHƯA code.
- **Phase 1 — Orchestrator tối thiểu (headless):** 1 vòng dạy: LLM sinh câu hỏi → nhận trả lời THẬT → dựng
  Evidence verbatim → gọi kernel `done` → validate PASS. Spec + RED-first, có test ép INV-A2-1/2/3
  (đặc biệt: "learned" bị chặn nếu Evidence không verbatim / thiếu trục). Kernel 520 test GIỮ xanh.
- **Phase 2 — Báo cáo M2 retention (read-only):** tính từ log FSRS; teeth-test trên vault mẫu. Không đổi INV.
- **Phase 3 — UI localhost tối thiểu:** hiển thị hỏi-đáp 1-mỗi-lượt + trạng thái cổng M1 + KPI M2.
- **Phase 4 — LLM adapter (BYO-key) + đóng gói:** interface + 1 provider; bundling.
- Mỗi pha: spec → RED-first → verify (suite kernel xanh + validate PASS) → ghi nhật ký. Mọi thay đổi CHẠM
  kernel/registry/schema/spec → qua change-request §12.

## 10. Cái CẦN owner quyết trước khi sang Phase 1
1. Duyệt **SD-1 = Local-web**, **SD-2 = import in-process**, **SD-3 = BYO-key + optional local**, **SD-4** (offline scope) — hay đổi?
2. Duyệt định nghĩa **M1/M2** (proxy, không hứa "hiểu thật") — đủ/đúng chưa?
3. Chọn **hạng mục Phase 1 đầu tiên**: (a) orchestrator ép-kernel tối thiểu, hay (b) báo cáo M2 retention trước?

> Sau khi bạn duyệt §6–§10, tôi mới lập **spec triển khai** cho hạng mục đầu tiên rồi RED-first. Chưa code tới lúc đó.
