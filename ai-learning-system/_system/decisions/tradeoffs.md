# (3) Các Trade-off AI phải cân nhắc

Những chỗ có nhiều phương án hợp lệ, phải cân đo. Mỗi entry ghi rõ phương án bị loại + lý do chọn.
Entry `open-question` là điểm cần người dùng quyết trước khi đóng.

---

## TRD-001 — Tầng transaction tự viết vs. git / SQLite

```yaml
id: TRD-001
type: tradeoff
date: 2026-07-02
title: "Bespoke transaction (manifest markdown) vs dùng git/SQLite làm tầng ACID"
spec_ref: "spec mục 3 (dữ liệu là markdown thuần, portable, người-đọc-được, AI-sửa-được)"
summary: >
  Tầng ghi an toàn (transaction.py) được tự viết theo mô hình vault markdown + tombstone +
  validate-gate, thay vì mượn ACID có sẵn của git (mỗi commit atomic) hoặc SQLite.
alternatives:
  - "git-as-transaction: mỗi thao tác = commit atomic, có history sẵn — nhưng buộc mọi máy có git, và dữ liệu bị 'gói' trong repo."
  - "SQLite: ACID vững sẵn — nhưng mất tính markdown-thuần portable, người/AI khó đọc-sửa trực tiếp."
chosen: "bespoke transaction trên file markdown"
rationale: >
  Spec chốt dữ liệu phải là plain-text markdown mang đi máy khác, người & AI đọc-sửa trực tiếp.
  git/SQLite sẽ đổi mô hình lưu trữ (mất portable plain-text hoặc buộc phụ thuộc runtime).
  Đây là đánh đổi CÓ CHỦ ĐÍCH, không phải 'phát minh lại bánh xe' tuỳ tiện.
evidence:
  - "end.md: phân tích 'Tầng transaction/ACID ... tôi tự viết vì spec chốt dữ liệu phải là file markdown thuần'"
  - "repo_lab/repo_evaluations/fsrs.md (triết lý portable plain-text của dự án)"
verified: true
method: ran-test
status: active
owner_decision: "2026-07-04 (Q4=a): GIỮ transaction tự viết. Lý do chốt: atomicity đã AUDIT vững (NOTE-021: roll-forward đúng, 2 ranh giới an toàn khoá); portable thuần-file (INV-16, không phụ thuộc git/sqlite cài sẵn) — cốt lõi triết lý dự án; không có vấn đề thực tế cần đổi. open-question ĐÓNG."
reversible: >
  Nếu muốn đổi sang git-as-transaction: lập phiếu repo_lab/.../git.md (role: mechanism),
  so đánh đổi (portable vs history/độ phức tạp) rồi đổi qua change request. Quyết định hiện tại: GIỮ.
```

---

## TRD-002 — Chuẩn so tất định: `due_date` (ngày) vs `due_at_utc` (thời điểm)

```yaml
id: TRD-002
type: tradeoff
date: 2026-07-01
title: "Đổi độ chính xác so khớp lịch ôn để đạt tất định cross-platform"
spec_ref: "INV-08 / spec 8.3"
summary: >
  Chọn so theo ngày (due_date) thay vì so thời điểm UTC exact.
alternatives:
  - "due_at_utc exact: chính xác tới thời điểm — nhưng phụ thuộc float transcendental, không bit-khớp cross-platform → sai lệch giả."
  - "due_date (ngày): mất độ mịn giờ/phút — nhưng ổn định, tất định, kiểm chứng được."
chosen: "due_date (ngày)"
rationale: >
  Bản chất spaced-repetition là lịch theo NGÀY; độ mịn micro giây không mang giá trị học tập
  nhưng lại phá tất định. Chọn mức chính xác vừa đủ, ổn định. (Là mặt trade-off của DEV-002.)
evidence:
  - "repo_lab/repo_evaluations/fsrs.md: F-B + risks 'stability float → cross-platform boundary'"
verified: true
method: read-source
status: active
reversible: "Chỉ khi có API quantize-trước-due từ py-fsrs."
```

---

## TRD-003 — Enforce INV-17/18 bằng danh sách heuristic vs để trống

```yaml
id: TRD-003
type: tradeoff
date: 2026-07-03
title: "Danh sách tường minh (có thể sót/thừa) vs không enforce (sót hoàn toàn)"
spec_ref: "INV-17/18"
summary: >
  Chọn enforce bằng danh sách cụ thể thư mục/đuôi/tên + vùng loại trừ, chấp nhận khả năng
  danh sách chưa phủ hết mọi loại code/deps.
alternatives:
  - "Không enforce: an toàn khỏi bắt oan tuyệt đối — nhưng để lọt hoàn toàn (INV mồ côi)."
  - "Quét sâu ngữ nghĩa (đoán 'đây có phải code?'): phủ rộng — nhưng dễ bắt oan, vi phạm 'không suy đoán'."
  - "Danh sách tường minh + prune: cân bằng — phủ các trường hợp phổ biến, sai số kiểm soát được."
chosen: "danh sách tường minh + vùng loại trừ + os.walk prune"
rationale: >
  Danh sách rõ ràng cho phép kiểm chứng chính xác và mở rộng có kiểm soát; tránh phán đoán mơ hồ.
  Thà phủ chắc phần phổ biến hơn là đoán bừa.
evidence:
  - "validator/validate.py: _VAULT_FORBIDDEN_* / _SYSTEM_DATA_NAMES / _SYSTEM_SKIP_DIRS"
verified: true
method: read-source
status: active
reversible: "Bổ sung phần tử vào danh sách khi phát hiện loại mới; qua change request."
```

---

## TRD-004 — `pip install --require-hashes` (chặt) vs cài lỏng

```yaml
id: TRD-004
type: tradeoff
date: 2026-07-01
title: "Khoá dependency bằng hash để tái lập/bảo mật, đổi lấy khó rebuild trên Python khác"
spec_ref: "repo_lab/repo_evaluations/fsrs.md (role: install_dependency; lock_source: requirements.txt)"
summary: >
  Dùng requirements.txt có hash + cài bằng --require-hashes.
alternatives:
  - "Cài lỏng (không hash/không pin): dễ rebuild mọi nơi — nhưng mất tái lập & mở cửa supply-chain."
  - "--require-hashes + pin: tái lập bit-khớp, chống chèn gói độc — nhưng lock gắn với Python 3.11, khó rebuild trên 3.13 (xem NOTE-002)."
chosen: "--require-hashes + pin (chặt)"
rationale: >
  Sản phẩm thương mại cần tái lập và an toàn chuỗi cung. Chi phí là rebuild kém linh hoạt khi
  đổi phiên bản Python — chấp nhận được, xử lý bằng quy trình regenerate lock.
evidence:
  - "requirements.txt: header 'pip-compile --generate-hashes ... Python 3.11' + hash mọi gói"
  - "repo_lab/repo_evaluations/fsrs.md: 'lock_source: requirements.txt ... cài: pip install --require-hashes'"
verified: true
method: read-source
status: active
reversible: "Khi đổi Python: pip-compile lại (regenerate hashes) qua change request."
```

---

## TRD-005 — Kiểm `schema_version` NHẤT QUÁN CROSS-FILE vs. bám đúng phạm vi INV-19

```yaml
id: TRD-005
type: tradeoff
date: 2026-07-04
title: "Có nên ép mọi file (lesson/topic/sources).schema_version == vault_state.schema_version không?"
spec_ref: "INV-19 (spec dòng 689: CHỈ vault_state.schema_version vs _system/VERSION); §10.3b/10.7 (migration)"
summary: >
  Khi audit toàn vẹn version, phát hiện: validator CHỈ kiểm vault_state.schema_version vs system (INV-19);
  KHÔNG kiểm mỗi file (lesson_state/topic_state/sources) có cùng schema_version với vault. Về lý thuyết
  một file bị sửa tay lệch version sẽ được validator áp NHẦM luật version-hiện-tại (im lặng hiểu sai).
alternatives:
  - "A. Ép cross-file: mọi *_state/sources.schema_version PHẢI == vault_state.schema_version, lệch → E-SCHEMA-* (defense chống nửa-migrate/sửa tay)."
  - "B. Bám đúng INV-19: chỉ kiểm vault vs system; không thêm luật spec không viết."
chosen: "B (KHÔNG ép cross-file) — ở thời điểm này"
rationale: >
  INV-19 nói RÕ chỉ về vault_state vs _system/VERSION; spec KHÔNG liệt kê 'mọi file cùng version' như một
  bất biến. Migration (§10.3b) rewrite cả vault về version đích, nên trạng thái nghỉ hợp lệ ngầm-định là
  đồng version — nhưng đó là GIẢ ĐỊNH QUY TRÌNH, không phải INV tường minh. Theo bài học NOTE-012
  ('phân biệt under-enforce-so-với-spec vs spec-cố-ý-không-yêu-cầu'), thêm luật A = BỊA yêu cầu → không làm
  đơn phương. KHÁC open_session (DEC-031: INV-03 'MỌI tham chiếu' phủ rõ) và date_policy (DEC-030: triết lý
  strict + giá trị duy nhất) — hai cái đó có neo spec; còn cross-file version thì KHÔNG.
impact_if_wrong: >
  Rủi ro chỉ hiện thực khi người dùng SỬA TAY một file lệch version (hệ file cho phép). Thấp trong luồng
  bình thường (driver + migration luôn ghi đồng version). Nếu spec-owner muốn defense-in-depth → nâng thành
  INV mới qua change request rồi mới enforce (đúng kỷ luật §12), kèm mã lỗi + test RED-first.
recommendation_for_owner: "Quyết: có nâng 'cross-file schema_version consistency' thành INV chính thức không? Nếu có → tôi enforce ở validate_full_core + RED test."
owner_decision: "2026-07-04 (Q3): ĐỒNG Ý HOÃN. Chờ thiết kế P11 migration rõ (trạng thái pha-trộn version khi đang migrate có thể hợp lệ tạm thời → ép cross-file lúc này sẽ chặn nhầm). Xét lại sau khi có bước migration thật."
verified: true
method: read-source
status: open-question
reversible: "n/a (chưa triển khai; chỉ ghi nhận trade-off)"
```

## TRD-006 — Clone bulk 5 repo học vào folder vs nạp reference ON-DEMAND

```yaml
id: TRD-006
type: tradeoff
date: 2026-07-05
title: "Tải toàn bộ 5 repo (freeCodeCamp/free-programming-books/developer-roadmap/system-design-primer/project-based-learning) vào hệ vs chỉ kéo lát cắt liên quan khi học"
spec_ref: "none (đề xuất người dùng 'cài hết vào rồi chạy'); R1/R4/R2 của spec curriculum-driven-learning"
context: >
  Người dùng đề xuất clone hết 5 repo vào để 'dùng tối đa'. AI phân tích và CHỌN on-demand.
option_bulk:
  pros: ["offline sẵn toàn bộ", "không cần mạng khi dựng giáo trình"]
  cons:
    - "PHÁ INV-17: các repo chứa code/.git/manifest (freeCodeCamp là app, developer-roadmap TS/Astro, system-design-primer có Python) → E-MIX-CODE."
    - "PHÁ tính portable (INV-16 tinh thần): nặng hàng trăm MB, validate chậm, handoff nặng."
    - "Rủi ro bản quyền khi đóng gói nguyên repo (license đa dạng: BSD/CC-BY-SA/CC-BY-ND)."
    - "'Chạy' repo vô nghĩa: hệ là AI-dạy-hỏi text, không chạy app của họ."
option_ondemand (ĐÃ CHỌN):
  pros:
    - "Giữ INV-16/17: reference/ chỉ chứa .md trích đoạn liên quan, không .git/code."
    - "Nhẹ + portable; hợp lệ bản quyền (trích dẫn + ghi nguồn, không vendor bulk)."
    - "Tận dụng ĐÚNG thế mạnh mỗi repo (roadmap=thứ tự, free-programming-books=tài liệu, project-based-learning=đề exam, system-design-primer=nội dung sâu, freeCodeCamp=ý tưởng)."
  cons:
    - "Cần mạng lúc 'collect' (giảm thiểu: offline → lỗi sạch, không tạo curriculum rỗng — R1.5)."
    - "Không có toàn bộ nội dung offline (chấp nhận: chỉ cần trích đoạn liên quan topic)."
decision: "ON-DEMAND. Đăng ký repo vào sources.md (status raw) + kéo lát cắt markdown liên quan vào reference/<topic>/ khi dựng giáo trình."
verified: true
method: read-source
status: active
```

## TRD-007 — Coverage_Map đặt ở phía CURRICULUM (area_refs) vs phía BLUEPRINT (covered_by)

```yaml
id: TRD-007
type: tradeoff
date: 2026-07-07
title: "Ánh xạ phủ (mỗi Mandatory_Area ↔ Curriculum_Point) lưu ở đâu: CurriculumPoint.area_refs (bên sửa được) hay Blueprint.covered_by (bên khóa khi approved)?"
spec_ref: "mandatory-curriculum-framework R3.1/R3.5/R4.3; DEC-074 (QĐ-1); CR-0012; spec §3.6"
summary: >
  Coverage_Map là quan hệ 'mỗi Mandatory_Area bắt-buộc được phủ bởi ≥1 Curriculum_Point'. Phải lưu ánh xạ đó
  ở MỘT phía. Chọn đặt ở phía curriculum: thêm CurriculumPoint.area_refs: list[str]=[] (id các area mà point
  phủ).
alternatives:
  - "A. CurriculumPoint.area_refs (ĐÃ CHỌN): mapping ở phía curriculum — bên EDITABLE (curriculum sửa/chèn point tự do). Phủ = mỗi mandatory area id xuất hiện trong area_refs của ≥1 point."
  - "B. Blueprint.covered_by: [cp-ids]: mapping ở phía blueprint — nhưng R4.3 KHÓA blueprint khi approved. Mỗi lần sửa curriculum (thêm/chèn/đổi point) lại phải sửa blueprint approved → buộc --amend --confirm liên tục → xung đột khóa + phá ý nghĩa 'approved = chuẩn ổn định'."
chosen: "A — CurriculumPoint.area_refs (phía curriculum, editable)"
rationale: >
  Nguyên tắc gốc: đặt dữ-liệu-hay-đổi ở phía HAY ĐỔI (curriculum), không ở phía KHÓA (blueprint approved).
  R4.3 quy định blueprint approved là chuẩn ràng buộc, chỉ sửa qua bước có xác nhận; nếu mapping nằm trong
  blueprint thì mọi thao tác curriculum bình thường sẽ đụng blueprint approved → mâu thuẫn thiết kế. Đặt
  area_refs ở CurriculumPoint giữ blueprint 'thuần khung' (chỉ khai báo mảng), curriculum 'thuần phủ' (khai
  báo point nào phủ mảng nào) — phân tách trách nhiệm sạch. Toàn vẹn tham chiếu (area_refs trỏ area tồn tại)
  do Blueprint_Validator kiểm (E-BP-AREA-REF-BROKEN), KHÔNG nhét vào model (giữ mã lỗi phân biệt).
tradeoff_accepted: >
  Chi phí: phải mở rộng schema curriculum (thêm area_refs) qua CR-0012 → CHẠM vào tính năng
  curriculum-driven-learning ĐÃ hoàn tất. Giảm thiểu: field OPTIONAL default [] → curriculum cũ (không có
  key này) parse nguyên vẹn, mọi test/luồng cũ xanh (tương thích ngược tuyệt đối). Đánh đổi chấp nhận được
  vì phương án B tạo mâu thuẫn khóa nghiêm trọng hơn nhiều.
evidence:
  - "read-source: models.py CurriculumPoint.area_refs: list[str] = [] (dòng ~310, comment CR-0012 'Coverage_Map ... default [] tương thích ngược')"
  - "read-source: spec §3.6 dòng 229 'Coverage_Map ... đặt ở phía curriculum, qua CurriculumPoint.area_refs[] ... chứ không phải blueprint (bên khóa khi approved) để tránh xung đột khóa'"
  - "read-source: cr-0012-curriculum-area-refs.md (approved); changelog dòng cr-0012"
  - "ran-test (phiên này): 505 passed (bao gồm test_session_curriculum_arearefs +5)"
verified: true
method: read-source
status: active
reversible: "Đảo sang B: gỡ area_refs khỏi CurriculumPoint + thêm covered_by vào Blueprint + chuyển logic phủ trong _check_blueprint sang đọc blueprint-side. Nhưng sẽ tái tạo xung đột khóa R4.3 → không nên."
```

## TRD-008 — Áp khung lên curriculum ĐÃ teachable: GHI NHẬN ràng buộc (blueprint-first) vs XÂY lệnh retrofit area_refs

```yaml
id: TRD-008
type: tradeoff
date: 2026-07-07
title: "Phát hiện giới hạn workflow (xem NOTE-039): không có lệnh gắn area_refs vào Curriculum_Point ĐÃ CÓ → có nên xây lệnh retrofit ngay không?"
spec_ref: "mandatory-curriculum-framework R2 (dựng khi bắt đầu topic)/R5.4 (backward-compat)/R7.1 (lệnh mới qua CR); NOTE-039; DEC-075"
summary: >
  Truy vết luồng (NOTE-039) cho thấy: nếu một topic đã có curriculum teachable KHÔNG mang area_refs TRƯỚC, thì
  về sau KHÔNG approve được blueprint lên topic đó (E-BP-POINT-OUTSIDE + E-BP-AREA-UNCOVERED) và KHÔNG có lệnh
  nào gắn area_refs vào point đã có (cmd_curriculum từ chối nếu curriculum tồn tại; cmd_curriculum_insert chỉ
  THÊM point mới). Chỉ đi được luồng blueprint-first. Câu hỏi: xây lệnh retrofit ngay, hay ghi nhận ràng buộc?
alternatives:
  - "A. GHI NHẬN ràng buộc (ĐÃ CHỌN — ở thời điểm này): tài liệu hoá 'blueprint-first là luồng được hỗ trợ' (dựng blueprint → approve/draft → dựng curriculum có area_refs → dạy). ZERO code, an toàn tuyệt đối."
  - "B. XÂY lệnh retrofit: thêm năng lực gắn/sửa area_refs cho Curriculum_Point đã có (vd /curriculum --set-area-refs cp-XXX <area-ids>) → cho phép luồng curriculum-first rồi áp-khung-về-sau."
chosen: "A — GHI NHẬN ràng buộc (blueprint-first), CHƯA xây retrofit"
rationale: >
  Ba lý do CHÍNH XÁC (không phóng đại): (1) KHÔNG có gì hỏng — validator ép ĐÚNG bất biến R3/R5 (đã probe xác
  nhận ở phiên trước); đây là THIẾU NĂNG LỰC, không phải bug. (2) KHÔNG vi phạm requirements — R5.4 (no-blueprint
  / draft → hành vi cũ) vẫn giữ; R2 mô tả dựng blueprint 'khi bắt đầu topic' (blueprint-first là luồng chính
  spec hình dung); KHÔNG requirement nào bắt buộc retrofit. (3) vault ship RỖNG (DEC-054) → KHÔNG người dùng
  thật nào đang bị kẹt; luồng blueprint-first đã giao đủ giá trị cốt lõi (E2E DEC-074 Wave 7 chứng minh).
  Thêm lệnh mới = mở rộng scope, và R7.1 BẮT BUỘC qua CR được duyệt → là quyết định của owner, không tự thêm.
tradeoff_accepted: >
  Chi phí của A: người dùng đã lỡ dựng curriculum teachable trước rồi mới muốn áp khung sẽ vào ngõ cụt (phải
  xoá/dựng lại curriculum thủ công). Chấp nhận được vì vault rỗng khi ship + luồng đúng (blueprint-first) rẻ
  và tự nhiên. Nếu owner muốn hệ 'chống mọi thứ tự thao tác' (thương mại, nhiều người dùng có dữ liệu cũ) →
  chọn B: mở CR mới + SPEC-first (requirements bổ sung → design → tasks → RED-first) đầy đủ.
recommendation_for_owner: "Quyết: có nâng 'retrofit area_refs cho curriculum đã có' thành năng lực chính thức (phương án B) không? Nếu CÓ → tôi mở CR + thiết kế + kịch bản test chuẩn trước khi code. Nếu KHÔNG → giữ A (đã tài liệu hoá)."
evidence:
  - "read-source (phiên này): session.py cmd_curriculum '~L751 if cpath.is_file(): raise ... chỉ DỰNG mới' (từ chối ghi đè); cmd_curriculum_insert chỉ chèn point MỚI (không sửa area_refs point cũ)"
  - "read-source: KHÔNG có backend nào set area_refs trên point đã có (grep cmd_* — chỉ cmd_curriculum/cmd_curriculum_insert đọc area_refs từ JSON đầu vào)"
  - "cross-ref: NOTE-039 (phát hiện + root-cause đầy đủ); DEC-075 (phủ là cổng teachable)"
verified: true
method: read-source
status: open-question
reversible: "n/a (chưa triển khai gì; chỉ ghi nhận trade-off + chờ owner quyết B)"
```
