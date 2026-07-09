# PRODUCT_THESIS — Quyết định luận đề sản phẩm (giữ kernel / cắt / thêm)

> Trạng thái: **BẢN NHÁP ĐỂ QUYẾT ĐỊNH** — chưa chốt. Ngày lập: 2026-07-09.
> Mục đích: quyết luận đề sản phẩm TRƯỚC khi viết thêm code, đúng nguyên tắc
> "thiết kế rõ → valid thiết kế → mới triển khai". Đây là tài liệu chiến lược,
> KHÔNG phải nhật ký quyết định kỹ thuật (`_system/decisions/`) và KHÔNG phải spec.
> Đối chiếu tiền lệ: `ai-learning-system/_system/repo_lab/repo_evaluations/similar_systems_landscape.md`.

---

## 1. Vấn đề gốc (không phải vấn đề code)

Hệ hiện tại là **một kernel toàn vẹn xuất sắc đang đi tìm một sản phẩm**.

- Kiến trúc hôm nay tối ưu cho mục tiêu: *"substrate học-tập portable, do-AI-vận-hành, chứng minh được toàn vẹn"*.
- Mục tiêu bạn vừa nêu: *"sản phẩm thương mại, lâu dài"*.

Hai mục tiêu này **lệch nhau** ở 3 điểm. Đây là thứ phải quyết — không phải "viết lại code".
**Đập đi xây lại là sai**: nó phá đúng phần khó & hiếm nhất (tầng toàn vẹn + governance) mà không giải
được bất kỳ điểm lệch nào ở dưới.

---

## 2. Sự thật nền (đã kiểm chứng, không phỏng đoán)

- Quy mô: ~519 test / 85 file / ~6.400 dòng test; spec 1.236 dòng; ~11 module lõi; 8 schema; 6 bộ luật;
  transaction engine; 15 lệnh CLI; 133 entry nhật ký quyết định. → Hệ **trưởng thành**, không phải prototype.
- Phần khác biệt = **tầng toàn vẹn (Class A) + governance/anti-drift**. FSRS và markdown-SR là **commodity**.
- Bằng chứng thị trường: vestige (bộ nhớ AI-agent, FSRS, portable qua MCP) có 579 stars, 28 release →
  thị trường "portable AI cognition" là thật. Nhưng **ô "DẠY-HỌC có cổng hiểu" vẫn trống**.

---

## 3. Ba quyết định GỐC phải chốt (kèm phương án + lý do chính xác)

### QĐ-1 — NGƯỜI DÙNG MỤC TIÊU là ai?

Đây là quyết định mẹ; hai quyết định sau phụ thuộc nó.

| Phương án | Mô tả | Hệ quả |
|---|---|---|
| **A. Người học cuối** (học sinh/sinh viên/tự học) | Sản phẩm dạy–học trực tiếp | Bắt buộc có UI; KHÔNG được phụ thuộc "AI có chịu chạy CLI"; chất lượng DẠY (Class D) phải đo được |
| **B. Dev / AI-agent** (giống vestige) | Bán "substrate học/nhớ" cho hệ khác nhúng | Giữ CLI-first; khác biệt hoá bằng tầng toàn vẹn; phân phối qua MCP/thư viện |
| **C. Kép** | Kernel B ở dưới, sản phẩm A ở trên | Rủi ro dàn trải; chỉ nên khi kernel đã đóng băng ổn định |

**Khuyến nghị: A, nhưng xây trên kernel hiện có (không rebuild).** Lý do:
ô dạy–học-có-cổng-hiểu đang trống (khác biệt rõ so với vestige/markdown-SR);
và giá trị người dùng trả tiền là "tôi học VÀO", không phải "dữ liệu toàn vẹn" (toàn vẹn là điều kiện cần, không phải điểm bán).

> **✅ QĐ-1 ĐÃ CHỐT (2026-07-09): A — Người học cuối (end learners).** Owner chọn qua user_input.
> Ghi nhận ở nhật ký: NOTE-043. Hệ quả kích hoạt (bắt buộc trước khi build sản phẩm):
> (i) **QĐ-2 trở thành nút thắt kế tiếp** — phải giải rủi ro gốc "bảo đảm phụ thuộc AI chịu chạy CLI"
> (end-learner không kiểm soát được AI của họ) → hướng MCP/service; (ii) cần lớp UI; (iii) QĐ-3
> (đo được chất lượng DẠY / Class D) là hạng mục đầu tư giá trị-cốt-lõi. Kernel GIỮ nguyên, không rebuild.

### QĐ-2 — CƠ CHẾ ĐẢM BẢO: "AI chạy CLI" hay "service/MCP"?

**Rủi ro gốc hiện tại (trích chính START_HERE):** *"AI chỉ-chat sẽ chỉ mô phỏng → mất bảo đảm."*
Nghĩa là mọi bảo đảm Class A **phụ thuộc việc AI chịu thật sự chạy validator**. Với sản phẩm thương mại,
bạn KHÔNG kiểm soát được điều đó ở phía người dùng. **Không vá bằng thêm test được** — đây là kiến trúc.

| Phương án | Mô tả | Đánh đổi |
|---|---|---|
| **Giữ CLI + mồi thủ công** | Như hiện tại | OK cho nghiên cứu/dev; KHÔNG ổn cho người dùng cuối |
| **Đóng gói thành SERVICE** | Validator/transaction chạy phía bạn (local app hoặc backend); AI chỉ gọi | Bảo đảm không còn phụ thuộc thiện chí của AI; cần công sức đóng gói |
| **Phơi qua MCP** (bài học vestige) | Kernel thành MCP server; agent nào cũng gọi tool được, tự động | Chuẩn phân phối 2026; giải đúng rủi ro gốc; vẫn giữ được "portable qua mọi AI" |

**Khuyến nghị: MCP (hoặc service có API) bọc quanh kernel.** Lý do:
vestige là bằng chứng trực tiếp rằng "portable qua mọi AI" ship được, tự động, bằng MCP — đúng thứ ta đang làm thủ công.
Kernel Python + CLI hiện tại **không phải bỏ**: nó trở thành lõi được MCP/service gọi.

> **✅ QĐ-2 ĐÃ CHỐT (2026-07-09): A2 — App local-first nhúng kernel làm SERVICE tin cậy + tự điều phối LLM.**
> Owner chọn qua user_input. Ghi ở NOTE-044. Tinh chỉnh so với khuyến nghị "MCP/service" ban đầu: cho nhóm
> A (người học cuối) thì **SERVICE do-sản-phẩm-chạy** là cốt lõi (validator/transaction luôn chạy, không
> phụ thuộc AI người dùng), local-first giữ privacy/markdown-portable (ethos = moat); **MCP là kênh PHỤ**
> cho power-user, KHÔNG phải sản phẩm chính (người học phổ thông không dùng client MCP). Cloud SaaS bị loại
> ở bước này (đánh đổi local-first/privacy + hạ tầng). Kernel GIỮ nguyên; chỉ BỌC (UI + orchestrator + LLM
> adapter). Chi tiết kiến trúc A2 sẽ dựng ở design doc riêng SAU khi chốt nốt QĐ-3.

### QĐ-3 — Biến CHẤT LƯỢNG DẠY (Class D) từ "tùy AI" thành ĐO ĐƯỢC

Nghịch lý hiện tại: 519 test bảo vệ *toàn vẹn dữ liệu*, nhưng thứ người học trả tiền —
*"tôi có hiểu không"* — lại là Class D, máy KHÔNG đảm bảo. **Sản phẩm phải mạnh nhất đúng chỗ hệ đang yếu nhất.**

Hướng (cần thiết kế riêng, chưa chốt):
- Rubric chấm hiểu có đối chứng + chống bịa dẫn chứng (đã có mầm: E-ASSESS-FAKEQUOTE).
- "Property test cho tiến trình học": ví dụ *không được đánh dấu learned nếu chưa có dẫn chứng verbatim qua đủ trục*; *độ phủ blueprint phải đo cả độ sâu, không chỉ ánh xạ 1-điểm* (điểm yếu "phủ thô" đã ghi nhận).
- Thang đo giữ chân/tái hiện (retention thực đo qua FSRS) làm KPI sản phẩm.

**Khuyến nghị:** coi QĐ-3 là **hạng mục đầu tư mới quan trọng nhất** cho bản thương mại. Đây là nơi tạo giá trị,
và cũng là nơi hệ hiện hở.

> **✅ QĐ-3 ĐÃ CHỐT (2026-07-09): C3 — Cả hai (cổng-quá-trình + kết-quả-lưu-giữ).** Owner chọn qua user_input.
> Ghi ở NOTE-045. Cụ thể 2 trục ĐO ĐƯỢC (proxy, KHÔNG phải "chứng minh hiểu thật" — ranh giới trung thực):
> (1) **Cổng-quá-trình (lúc chốt bài):** "learned" chỉ được cấp khi có dẫn chứng verbatim (lời THẬT của
> người học) qua đủ 5 trục hiểu + chống bịa (E-ASSESS-FAKEQUOTE) — máy ép, không do LLM tự nhận.
> (2) **Kết-quả-lưu-giữ (theo thời gian):** KPI = tỉ lệ nhớ đúng ở các mốc ôn FSRS (retention). Cả hai
> máy-đo-được, khớp ethos "validator là chân lý". Chi tiết định nghĩa metric + cách enforce → design doc.

---

## 4. GIỮ / DÙNG LẠI / QUYẾT LẠI / CẮT / ĐẦU TƯ

| Nhóm | Hạng mục | Hành động | Lý do |
|---|---|---|---|
| **GIỮ (tài sản, đừng động)** | vault markdown, validator/INV, transaction, decision journal, anti-drift, change-request | Đóng băng thành **"kernel toàn vẹn" có version** | Đây là moat; có 519 test bảo vệ; rebuild = phá cái khó nhất, không thêm giá trị |
| **DÙNG LẠI (đừng tự viết)** | FSRS (py-fsrs) | Giữ nguyên | Chuẩn ngành; đã có phiếu đánh giá + lock hash |
| | Quy ước markdown-SR (hashcards/Decks) | Tham khảo nếu cần tương thích ngoài | Tránh phát minh lại |
| **QUYẾT LẠI (làm TRƯỚC khi code)** | QĐ-1/2/3 ở trên | Chốt với người ra quyết định | Luận đề sai thì code đúng cũng vô ích |
| **ĐẦU TƯ MỚI** | Lớp sản phẩm/UI (nếu QĐ-1=A) | Bọc lớp mỏng lên kernel | Đối thủ đều có; ta chưa |
| | MCP/service wrapper (QĐ-2) | Bọc kernel | Giải rủi ro gốc "phụ thuộc AI chạy CLI" |
| | Đo chất lượng dạy (QĐ-3) | Thiết kế riêng | Nơi tạo giá trị thương mại |
| **CẮT / HOÃN** | "Mồi thủ công cho AI đọc START_HERE" như CƠ CHẾ chính | Thay bằng MCP/service | Không dùng được cho người dùng cuối |
| | Đổi tên topic, các tiện ích vận hành nội bộ | Hoãn | Không phải đường tới hạn sản phẩm |

---

## 5. Rủi ro cần canh

1. **Dàn trải** nếu chọn QĐ-1=C quá sớm khi kernel chưa đóng băng.
2. **AGPL của vestige** — nếu định tham chiếu/nhúng bất kỳ phần nào, phải kiểm giấy phép (vestige = AGPL-3.0).
3. **Class D là bài toán khó thật** — đừng hứa "máy đảm bảo học vào"; hứa "đo được tiến trình", không hứa "đảm bảo hiểu".
4. **arXiv:2605.11032 chưa đọc toàn văn** — nếu đi hướng "portable+verifiable memory", đọc trước khi thiết kế protocol.

---

## 6. Bước tiếp theo

**✅ 3 quyết định gốc ĐÃ CHỐT (2026-07-09):** QĐ-1 = A (người học cuối) · QĐ-2 = A2 (app local-first nhúng
kernel làm service tin cậy + tự điều phối LLM) · QĐ-3 = C3 (cổng-quá-trình + retention). Ghi: NOTE-043/044/045.

**Kế tiếp (design-first, CHƯA code):**
1. Dựng **design doc kiến trúc A2 + đo QĐ-3** (`DESIGN_A2.md`): sơ đồ UI ↔ orchestrator ↔ kernel-as-trusted-
   service ↔ vault; trust boundary (mọi 'learned' phải qua validate PASS + evidence, do SẢN PHẨM ép);
   REUSE (kernel nguyên vẹn) vs NEW (UI/orchestrator/LLM-adapter); các SUB-quyết-định (đóng gói desktop vs
   local-web, nhúng Python kernel, BYO-key LLM, offline); định nghĩa CHÍNH XÁC 2 metric QĐ-3; rủi ro + kế
   hoạch validate theo pha.
2. Owner đọc + validate design (đúng phương pháp 'thiết kế rõ → valid → mới triển khai').
3. Chỉ **sau** khi design được duyệt → lập **spec triển khai** cho hạng mục đầu tiên (ứng viên: orchestrator
   ép-kernel tối thiểu, hoặc metric QĐ-3), rồi RED-first.

> Kernel `_system/` GIỮ nguyên (moat) — chỉ BỌC lớp ngoài. Tài liệu chiến lược (`PRODUCT_THESIS.md`,
> `similar_systems_landscape.md`, tương lai `DESIGN_A2.md`) nằm NGOÀI cây governed (DEC-079) nên không
> ảnh hưởng test suite (520 passed, verified 2026-07-09).
