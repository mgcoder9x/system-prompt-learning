# (4) Bất kỳ điều gì AI sau nên biết

Trạng thái, cạm bẫy môi trường, và việc còn dở. Đọc trước khi tiếp tục để không lặp lỗi/không đoán.

---

## NOTE-001 — ⚠️ `.venv` đang HỎNG do workspace bị di chuyển máy (verified phiên này)

```yaml
id: NOTE-001
type: note
date: 2026-07-03
title: ".venv trỏ interpreter của máy cũ (k.nguyen.manh.toan) → không chạy được trên máy hiện tại (toann)"
spec_ref: "n/a (vấn đề môi trường)"
summary: >
  Chạy `.venv\Scripts\python.exe` báo: No Python at
  'C:\Users\k.nguyen.manh.toan\AppData\Local\Programs\Python\Python311\python.exe'.
  Workspace hiện ở C:\Users\toann\... → venv không tái định vị được (virtualenv KHÔNG relocatable:
  launcher ghi cứng đường dẫn base interpreter khi tạo).
rationale (nguyên nhân GỐC, không phải ngọn): >
  Không phải lỗi code. Gốc: thư mục dự án được copy/di chuyển từ máy 'k.nguyen.manh.toan' sang
  'toann'; .venv mang theo đường dẫn tuyệt đối cũ. Đây cũng là minh hoạ sống cho chính bài toán
  portability của dự án — nhưng nằm ở tầng _system/.venv (công cụ), KHÔNG phải trong learning_vault.
impact:
  - "KHÔNG chạy được pytest / validator ở phiên hiện tại → mọi con số test là 'theo transcript', chưa tái kiểm."
evidence:
  - "Lệnh đã chạy: .venv\\Scripts\\python.exe -m pytest ... → 'No Python at ...Python311\\python.exe'"
  - "Lệnh đã chạy: python --version → Python 3.13.12 (interpreter hệ thống hiện có)"
verified: true
method: ran-command
status: resolved
resolution: >
  ĐÃ SỬA GỐC ngày 2026-07-03 (verified ran-command):
  1) Xoá .venv hỏng; python -m venv .venv bằng Python 3.13.12 (scoop) — pyproject requires-python
     ">=3.10" nên 3.13 hợp lệ.
  2) pip install --require-hashes -r requirements.txt → THÀNH CÔNG (xem NOTE-002: lock có sẵn hash
     wheel cp313, không cần đổi lock).
  3) pip install pytest (dev dep, không trong lock).
  4) pytest validator/tests → 216 passed; sau khôi phục claim_rules (NOTE-006) → 218 passed.
  5) validate.py --scope full trên vault + _system → pass:true, errors:[], warnings:[].
reversible: "n/a (việc sửa môi trường; .venv luôn dựng lại được từ requirements.txt)."
```

---

## NOTE-002 — Lock có bao phủ Python 3.13 (lo ngại ban đầu đã được THỰC NGHIỆM bác bỏ)

```yaml
id: NOTE-002
type: note
date: 2026-07-03
title: "requirements.txt biên dịch trên 3.11 NHƯNG lock chứa sẵn hash wheel cp313 → cài trên 3.13 OK"
spec_ref: "requirements.txt / TRD-004 / pyproject requires-python >=3.10"
summary: >
  CẬP NHẬT (verified): lo ngại ban đầu 'lock 3.11-only → cài trên 3.13 sẽ lệch hash' là SAI.
  pip-compile --generate-hashes ghi hash cho MỌI file phân phối của phiên bản đã ghim (đa nền tảng/
  đa phiên bản Python), nên lock chứa sẵn hash của pydantic_core/pyyaml wheel cp313-win_amd64.
  Thực nghiệm: pip install --require-hashes -r requirements.txt trên Python 3.13.12 → THÀNH CÔNG,
  không cần đổi lock. pyproject requires-python ">=3.10" cũng chấp nhận 3.13.
correction: >
  Bài học: KHÔNG suy đoán ('nhiều khả năng thất bại'). Phải thử thực nghiệm rồi mới kết luận —
  đúng nguyên tắc 'tính, đừng đoán'. Entry này ban đầu ghi lo ngại chưa kiểm; nay đã sửa theo sự thật.
evidence:
  - "Lệnh đã chạy: pip install --require-hashes -r requirements.txt → 'Successfully installed ... pydantic-core-2.46.4 ...'"
  - "Log tải: 'Downloading pydantic_core-2.46.4-cp313-cp313-win_amd64.whl' + hash pass"
  - "pyproject.toml: requires-python = '>=3.10'"
verified: true
method: ran-command
status: active
recommendation: >
  Giữ nguyên lock + --require-hashes. Chỉ regenerate lock (qua change request) nếu NÂNG phiên bản
  thư viện, không phải vì đổi Python trong dải >=3.10 đã có wheel.
reversible: "n/a"
```

---

## NOTE-003 — Trạng thái độ phủ invariant & số test (theo transcript, CHƯA tái kiểm)

```yaml
id: NOTE-003
type: note
date: 2026-07-03
title: "Baseline THẬT phiên này: 218 passed (216 gốc + 2 sau khôi phục claim_rules); validator full PASS"
spec_ref: "INV-01..26"
summary: >
  ĐÃ TÁI KIỂM (verified ran-test) sau khi sửa .venv (NOTE-001):
  - pytest validator/tests → 216 passed ở trạng thái nhận được (thiếu claim_rules — NOTE-006).
  - Sau khi khôi phục claim_rules.md + test (NOTE-006) → 218 passed.
  - validate.py --scope full (vault + _system) → pass:true, errors:[], warnings:[].
  Con số 'transcript' trước đây (218) khớp lại SAU khi vá đúng phần bị thiếu do di chuyển máy.
rationale: >
  Không tuyên bố PASS nếu chưa có output thật — nay đã có output pytest + validator thật ở phiên này.
evidence:
  - "Lệnh đã chạy: pytest validator/tests -q → '216 passed' rồi '218 passed'"
  - "Lệnh đã chạy: validate.py --system . --vault ..\\learning_vault --level full --scope full --json → pass:true"
verified: true
method: ran-test
status: active
reversible: "n/a"
```

---

## NOTE-004 — Phần chưa làm: lớp prompt vận hành + schemas/

```yaml
id: NOTE-004
type: note
date: 2026-07-03
title: "P10-agent lớp prose ĐÃ đủ: schemas/ (DEC-008) + prompts/ (DEC-009) xong"
spec_ref: "spec 20.1 bước 8–10 (lớp agent/prompt)"
summary: >
  Đã có: rules/ ĐỦ 6 file (review, teaching, validation, claim, memory, anti_drift — DEC-012), commands.md,
  validator/ đầy đủ, fsrs_config.yaml, VERSION, schemas/ (DEC-008), prompts/ (DEC-009),
  change_requests/ (DEC-010), migrations/planner.py (DEC-011).
  Lõi P10-agent để AI chạy đầu-cuối coi như đủ. CÒN LẠI (chưa dựng, ưu tiên thấp):
  validator/{invariants.md,error_codes.md} (trùng lặp spec + validation_rules.md, ưu tiên thấp);
  P11 lớp execution + cache.py/diff.py (hoãn tới khi có schema v2 / vault lớn);
  backend còn null: /skip /fix; /system cố ý null (chỉ tạo CR).
  ĐÃ CÓ (11/15): learn/review/done/forget + schedule/status/resume/gaps/test (read-only) + source/ask (LIGHT).
  → P12 tất định XONG + Pilot Runbook. CR workflow chạy thật (cr-0001 v2.6, cr-0002 /test read-only).
  Còn: pilot người-chạy (thủ công) + /skip (UX) + /fix (rủi ro cao) + P11 (hoãn).
  [XONG 2026-07-03 — DEC-013] templates/ (topic + lesson) đã dựng + golden test.
rationale: >
  Đây là mắt xích cuối để hệ thống 'chạy thật đầu-cuối'; phần prose thuần nên ít testable nhất.
impact:
  - "Chưa thể coi là sản phẩm AI-dùng-được đầu-cuối cho tới khi có lớp prompt này."
evidence:
  - "file_search 'system_prompt.md' → No files found"
  - "file_search 'router_prompt.md' → No files found"
  - "Cây thư mục _system/: có rules/, commands.md, validator/ — không có schemas/ hay *_prompt.md"
verified: true
method: read-source
status: active
todo: "Soạn 3 file prompt từ PROMPT_LEARNING_SYSTEM.md (v2.6); cân nhắc schemas/ đối chiếu models.py."
reversible: "n/a"
```

---

## NOTE-005 — Nguồn sự thật của spec & cách 'dùng thư viện'

```yaml
id: NOTE-005
type: note
date: 2026-07-03
title: "Spec gốc = PROMPT_LEARNING_SYSTEM.md (v2.6); thư viện chuẩn thì DÙNG (install), không tự viết lại"
spec_ref: "toàn cục"
summary: >
  Nguyên tắc kiến trúc đã chốt: vấn đề đã có lời giải chuẩn thì dùng gói của họ, không tái hiện.
  fsrs (engine ôn), pydantic (schema), PyYAML (YAML), markdown-it-py (AST) — đều install từ PyPI,
  KHÔNG clone source, KHÔNG viết lại. Phần tự viết chỉ là lõi RIÊNG của dự án (validator INV-01..26,
  transaction, views, session) — vì không có upstream để install/clone.
rationale: >
  fsrs_adapter.py chỉ bọc mỏng gọi thẳng py-fsrs (Scheduler/Card/Rating/State) — thuật toán lịch ôn
  vẫn là thư viện thật, không phải bản tự chế.
evidence:
  - "repo_lab/repo_evaluations/fsrs.md: role='install_dependency', source_location=null"
  - "requirements.txt: fsrs==6.3.1, pydantic==2.13.4, pyyaml==6.0.3, markdown-it-py==4.2.0 (+hash)"
  - "end.md: kiểm kê import — 4 việc chuẩn dùng gói của họ; lõi riêng thì tự viết"
verified: true
method: read-source
status: active
reversible: "n/a"
```

---

## NOTE-006 — Bản sao máy hiện tại THIẾU claim_rules (doc + test) → đã khôi phục bám nguồn

```yaml
id: NOTE-006
type: note
date: 2026-07-03
title: "Di chuyển workspace làm rớt rules/claim_rules.md + test_claim_rules_consistency.py (mốc cuối transcript)"
spec_ref: "spec 0.1 / 5.5; validation_rules.md; validate._CLAIM_CLASSES/_CLAIM_STATUS"
summary: >
  Nguyên nhân gốc của lệch số test (transcript 218 vs thực tế 216): bản sao trên máy hiện tại
  THIẾU HẲN cặp file của mốc cuối transcript — rules/claim_rules.md (doc) và
  validator/tests/phase10/test_claim_rules_consistency.py (drift-guard, +2 test). Các phần khác
  (review/teaching/validation rules, commands.md, toàn bộ validator) đều có đủ.
root_cause: >
  Truyền/copy workspace giữa hai máy không trọn vẹn ở bước cuối; KHÔNG phải lỗi logic. Xác định
  bằng: list rules/ chỉ có 3 file; Test-Path test_claim_rules_consistency.py → False; tổng test
  cộng tay = 216 khớp output pytest.
fix: >
  Khôi phục cả hai, DỰNG LẠI TỪ NGUỒN XÁC MINH (không chép ký ức transcript):
  - claim_rules.md: bảng lớp A/B/C/D verbatim từ spec mục 0.1; luật cứng + mã lỗi/INV từ validation_rules.md;
    khối máy-đọc claim_taxonomy bám validate._CLAIM_CLASSES={A,B,C,D} / _CLAIM_STATUS={draft,confirmed}.
  - test: kiểm claim_taxonomy khớp CHÍNH XÁC hằng số code (cùng khuôn test_validation_rules_codes.py).
  → pytest: 216 → 218 passed; validator --scope full vẫn PASS (claim_rules.md không kích INV-18).
evidence:
  - "list_directory rules/ → chỉ review/teaching/validation (trước khi khôi phục)"
  - "PROMPT_LEARNING_SYSTEM.md mục 0.1 (bảng A/B/C/D) + dòng 113 liệt kê claim_rules.md"
  - "validate.py:583-584 _CLAIM_CLASSES/_CLAIM_STATUS"
  - "Lệnh đã chạy: pytest ... test_claim_rules_consistency.py → 2 passed; full → 218 passed"
verified: true
method: ran-test
status: resolved
todo: >
  KIỂM TRA TÍNH TRỌN VẸN bản sao: nên đối chiếu cây file máy hiện tại với máy gốc/transcript để
  chắc không còn file nào khác bị rớt (ví dụ anti_drift_rules.md, schemas/*.schema.md được spec
  mục layout nhắc tới nhưng CHƯA có — xem NOTE-004).
reversible: "Có thể xoá 2 file vừa tạo; nhưng sẽ mở lại lỗ hổng drift-guard claim."
```

---

## NOTE-007 — Kiểm trọn vẹn bản sao: chỉ claim_rules bị rớt; phần còn lại là chưa-dựng (verified)

```yaml
id: NOTE-007
type: note
date: 2026-07-03
title: "Audit đối chiếu spec-layout ↔ đĩa + quét dangling reference → không còn transfer-gap ẩn"
spec_ref: "PROMPT_LEARNING_SYSTEM.md mục 2 (cấu trúc _system/)"
summary: >
  Phương pháp (không cần máy gốc): (1) liệt kê file thực có; (2) đối chiếu layout spec khai báo;
  (3) với mỗi file THIẾU, quét toàn bộ code/rules/commands đã dựng tìm tham chiếu tới nó.
  Kết quả: KHÔNG file built nào tham chiếu tới file thiếu (chỉ vài false-positive: biến
  _PENDING_SCHEMAS, method _invariants của pydantic, literal 'uv.lock' trong danh sách cấm).
conclusion: >
  Transfer-gap DUY NHẤT là claim_rules (doc+test) — đã khôi phục (NOTE-006). Mọi file spec-khai-báo
  còn thiếu đều là CHƯA DỰNG (khớp danh sách 'còn lại' của transcript), KHÔNG phải mất do di chuyển.
  Baseline 218-test tự nhất quán: không có tham chiếu treo.
not_built_yet:   # chưa dựng — thiếu là ĐÚNG kỳ vọng, không phải lỗi mất dữ liệu
  - "[XONG 2026-07-03 — DEC-009] prompts/{system_prompt,router_prompt,system_change_prompt}.md — đã dựng + drift-guard router"
  - "[XONG 2026-07-03 — DEC-008] schemas/*.schema.md (5 file) — đã dựng + drift-guard vào models.py"
  - "[XONG 2026-07-03 — DEC-012] rules/memory_rules.md + rules/anti_drift_rules.md → rules/ ĐỦ 6 file theo layout"
  - "validator/invariants.md, validator/error_codes.md (INV nằm ở spec; mã lỗi ở rules/validation_rules.md — trùng lặp, ưu tiên thấp)"
  - "[XONG 2026-07-03 — DEC-010] change_requests/{pending,approved,rejected,changelog.md} — đã dựng + CR-0001 + drift-guard"
  - "[MỘT PHẦN 2026-07-03 — DEC-011] migrations/planner.py xong; CÒN: lớp execution + cache.py/diff.py (P11) — hoãn tới khi có schema v2/vault lớn"
  - "[XONG 2026-07-03 — DEC-013] templates/ (topic_template + lesson_template, đuôi .template.md) — dựng + golden test"
  - "repo_lab/{candidates.md,selected_repos.md,installed_repos/,reference_repos/}"
  - "_system/README.md, uv.lock (chỉ có requirements.txt — fallback pip, hợp lệ)"
evidence:
  - "Get-ChildItem -Recurse (liệt kê 57 file thực có, trừ .venv/cache)"
  - "grep dangling ref trong validator/*.py + rules/*.md + commands.md → chỉ false-positive"
verified: true
method: ran-command
status: resolved
reversible: "n/a"
```

---

## NOTE-008 — Đối chiếu install ↔ thiết kế: khớp exact, đã verify (theo yêu cầu "install repo đã nêu")

```yaml
id: NOTE-008
type: note
date: 2026-07-03
title: "Mọi dependency thiết kế khai báo đều đã install đúng phiên bản trong _system/.venv"
spec_ref: "pyproject.toml + requirements.txt + repo_lab/repo_evaluations/fsrs.md"
summary: >
  Kiểm theo yêu cầu 'install các repo đã nêu trong thiết kế'. Thiết kế chốt: fsrs==6.3.1 (repo duy nhất
  có phiếu đánh giá, role=install_dependency, install_location=_system/.venv) + pydantic/PyYAML/
  markdown-it-py (thư viện) + pytest (dev). KHÔNG repo nào khác được thiết kế quyết cài/clone
  (repo_evaluations/ chỉ có fsrs.md; candidates.md/selected_repos.md/reference_repos/ chưa dựng).
result: >
  Đối chiếu thực tế .venv: cả 9 gói khoá đều 'already satisfied' đúng version pin; import chạy;
  fsrs.State = [Learning, Review, Relearning] (khớp F-A). Dùng thật, không tự viết lại (fsrs_adapter bọc).
  → Không có repo/deps nào thiếu so với thiết kế. Không cần cài thêm.
evidence:
  - "Lệnh: pip install --require-hashes -r requirements.txt → toàn bộ 'Requirement already satisfied'"
  - "Lệnh: import fsrs/pydantic/yaml/markdown_it + metadata.version → fsrs 6.3.1, pydantic 2.13.4, pydantic-core 2.46.4, PyYAML 6.0.3, markdown-it-py 4.2.0"
  - "fsrs API: State enum = ['Learning','Review','Relearning']"
verified: true
method: ran-command
status: active
note: >
  Nếu SAU này thiết kế thêm repo (vd reference_repos clone-để-đọc, hoặc lib mới): phải (1) thêm phiếu
  repo_evaluations/<id>.md, (2) thêm vào pyproject + regenerate requirements.txt (pip-compile --generate-hashes),
  (3) cài bằng --require-hashes — qua change request, không cài nóng.
reversible: "n/a"
```

---

## NOTE-009 — INV-05 chỉ ép `updated >= created`, KHÔNG ép `updated <= today` (spec-vs-code gap)

```yaml
id: NOTE-009
type: note
date: 2026-07-03
title: "Spec 5.1 nói 'updated <= hôm nay' nhưng code chỉ enforce updated >= created"
spec_ref: "spec 5.1 (updated: >= created, <= hôm nay); validator/models.py + validate.py"
summary: >
  Phát hiện khi thiết kế E2E (chọn `at`). models.py._invariants chỉ raise khi updated < created.
  Không có bất kỳ chỗ nào (models/validate) chặn updated > today. Grep 'today|date.today|now().date'
  trong validator/*.py → không có upper-bound. ⇒ vault có thể lưu updated ở TƯƠNG LAI mà validator PASS.
impact:
  - "Không phải lỗ hổng nghiêm trọng (ghi qua CLI luôn dùng at hiện tại), nhưng lệch spec 5.1."
  - "Tiện cho test (dùng at cố định tương lai không vỡ), nhưng người dùng sửa tay updated=tương lai sẽ lọt."
evidence:
  - "models.py: LessonState._invariants / TopicState._invariants — chỉ 'updated < created'"
  - "grep today|date.today trong validator/*.py → không có check upper-bound"
verified: true
method: ran-test
status: resolved
resolution: >
  ĐÃ SỬA ở DEC-029 (2026-07-04). Thêm _check_updated_not_future trong validate.py (validate_full_core,
  cho lesson_state + topic_state), 'today' = ngày lịch thật theo utc_offset (KHÔNG day_cutoff, đúng spec §8.5).
  Model giữ nguyên phần thuần created<=updated; phần thời gian đặt ở validator (có offset + mốc now bơm được:
  --at cho CLI, Transaction.now cho driver). KHÔNG cần CR (code khớp lại spec, không đổi spec/registry).
  Kiểm chứng: RED-first test_inv05_updated_today.py (5 test) + full suite 321 passed + validate.py --at chạy thật.
  Recommendation cũ ('cần CR') đã được xét lại: đây là bug code-lệch-spec, không phải đổi spec ⇒ không cần CR.
reversible: "Gỡ check + tham số now (backward-compatible)."
```

---

## NOTE-010 — Nợ tất định do DEC-029 (INV-05 now=đồng-hồ-thật) — ĐÃ đóng bằng bơm now cố định vào test

```yaml
id: NOTE-010
type: note
date: 2026-07-04
title: "DEC-029 làm test validate-standalone phụ thuộc đồng hồ tường → đã bơm now cố định cho TẤT CẢ"
spec_ref: "hệ quả DEC-029; nguyên tắc tất định (spec §0/§1 determinism)"
summary: >
  DEC-029 để validate_full_core/semantic mặc định now=datetime.now() (đúng cho audit production). Nhưng
  nhiều test gọi validator STANDALONE với now mặc định trên vault/fixture ngày cứng (2026-06-30..07-03).
  ⇒ chạy suite trên máy có ĐỒNG HỒ THỰC trước các ngày đó sẽ báo E-SCHEMA (updated>today) giả → đỏ oan.
  Đây là nợ tất định TÔI tạo ra khi thêm DEC-029 (lúc đầu chỉ sửa 2 file cli_loop/p12).
resolution: >
  Đã bơm `now` TƯỜNG MINH vào MỌI call validate-standalone (13 file): test driver dùng now=mốc-thao-tác
  (REVIEWED_AT/DONE_AT/FORGET_AT/AT — ngữ nghĩa 'validate tại thời điểm thao tác'); test validate vault
  demo/fixture dùng hằng now cố định (>= ngày dữ liệu). Đường transaction đã tất định sẵn (now=at threaded).
  Còn test_staged_full_semantic giữ nguyên: assert MEMBERSHIP (E-GATE-FAIL in codes) nên đã tất định về kết quả.
evidence:
  - "grep validate_full_(core|semantic) không-kèm-now trong tests → chỉ còn docstring + call đã xuống dòng now="
  - "13 file sửa: test_session_{review,done,forget,learn,source,cli}, test_done_draft_knowledge, test_templates_valid, test_e2e_claim_source, test_full_core, test_inv19_version, test_gate_evidence, test_claims, test_inv03_refs (+ trước đó cli_loop, p12)"
  - "ran-test: full suite 321 passed sau khi bơm now"
verified: true
method: ran-test
status: resolved
lesson: "Khi thêm 1 chiều-thời-gian vào validator, PHẢI rà mọi caller standalone trong test để giữ tất định — không chỉ caller trực tiếp của thay đổi."
reversible: "n/a (cải thiện chất lượng test)"
```

---

## NOTE-011 — P12 stateless-handoff: ĐÃ có auto-test tất định (phần AI-dạy-thật vẫn thủ công)

```yaml
id: NOTE-011
type: note
date: 2026-07-04
title: "Handoff cross-session (phiên 2 tiếp quản chỉ từ file, path khác) — auto-test tất định, có răng"
spec_ref: "spec 20.12–13, §11B/11B.2; PHASE_12 DoD mục 'stateless handoff'"
summary: >
  Thêm tests/phase12/test_stateless_handoff.py (3 test): phiên-1 /resume mở phiên (open_session vào FILE,
  không /done) → COPY vault sang path tuyệt đối KHÁC (giả lập máy khác) → 'phiên 2' đọc nguội bằng
  cmd_status/cmd_resume (hàm đọc-file thuần). Assert: status thấy đúng topic/lesson + cảnh báo phiên chưa
  đóng; resume khôi phục ĐÚNG next_action (đọc lại từ file để so, không hardcode); validator FULL PASS trên
  path mới (portability INV-16); 2 lần status giống hệt (tất định). now=AT cố định → không lệ đồng hồ.
teeth_verified: >
  Thực nghiệm (ran-command): đổi next_action thành 'SENTINEL-XYZ-123...' → cmd_resume trả đúng sentinel
  ('TEETH OK') ⇒ resume phản ánh TRUNG THỰC file, không hardcode. Nếu hồi quy làm mất fidelity next_action /
  không hiện open_session / state không sống sót khi đổi path → test ĐỎ.
scope_note: >
  Đây là phần AUTO-TEST ĐƯỢC của P12 DoD stateless-handoff. Phần CÒN LẠI (không auto): AI thật dạy 1 topic
  qua nhiều lượt hỏi-đáp + chấm rubric/evidence + phiên AI-2 (model/context khác) đọc hiểu và dạy tiếp —
  nghiệm thu bán-thủ-công (walkthrough), vì tầng dạy 'không có đúng tuyệt đối' (validator dưới mới là chốt).
evidence:
  - "validator/tests/phase12/test_stateless_handoff.py — 3 test PASS"
  - "ran-command teeth: sentinel next_action round-trip qua cmd_resume = khớp"
  - "ran-test: full suite 326 passed (323 + 3); validator full scope demo pass:true"
  - "PILOT_RUNBOOK.md đồng bộ: mục 3 + DoD mục 5 tách [AUTO] nền-tất-định (test_stateless_handoff) vs [MANUAL] tầng-dạy; mục 4 thêm --at cho audit tái-lập (DEC-029). Drift-guard phase12/test_pilot_runbook PASS"
verified: true
method: ran-test
status: active
```

---

## NOTE-012 — Audit toàn vẹn tham chiếu hệ claim/nguồn: ĐÚNG spec, KHÔNG mở rộng (chống over-reach)

```yaml
id: NOTE-012
type: note
date: 2026-07-04
title: "claim/source/anchor reference-integrity: verified khớp spec §5.5/INV-04/12/13/14 — cố ý KHÔNG thêm luật"
spec_ref: "spec §5.5 (Claim & Evidence Contract), INV-04/12/13/14/15, dòng 666 (src-* không trùng)"
summary: >
  Soát toàn vẹn tham chiếu trong hệ claim/nguồn (đọc mã _check_claims + models.Sources + spec §5.5).
  KẾT QUẢ: enforce ĐÚNG spec, KHÔNG có gap:
    - src-* uniqueness (INV-04): ĐÃ enforce ở models.Sources._invariants (len != set → raise).
    - src id pattern ^src-\S+$: ĐÃ enforce (Source._sid).
    - B confirmed: source_refs phải trỏ nguồn confirmed + anchor tồn tại + quote≠rỗng (INV-12,
      _anchor_confirmed_valid) → ref treo/anchor thiếu ⇒ E-CLAIM-NOSRC.
    - C confirmed: premise_refs phải là claim A/B confirmed TỒN TẠI (INV-14) → premise treo/sai lớp/
      draft ⇒ E-CLAIM-WEAKBASE (by_id.get(pid) is None cũng bắt).
    - raw/rejected làm anchor ⇒ E-SRC-RAWUSED (INV-13).
decision_not_to_extend: >
  KHÔNG thêm check 'source_refs trên claim NON-confirmed (A/C/draft) phải resolve'. Lý do: spec §5.5 nói
  RÕ chỉ status=confirmed mới áp luật lớp, và tuyên bố 'Phạm vi claim CỐ Ý HẸP để khả thi'. Thêm luật này
  = BỊA yêu cầu spec không có → vi phạm nguyên tắc 'không bịa'. (Khác open_session DEC-031: đó là con trỏ
  vận hành + INV-03 'mọi tham chiếu'; còn đây nằm trong hợp đồng claim spec đã scope hẹp có chủ đích.)
  Cũng KHÔNG ép anchor id uniqueness trong 1 source (INV-04 chỉ liệt kê gap-*/rv-*/src-*, không có anchor).
regression_locks_added: >
  Khoá HÀNH VI ĐÚNG hiện có (không phải luật mới) bằng 3 test: test_claims::test_C_premise_nonexistent_is_weakbase;
  test_e2e_claim_source::test_class_B_dangling_source_ref + test_class_B_dangling_anchor. Đề phòng hồi quy
  làm im lặng ref treo.
evidence:
  - "models.py Sources._invariants: 'source id trùng (INV-04)'; Source._sid pattern"
  - "validate.py _check_claims + _anchor_confirmed_valid (INV-12/13/14) — đọc trực tiếp"
  - "spec §5.5: 'nếu status=confirmed thì áp luật lớp'; 'Phạm vi claim (cố ý hẹp để khả thi)'"
  - "ran-test: full suite 331 passed (328 + 3 khoá hồi quy)"
verified: true
method: ran-test
status: active
lesson: "Audit tìm gap phải phân biệt 'under-enforce so với spec' (đáng fix) vs 'spec cố ý không yêu cầu' (KHÔNG được tự thêm)."
```

---

## NOTE-013 — Audit coverage mã lỗi (spec §10.6): 39 mã, tìm & bịt 2 lỗ (E-SCHEMA-UNKNOWN/E-SCHEMA-YAML)

```yaml
id: NOTE-013
type: note
date: 2026-07-04
title: "Mọi mã lỗi validator PHÁT RA đều có test ASSERT — validate-the-validator (spec §10.6) đủ"
spec_ref: "spec §10.6 (Kiểm Thử Chính Validator: mỗi INV/mã có ≥1 fixture FAIL kèm expected_error_code)"
summary: >
  Audit meta bằng script: trích 39 mã E-* validator PHÁT RA (rep.err/TxError/error_code/raise ở
  validate/transaction/session/models/...) rồi đối chiếu tập mã được ASSERT trong tests (dòng có 'assert'
  hoặc tên fixture). Phát hiện 2 mã CHƯA có test: E-SCHEMA-UNKNOWN (schema field lạ) và E-SCHEMA-YAML
  (front-matter YAML hỏng) — hai nhánh lỗi mức LIGHT bị bỏ sót test. Đã bịt bằng 2 test
  phase06_light: test_unknown_schema + test_broken_yaml_frontmatter. Audit lại → 0 mã thiếu.
process_note: >
  CẢNH BÁO công cụ: PowerShell Select-String + nhiều Write-Host bị CONSOLE TRUNCATION (chỉ hiện dòng cuối)
  → cho âm-tính-giả (ban đầu tưởng 0 gap). Phải dùng script Python (stdout render đủ) + grep_search (tin cậy)
  mới ra đúng 2 gap. Bài học: audit định lượng KHÔNG dùng PowerShell echo nhiều dòng; dùng script ghi rõ ràng.
evidence:
  - "script audit (tạm, đã xoá): EMITTED=39, missing-before=[E-SCHEMA-UNKNOWN, E-SCHEMA-YAML], missing-after=0"
  - "grep_search xác nhận: 2 mã đó phát ra ở validate.py (_validate_state_file + _parse_state_model) nhưng 0 test trước fix"
  - "validator/tests/phase06_light/test_validate_light.py: +test_unknown_schema, +test_broken_yaml_frontmatter"
  - "ran-test: full suite 333 passed (331 + 2)"
verified: true
method: ran-test
status: active
lesson: "Enforce mà KHÔNG có test = có thể âm thầm hỏng khi refactor. §10.6 đòi mỗi mã có fixture FAIL — nay đủ 39/39."
```

---

## NOTE-014 — Audit error-path của driver (session.py): coverage ĐỦ, không cần thêm test

```yaml
id: NOTE-014
type: note
date: 2026-07-04
title: "13 nhánh SessionError của driver — các nhánh user-facing quan trọng ĐỀU có test; không thêm ceremony"
spec_ref: "robustness driver (spec 11A commands); §10.6 (validate-the-validator, tinh thần)"
summary: >
  Soát toàn bộ 'raise SessionError' trong session.py (13 nhánh) đối chiếu test. KẾT QUẢ: các nhánh
  quan trọng ĐỀU có test — cmd_review(item lạ), cmd_forget(no-confirm + topic-level + unknown-lesson),
  cmd_test(unknown-lesson), cmd_source(unknown-topic), cmd_ask(unknown-lesson), cmd_learn(existing-topic +
  bad-topic-id). Chỉ còn vài nhánh input-validation VẶT chưa test riêng (cmd_ask câu-hỏi-rỗng / lesson_id
  thiếu '/'; cmd_source topic_id chứa '/'; cmd_test thiếu current_lesson).
decision: >
  KHÔNG thêm test cho các nhánh vặt đó lúc này: giá trị thấp (input-validation hiển nhiên, cùng pattern đã
  test ở lệnh khác) — thêm sẽ là ceremony, trái tinh thần 'cực tốt = có ý nghĩa, không busywork'. Ghi lại để
  phiên sau KHÔNG audit lại vùng này. Nếu sau muốn 100% branch coverage driver → thêm nhanh theo pattern có sẵn.
evidence:
  - "grep 'raise SessionError' session.py = 13 nhánh; grep tests: forget/test/source/ask/learn/review error-path đều có pytest.raises(SessionError)"
verified: true
method: ran-command
status: active
```

---

## NOTE-015 — Pilot tự-giả-lập-người-học tìm được 2 BUG THẬT + chạy trọn lesson 'learned' đầu tiên

```yaml
id: NOTE-015
type: note
date: 2026-07-04
title: "Chạy pilot end-to-end qua CLI thật (tự author nội dung học) → phát hiện 2 bug tích hợp auto-test bỏ sót"
spec_ref: "PHASE_12 pilot; theo yêu cầu người dùng 'tự giả lập người học rồi tìm lỗi'"
summary: >
  Trên bản COPY tạm của vault demo, chạy CLI thật: /status → /learn python → tự author lesson.md
  (Question/Answer transcript + 5 Evidence, quote ⊆ transcript) + lesson_state (learned + điểm đạt cổng) →
  /done. Việc này ĐI QUA tầng semantic (gate INV-07 + evidence INV-22/22b) với NỘI DUNG THẬT — điều mà
  vault demo (in_progress, mastery 0, KHÔNG có lesson_notes) + unit test nội-dung-tổng-hợp chưa từng phủ.
bugs_found:
  - "BUG1 (DEC-038): file có BOM UTF-8 (editor Windows) → validator báo 'thiếu front-matter' oan + driver
     _load_raw lại đọc được → LỆCH reader → E-SCHEMA+E-VIEW-MISMATCH. Fix: read_text utf-8-sig."
  - "BUG2 (DEC-039): /done regen KHÔNG đồng bộ topic_state.lessons[].status (view §4) → khi lesson→learned,
     index kẹt 'not_started' → E-INDEX-MISMATCH. Fix: regen đính+sync lesson_status."
outcome: >
  Sau 2 fix: /done python learned → committed:true, pass:true; validate FULL độc lập pass:true. Đây là
  lesson 'learned' đầy đủ (evidence/gate/index/view) ĐẦU TIÊN đi trọn qua CLI thật — trước đó chỉ có vault
  demo tối giản + unit test tổng hợp.
honesty_boundary: >
  Pilot này tìm bug tầng MÁY (Class A/B: driver+validator+composition), KHÔNG chứng minh 'người học hiểu
  thật' (Class D) — tôi đóng cả 2 vai teacher+learner nên rubric/evidence tự-nhất-quán, không phải kiểm
  độc lập. Handoff cross-AI DẠY-TIẾP thật vẫn cần người + phiên AI thứ 2 (PHASE_12 [MANUAL]).
lesson: >
  Auto-test dùng fixture tối giản BỎ SÓT bug chỉ lộ khi nội dung THẬT chảy qua nhiều tầng (BOM, view-sync
  khi status đổi). Pilot self-simulate là cách rẻ tìm loại bug tích hợp này — nên lặp lại định kỳ.
evidence:
  - "ran-command: chuỗi CLI trên %TEMP%/pilot_vault (status/learn/done + validate FULL)"
  - "DEC-038, DEC-039 (RED-first tests + full suite 348 passed)"
verified: true
method: ran-command
status: active
```

---

## NOTE-016 — Pilot sâu vòng 2 (review + claim/source/Knowledge Map + forget): SẠCH end-to-end, không bug mới

```yaml
id: NOTE-016
type: note
date: 2026-07-04
title: "Chạy tiếp pilot qua các nhánh chưa đi với nội dung thật — tất cả PASS đúng kỳ vọng (dương + âm)"
spec_ref: "PHASE_12; INV-08/12/13/23/26; nối tiếp NOTE-015"
summary: >
  Trên bản copy tạm (pilot2), chạy CLI thật các nhánh mà NOTE-015 chưa phủ, mỗi bước validate FULL:
    - /review docker/lesson-001 grade 2 → committed: card cập nhật (Learning step1, stability 2.3065,
      due 2026-07-05, mastery in_review), log ghi, view regen. FSRS replay đúng.
    - Nguồn confirmed (src-001+anchor a1) + claim lớp B confirmed (clm-001→src-001#a1) + Knowledge Map
      chứa clm-001 → /done committed, pass. INV-12/13/23 qua flow thật OK.
    - Thêm draft claim clm-002 (KHÔNG ở map) → /done regen has_draft_knowledge=TRUE, pass. INV-26 dương OK.
    - Đưa clm-002 (draft) VÀO Knowledge Map → /done ABORT committed=false, E-DRAFT-IN-MAP. INV-26 âm OK;
      abort KHÔNG làm hỏng vault (khôi phục topic.md rồi /forget sau đó vẫn PASS).
    - /forget docker/lesson-001 → committed: lesson xoá + tombstone (INV-11) + docker thành topic RỖNG
      (dir còn) → current_topic='docker' vẫn hợp lệ (DEC-037), current_lesson synced None.
result: >
  KHÔNG phát hiện bug MỚI vòng này. Các nhánh semantic/FSRS/forget SẠCH end-to-end với nội dung THẬT —
  SAU khi 2 bug NOTE-015 (BOM DEC-038, index-status-sync DEC-039) đã fix. Đây là verified-clean có giá trị:
  lần đầu các nhánh này đi trọn với nội dung thật (trước chỉ unit-test tổng hợp + demo tối giản).
honesty: >
  Không đổi code turn này (không có bug → không fix; tránh ceremony). Vẫn Class A/B; Class D (hiểu thật) +
  cross-AI DẠY-tiếp vẫn cần người. Đề xuất: lặp pilot self-simulate định kỳ khi thêm tính năng — rẻ, bắt bug tích hợp.
evidence:
  - "ran-command: chuỗi /review /done(x3) /forget trên %TEMP%/pilot2, mỗi bước committed/pass đúng kỳ vọng; E-DRAFT-IN-MAP đúng ở ca âm"
  - "full suite vẫn 348 passed (không đổi code)"
verified: true
method: ran-command
status: active
```


---

## NOTE-017 — Pilot vòng 3 (review→mastered) tìm BUG THẬT: Card.step under-modeling (DEC-040)

```yaml
id: NOTE-017
type: note
date: 2026-07-04
title: "Pilot vòng 3 đi nhánh review-nhiều-lần-tới-mastered → phát hiện crash step=None (Review state) auto-test bỏ sót"
spec_ref: "PHASE_12 pilot; spec §29/§8.2; INV-08/21; nối tiếp NOTE-015/016"
summary: >
  Trên bản copy tạm (pilot3_vault), chạy CLI thật nhánh CHƯA đi: /review lặp lại grade 3 (Easy) để
  đẩy card qua State.Review và tiến tới mastered (mastered_stability_days=60). NGAY review Easy đầu
  tiên → CRASH: py-fsrs đặt card.step=None khi vào Review nhưng model Card.step khai `int` bắt buộc →
  ValidationError ở _regen_topic_views. Đây là bug tích hợp thật (DEC-040) — auto-test bỏ sót vì mọi
  test review dùng grade=2 (giữ Learning, step int).
bug_found:
  - "DEC-040: Card.step phải Optional[int] (py-fsrs Review⇒step None). Fix schema (nguồn dữ liệu),
     đúng-đắn state↔step do replay INV-08 bảo vệ. Khớp spec §29 dòng 1 (đã tự quyết step Optional)."
lifecycle_covered: >
  Sau fix, chứng minh trọn vòng đời step qua CLI thật: Learning(int)→Review(None, stab 8.30)→
  Review(stab 65.62 ⇒ MASTERED)→[Again]Relearning(int, need_redo). validate FULL PASS mỗi bước.
  Đây là lần ĐẦU đạt mastery_state=mastered qua CLI thật (trước chỉ unit-test dựng card tổng hợp).
honesty_boundary: >
  Vẫn Class A/B (máy). Bug này thuần schema/replay — không liên quan Class D. Bài học lặp lại NOTE-015:
  fixture tối giản (grade=2 mãi) che nhánh chỉ lộ khi đi hết không gian trạng thái thật (Review/mastered).
lesson: >
  Khi model bọc cấu trúc thư viện bên thứ 3 (py-fsrs Card), PHẢI phủ MỌI trạng thái thư viện sinh ra
  (Learning/Review/Relearning), không chỉ trạng thái 'happy' hay gặp. Coverage theo state-space, không
  theo 'lệnh chạy được 1 lần'.
also_verified_clean:  # các nhánh CHƯA-đi khác của vòng 3, kiểm qua vault tạm — SẠCH, không thêm ceremony test
  - "Class C claim (INV-14) toàn-vault e2e: DƯƠNG (C confirmed + premise B confirmed → PASS) + ÂM
     (premise treo/premise draft → E-CLAIM-WEAKBASE). Trước đây C chỉ test UNIT (dict), chưa qua pipeline
     collect-from-markdown thật. Kết quả khớp — enforcement đúng qua toàn pipeline."
  - "Multi-lesson topic (driver): demo chỉ 1 lesson nên đường driver đọc/regen NHIỀU lesson_state CHƯA
     từng chạy. Author docker/lesson-002 hợp lệ (index+đĩa+lesson.md) → (a) baseline chưa-regen bắt
     E-VIEW-MISMATCH đúng (INV-09 có răng: không thể thêm lesson mà không regen view); (b) /review + /done
     regen view gồm CẢ HAI lesson (review_schedule rv-001+rv-002 sắp đúng), đồng bộ status cả hai index
     (DEC-039 scale multi-lesson), validate FULL PASS. Không bug."
  - "INV-22b (E-ASSESS-FAKEQUOTE) đã phủ kỹ sẵn (test_fake_quote âm + test_verbatim_tolerance dương
     bold/nháy-cong/space + normalize_for_match unit + pilot NOTE-015 5 evidence thật) → KHÔNG pilot lại
     (tránh ceremony)."
evidence:
  - "ran-command: /review grade 3 lần 1 crash (step=None) → fix → grade 3,3 tới mastered → grade 0 tới need_redo, mỗi bước validate FULL pass:true"
  - "DEC-040 (RED-first test + full suite 349 passed); py-fsrs verify trực tiếp step=None ở Review"
verified: true
method: ran-command
status: active
```


---

## NOTE-018 — Pilot vòng 4 (robustness): driver crash traceback trên file hỏng → fix biên parse (DEC-041)

```yaml
id: NOTE-018
type: note
date: 2026-07-04
title: "File on-disk sửa-tay hỏng khiến /review /done /forget crash stack trace thô — tầng đọc-parse driver thiếu biên lỗi"
spec_ref: "spec §10.4/§10.6/§19; an toàn sản phẩm thương mại; nối tiếp DEC-040"
summary: >
  Sau DEC-040 (step=None), đặt câu hỏi tổng quát cho SẢN PHẨM THƯƠNG MẠI: driver có BAO GIỜ crash bằng
  traceback thô không (thay vì mã lỗi chẩn đoán được)? RED evidence: sửa tay mastery score=99 (ngoài 0..3)
  rồi /review → pydantic ValidationError THOÁT dạng stack trace. Đào sâu thấy 3 bề mặt crash ở tầng
  đọc-parse driver (đều KHÔNG được main() bắt): _split IndexError (thiếu front-matter), _load_raw YAMLError
  (YAML hỏng), _lesson_model_from_raw ValidationError (schema sai). Validator xử lý cả 3 duyên dáng; driver
  thì không → BẤT ĐỐI XỨNG nguy hiểm.
fix: "DEC-041 — SchemaError(SessionError) ở _load_raw + _lesson_model_from_raw; main() getattr error_code → E-SCHEMA/E-SCHEMA-YAML sạch."
design_validation: >
  Chọn (C) bọc-biên thay (B) pre-flight cả-topic. Kiểm chứng thực nghiệm quyết định: /forget một lesson
  ĐANG HỎNG phải THÀNH CÔNG (regen loại nó ra) — (B) sẽ chặn nhầm, (C) đúng. Đây là ví dụ 'validate thiết
  kế bằng thực nghiệm trước khi tin' — không chỉ chọn theo cảm tính.
principle: >
  Nguyên tắc an toàn thương mại chốt lại: DRIVER KHÔNG BAO GIỜ được crash bằng traceback. Mọi lỗi đọc dữ
  liệu on-disk (người dùng sửa tay được) PHẢI suy biến về mã lỗi chuẩn — ngang hàng validator. Traceback
  thô = rò cấu trúc nội bộ + không hành động được cho người dùng cuối.
lesson: >
  DEC-040 là một TRIỆU CHỨNG; DEC-041 chữa CĂN BỆNH (thiếu biên lỗi ở tầng parse). Sau khi fix triệu chứng,
  luôn hỏi 'còn bao nhiêu biến thể cùng gốc?' rồi chữa gốc — đúng tinh thần 'fix bản chất, không fix ngọn'.
evidence:
  - "RED-first: 3 test test_session_cli.py (corrupt_schema→E-SCHEMA, broken_yaml→E-SCHEMA-YAML, missing_frontmatter→E-SCHEMA)"
  - "ran-command: /done vault score=99 → E-SCHEMA sạch; /review sibling hỏng → E-SCHEMA; /forget lesson hỏng → committed True (chứng minh chọn C)"
  - "ran-test: full suite 352 passed (349 + 3)"
verified: true
method: ran-test
status: active
```


---

## NOTE-019 — Pilot vòng 5 (robustness tầng sâu): vault_state sai-kiểu crash lệnh đọc → fix _load_vault_state (DEC-042)

```yaml
id: NOTE-019
type: note
date: 2026-07-04
title: "vault_state YAML-hợp-lệ-nhưng-SAI-KIỂU khiến status/schedule/resume crash AttributeError/TypeError — guard tầng-parse DEC-041 chưa đủ"
spec_ref: "spec §10.4/§10.6/§19; §5.4; nối tiếp DEC-041/NOTE-018"
summary: >
  Tiếp robustness audit (khuyến nghị #1 sau vòng 4). Kiểm chứng thực nghiệm các lệnh ĐỌC trên vault_state
  cố ý SAI KIỂU (YAML vẫn parse được): open_session='notadict' (chuỗi) → status/resume crash
  AttributeError 'str has no get'; current_lesson=12345 (int) → resume crash TypeError 'int not iterable'.
  DEC-041 (guard _load_raw + _lesson_model_from_raw) KHÔNG bắt vì đây là lỗi tầng TRUY-CẬP-FIELD trên raw
  dict, không phải tầng parse. Driver đọc vault_state như raw dict, giả định kiểu, bỏ qua model.
fix: >
  DEC-042 — _load_vault_state(vault): _load_raw (guard fm/YAML) + validate M.VaultState (cùng
  normalize_yaml_object + _STR_FIELDS như validator, KHÔNG lossy-coerce) → sai-kiểu ra E-SCHEMA sạch; trả
  raw. Wire 14 site đọc vault_state. Kiểm: current_lesson/current_topic KHÔNG trong _STR_FIELDS → strict
  reject int → E-SCHEMA ở CẢ driver lẫn validator (không lệch — bài học DEC-038).
trap_noted: >
  Bẫy đệ quy: helper chứa chính chuỗi bị global-replace → tự gọi mình. Đã đổi helper dùng biến `vs` trước
  khi wire. Ghi lại cho lần refactor global-replace sau.
principle_progression: >
  DEC-041 chữa tầng-parse (YAML/schema-model). DEC-042 chữa tầng-field-access (raw dict sai kiểu). Cùng
  một bản chất 'driver đọc dữ liệu không qua model như validator' nhưng ở 2 tầng khác nhau — chữa gốc phải
  quét đủ các tầng. Sau vòng 5: mọi lệnh đọc đã kiểm KHÔNG crash thô trên cả 2 lớp corrupt.
scope_next: >
  Còn có thể đào: topic_state/sources sai-kiểu trong đường REGEN (write commands) trước khi post-write
  validate kịp bắt — cần kiểm vòng 6 (đánh giá xem post-write validate đã đủ lưới chưa, hay regen crash trước).
evidence:
  - "RED-first: 2 test test_session_cli.py (status open_session=chuỗi → E-SCHEMA; resume current_lesson=int → E-SCHEMA)"
  - "ran-command sweep: status/schedule/resume × 2 corrupt → đều E-SCHEMA sạch (trước: crash thô)"
  - "ran-test: full suite 354 passed (352 + 2); happy-path bất biến (validate no-op trên vault hợp lệ)"
verified: true
method: ran-test
status: active
```


---

## NOTE-020 — Pilot vòng 6 (robustness tầng write): authored-collection sai-kiểu → fix DEC-043; KẾT THÚC chuỗi robustness

```yaml
id: NOTE-020
type: note
date: 2026-07-04
title: "topic_state.lessons/lesson_state.review_items sai-kiểu crash lệnh write TRƯỚC regen/post-validate — đóng nốt lớp robustness"
spec_ref: "spec §10.4/§10.6/§19; §4; INV-09/25; nối tiếp DEC-041/042/NOTE-018/019"
summary: >
  Đóng nốt robustness audit (khuyến nghị #1 sau vòng 5). Kiểm chứng thực nghiệm sweep lệnh WRITE trên
  topic_state/lesson_state sai-kiểu. Xác nhận: topic_state.lessons=chuỗi → review/done/forget CRASH
  AttributeError; review_items sai cấu trúc → review/forget crash; lessons-entry thiếu id → forget KeyError.
  ĐỒNG THỜI xác nhận các nhánh ĐÃ có lưới: view field corrupt (review_schedule hash=int) → regen GHI ĐÈ →
  /done vẫn committed (self-heal); enum sai → guard bắt E-SCHEMA.
fix: "DEC-043 — _load_topic_state (validate lessons qua LessonIndexEntry) + cmd_review validate full target lesson + cmd_forget guard review_items structural."
design_asymmetry: >
  Ba cách xử lý CÓ CHỦ ĐÍCH theo ngữ nghĩa (không tùy tiện): topic_state chỉ validate lessons (GIỮ self-heal
  view — kiểm chứng view-hash=int vẫn committed); review validate full lesson (phải hợp lệ mới review, an toàn
  self-heal numeric qua INV-08 replay); forget chỉ structural review_items (GIỮ DEC-041 forget-rác — kiểm chứng
  score=99 vẫn xoá được). Nguyên tắc: validate phần KHÔNG regen/recompute; phần tái-tạo để regen+post-validate+INV-08.
robustness_chain_complete: >
  Chuỗi robustness 3 vòng: DEC-041 (tầng file-parse: YAML/schema/thiếu-fm), DEC-042 (tầng vault_state field-access
  qua model), DEC-043 (tầng authored-collection topic/lesson khi write). Sau vòng 6: MỌI lệnh (đọc+ghi) đã kiểm
  KHÔNG crash traceback thô trên các lớp corrupt (encoding/YAML/schema/type/structure) — luôn suy biến về mã lỗi
  chuẩn (E-IO-ENCODING/E-SCHEMA/E-SCHEMA-YAML), ngang hàng validator. Đạt cam kết an toàn thương mại.
residual_scope: >
  Còn lớp NGỮ NGHĨA sâu (giá trị hợp lệ kiểu nhưng sai logic liên-file) — nhưng đó là việc của validator FULL
  (post-write validate abort transaction), KHÔNG phải crash. sources.md sai-kiểu trong /source: đi qua _load_raw
  (guard YAML) + post-write LIGHT validate → chưa thấy crash surface iterate; có thể kiểm bổ sung nếu cần.
evidence:
  - "RED-first: 2 test test_session_cli.py (done/review topic lessons=chuỗi → E-SCHEMA)"
  - "ran-command sweep: lessons=chuỗi→E-SCHEMA(review+done); view-hash=int→committed=True(self-heal giữ); forget score=99→committed=True(DEC-041 giữ); forget review_items structural→E-SCHEMA sạch"
  - "ran-test: full suite 356 passed (354 + 2); happy-path bất biến"
verified: true
method: ran-test
status: active
```


---

## NOTE-021 — Audit crash-safety transaction (pilot vòng 7): VỮNG, không bug; khoá 2 ranh giới an toàn

```yaml
id: NOTE-021
type: note
date: 2026-07-04
title: "Kiểm toán tính nguyên tử transaction dưới crash — thiết kế roll-forward đúng & phủ tốt; thêm 2 regression-lock cho ranh giới chưa canh"
spec_ref: "spec §10.3/10.3a/b (transaction, RECOVER-FIRST); an toàn dữ liệu sản phẩm thương mại"
summary: >
  Sau khi đóng lớp robustness ĐẦU-VÀO (DEC-041/042/043: file hỏng → lỗi sạch), audit trục an-toàn đối
  xứng ĐẦU-RA: crash giữa ghi → recovery có nhất quán không (all-or-nothing). Đọc trọn transaction.py +
  test_transaction.py. KẾT LUẬN: crash-safety VỮNG, KHÔNG tìm thấy bug. Giao thức roll-forward đúng bản
  chất: một khi 'committing' bền vững (đã qua validate_staged + occ_recheck-2 = quyết-định-commit),
  recovery HOÀN TẤT; trước đó ('prepared') recovery BỎ QUA (vault giữ bản cũ).
already_covered:  # các điểm-crash ĐÃ có test (đọc xác nhận, KHÔNG làm lại — tránh ceremony)
  - "crash GIỮA các file commit đa-file → recover roll-forward tất cả (test_crash_during_commit_then_recover)"
  - "crash SAU replace-hết TRƯỚC ghi log → recover finalize log/tombstone + cleanup (test_crash_after_commit_before_log)"
  - "abort trước 'committing' → file thật không đổi (test_fail_then_abort_leaves_real_file)"
  - "OCC 2 mốc: E-STALE-CONTEXT (read→begin) + E-CONCURRENT-EDIT→abort (begin→commit)"
  - "manifest chính rách → fallback .tmp; retry cloud-lock → E-TX-PARTIAL; multi-root thiếu sibling → E-TX-PARTIAL"
locks_added:  # 2 thuộc-tính-an-toàn cốt lõi CHƯA có test canh — khoá lại (regression-lock, xác nhận GREEN)
  - "test_prepared_crash_not_recovered_vault_stays_old: recovery KHÔNG roll-forward tx 'prepared' (chưa
     quyết-commit) → vault giữ CŨ. Canh chống refactor lỡ đưa 'prepared' vào scan_incomplete = commit tx
     chưa-validate (thảm hoạ). Ranh giới all-or-nothing đầu 'nothing'."
  - "test_recover_refuses_when_target_externally_modified: target bị sửa-ngoài trong cửa sổ crash (hash lạ)
     → recover raise E-TX-PARTIAL, KHÔNG clobber. Canh tính toàn-vẹn-recovery (không ghi đè sửa tay)."
verified_by_reasoning:  # đúng theo thiết kế idempotent, KHÔNG thêm test (tránh ceremony)
  - "recovery tái-nhập được (crash GIỮA recovery): _recover_one tái-suy pending từ hash hiện tại mỗi lần →
     idempotent; 'committed'+còn .tx được scan lại; materialize_log idempotent theo tx_id."
honesty: >
  Turn này KHÔNG có bug để fix (khác vòng 3-6). Báo trung thực: transaction atomicity là phần được thiết kế
  + test cẩn thận nhất. Chỉ bổ sung 2 lock cho ranh giới an-toàn thực sự chưa canh (không phải test vặt).
known_minor_reconfirmed: >
  Orphan '.tx' ở state 'prepared' (crash trước commit) KHÔNG được GC (scan chỉ committing/interrupted/committed).
  An toàn về dữ liệu (vault nhất quán = cũ) nhưng rò rỉ disk. GC để owner/P11 (đã ghi DEC-036). Không đổi turn này.
evidence:
  - "read-source: transaction.py (begin/stage/validate_staged/occ_recheck/commit/recover) + test_transaction.py (13 test cũ)"
  - "ran-test: 2 lock mới GREEN (xác nhận hành vi đúng); full suite 358 passed (356 + 2)"
verified: true
method: ran-test
status: active
```


---

## NOTE-022 — Audit round-trip YAML của driver (pilot vòng 8): TRUNG THỰC, không bug + soạn CR-0004

```yaml
id: NOTE-022
type: note
date: 2026-07-04
title: "Kiểm độ trung thực load→dump→load của driver (đặc biệt timestamp có nháy) — bảo toàn, idempotent, byte-stable"
spec_ref: "toàn vẹn dữ liệu file-based; _dump_state/_load_raw; nối tiếp audit an toàn"
summary: >
  Soi mạch toàn-vẹn chưa từng kiểm: driver _load_raw (yaml.safe_load) → mutate → _dump_state
  (yaml.safe_dump sort_keys=False) → _load_raw. Rủi ro nghi ngờ: timestamp 'due_at_utc: "...Z"' /
  'reviewed_at: ...+07:00' bị dump KHÔNG-nháy → reload thành datetime object thay vì str → drift.
  KẾT QUẢ (ran-command): KHÔNG bug. PyYAML safe_dump TỰ THÊM NHÁY cho chuỗi ambiguous (timestamp) →
  giữ đúng kiểu str. Kiểm cả state gốc VÀ sau /review (log[].reviewed_at offset +07:00, card
  .last_reviewed_at_utc): raw1==raw2 (idempotent), dump byte-stable, reviewed_at giữ type str.
double_safe: >
  Thêm lớp an toàn: view-hash (generated_from_hash) tính từ canonical_json của DATA MODEL, KHÔNG từ
  text YAML → kể cả biểu diễn YAML có đổi, hash view vẫn ổn định. Toàn vẹn view không phụ thuộc YAML text.
decision_no_test: >
  KHÔNG thêm test khoá round-trip: (1) độ trung thực chủ yếu là ĐẢM BẢO của PyYAML (không phải code ta);
  (2) đã được MỌI test /review /done ngầm bao (chúng validate sau commit — round-trip sai sẽ đỏ); (3) thêm
  = ceremony (NOTE-014). Ghi verified-clean để phiên sau KHÔNG soi lại vùng này.
honesty: "Turn này KHÔNG có bug (như vòng 7). Báo trung thực: mạch round-trip lành mạnh."
followup: >
  Thay vì implement 2 open-question (đổi hợp đồng spec — chưa CHẮC dưới ranh giới NOTE-012), soạn CR-0004
  (pending) formalize DEC-029 open_q 'sources[].added <= today' theo đúng §12 (AI chỉ ghi pending, chờ
  spec-owner duyệt). Đây là 'chuẩn bị thiết kế rõ ràng rồi valid rồi mới triển khai'. TRD-005 giữ DEFER (xung đột tiềm tàng P11 migration).
evidence:
  - "ran-command: round-trip lesson_state/topic_state (gốc + sau review) → idempotent + byte-stable; reviewed_at/last_reviewed_at_utc giữ str"
  - "read-source: _dump_state (safe_dump sort_keys=False), view-hash từ canonical_json (không phải YAML text)"
verified: true
method: ran-command
status: active
```


---

## NOTE-023 — Xác minh tất định FSRS cross-platform: code khớp quyết định F-B (due_date), §29#2 đã bị thay thế có chủ đích — KHÔNG bug

```yaml
id: NOTE-023
type: note
date: 2026-07-04
title: "Nghi vấn 'code không quantize stability trước due (spec §29#2)' → GIẢI ĐÁP: §29#2 (v2.5) bị F-B (v2.6) thay có chủ đích; code đúng"
spec_ref: "spec §29 vá #2 (v2.5, superseded); F-B; DEV-002; TRD-002; CR-0001; fsrs.md"
summary: >
  Audit tất định cross-platform: replay gọi sched.review_card (py-fsrs tính due từ stability FLOAT THÔ),
  card_to_dict chỉ round stability 4dp lúc LƯU → KHÔNG quantize-trước-interval như spec §29#2 (v2.5) đòi.
  Nghi là code-vs-spec gap. GIẢI ĐÁP (đọc fsrs.md + TRD-002): py-fsrs KHÔNG có hook/API quantize-trước-due
  (Q2: không có next_interval(stability) public; due tính SẴN nội bộ review_card). Nên §29#2 'không khả thi
  sạch' → quyết định v2.6 (F-B/DEV-002/TRD-002/CR-0001) CỐ Ý THAY: chuẩn so = due_date (ngày) exact +
  stability isclose(1e-4), KHÔNG so due_at_utc exact, KHÔNG quantize-trước-due. Code khớp ĐÚNG quyết định này.
conclusion: "KHÔNG bug. §29#2 là ý-tưởng-v2.5 đã bị thay thế, ghi vết đầy đủ (CR-0001/DEV-002/TRD-002)."
residual_tradeoff: >
  Rủi ro còn lại (đã chấp nhận, TRD-002): due_date có thể lệch 1 ngày cross-platform NẾU due rơi đúng ranh
  giới nửa đêm và libm transcendental lệch ULP. Hiếm; day-granularity 'đủ ổn'. Reversible chỉ khi py-fsrs
  có API quantize-trước-due. cards_equal so due_date exact ở Review → nếu xảy ra sẽ báo E-REVIEW-MISCALC
  (không âm thầm sai) → an toàn (fail-loud, không corrupt).
lesson: "Trước khi kết luận 'code lệch spec', PHẢI truy vết xem điều khoản spec đó có bị CR/deviation sau này thay thế không. §29 là bảng-vá-v2.5, một số mục bị v2.6 (F-A/F-B) supersede."
verified: true
method: read-source
status: active
```


---

## NOTE-024 — Q7 (file chưa dựng) + Q8 (rà prompt): quyết định + xác nhận

```yaml
id: NOTE-024
type: note
date: 2026-07-04
title: "Q7 dựng _system/README.md, BỎ các file trùng/ceremony; Q8 prompt khớp spec — không sửa"
spec_ref: "Q7/Q8 owner-delegated; anti-drift DEC-005/012; spec §0/§11/§12"
q7_decision: >
  DỰNG _system/README.md (định hướng toàn hệ + entry-point cho stateless-handoff phiên AI mới — giá trị
  cao sản phẩm). BỎ có lý do: (1) validator/{invariants.md,error_codes.md} — trùng spec (INV) +
  rules/validation_rules.md (mã lỗi) → nguồn-sự-thật-thứ-2 → rủi ro drift, TRÁI anti-drift; (2)
  repo_lab/{candidates,selected_repos,reference_repos} — chỉ 1 dep (fsrs) đã đánh giá; scaffolding rỗng =
  ceremony; (3) uv.lock — requirements.txt+hash CHÍNH LÀ lock (TRD-004), uv.lock thừa + cần toolchain uv.
q8_review: >
  Rà 3 prompt (system/router/system_change) theo spec §0/§11/§12/§13/§14: KHỚP, đã có drift-guard (router
  test khớp registry+7 intent), KHÔNG stale (vd /resume không còn ghi 'read-only' sau CR-0003; /system chỉ
  tạo CR; /fix chỉ hình thức). Là hiến-pháp cấp cao → thay đổi gần đây (DEC-029..045) là chi tiết triển
  khai, không đụng. KHÔNG sửa (tránh ceremony edit). Xác nhận sạch để phiên sau không rà lại.
evidence:
  - "ran-test: full suite 366 passed sau khi thêm README.md (không phá INV-17/18 / test kiểm kê); validator full PASS"
  - "read-source: 3 prompt vs spec §0/§11/§12; router máy-đọc khớp commands.md + 7 intent"
verified: true
method: ran-test
status: active
```


---

## NOTE-025 — Q5 Class D walkthrough: dạy 1 topic thật đầu-cuối + cold handoff; tìm bug DEC-046

```yaml
id: NOTE-025
type: note
date: 2026-07-04
title: "Walkthrough dạy 'đệ quy' (First Principles→Feynman→Socrates→teachback) + evidence→gate→done→cold-handoff; lộ bug cmd_learn escape (DEC-046)"
spec_ref: "Q5=a; PILOT_RUNBOOK; spec §11A.1/§13/§14; INV-07/22/22b/16"
summary: >
  Chạy walkthrough Class D trên vault tạm (owner chọn Q5=a): /learn topic 'recursion' → AI soạn transcript
  dạy thật (base case + recursive case, ví dụ giai thừa) + 5 evidence (quote ⊆ answer, mỗi trục 1) + chấm
  rubric đạt cổng (concept/explain/apply/teachback=2, critique=1) + status=learned → /done → cold handoff.
found_bug: >
  NGAY /learn với objective='Hiểu đệ quy: hàm tự gọi...' (có ':') → CRASH yaml.ScannerError. Gốc: cmd_learn
  thay free-text vào front-matter YAML không escape (DEC-046). Fixed RED-first → chạy lại trọn flow OK.
outcome_after_fix: >
  /learn committed; /done committed + validate_full_semantic PASS (qua cổng INV-07 + evidence INV-22/22b với
  NỘI DUNG DẠY THẬT — lần đầu 1 lesson 'learned' pedagogical hoàn chỉnh của topic MỚI đi trọn qua CLI);
  cold handoff (copy sang path khác) → cmd_status đọc đúng current_topic/lesson + validator FULL PASS (INV-16).
  B2 trước /done báo E-INDEX/VIEW-MISMATCH (đúng: view stale khi sửa tay) → /done regen self-heal.
honesty_boundary: >
  Tôi đóng CẢ teacher+learner → rubric/evidence tự-nhất-quán. Đây là demo CƠ CHẾ tải nội dung dạy qua máy
  (Class A/B: gate/evidence/view/portability), KHÔNG phải bằng chứng 'người học hiểu thật' (Class D thật cần
  NGƯỜI + phiên AI-2 độc lập đọc-nguội dạy-tiếp — PILOT_RUNBOOK [MANUAL]).
evidence:
  - "ran-command: walkthrough 4 bước trên %TEMP%/wt_vault (+ machine2 path khác); mỗi bước in kết quả; đã cleanup"
  - "DEC-046 (RED-first fix cmd_learn); full suite 367 passed"
verified: true
method: ran-command
status: active
```


---

## NOTE-026 — Truy quét lớp bug DEC-046 ở lệnh khác (/source, /ask): SẠCH — DEC-046 là instance duy nhất

```yaml
id: NOTE-026
type: note
date: 2026-07-04
title: "Kiểm 'free-text người-dùng → YAML/parse' ở /source /ask sau khi fix DEC-046 (cmd_learn) — không tìm thấy biến thể cùng gốc"
spec_ref: "nối DEC-046; bài học NOTE-018 (fix triệu chứng → truy gốc còn bao nhiêu biến thể); INV-16"
summary: >
  Sau DEC-046 (cmd_learn crash ':' vì thay free-text vào front-matter YAML), truy quét các lệnh KHÁC nhận
  free-text người-dùng. Kiểm chứng thực nghiệm (ran-command, vault tạm):
    - /source ref/scope chứa ':' '#' '\"' → committed + validate PASS. AN TOÀN: cmd_source build DICT rồi
      _dump_state (yaml.safe_dump tự escape), KHÔNG text-substitution vào YAML.
    - /ask question chứa ':' '#' '\"' → committed + PASS. AN TOÀN: chèn vào markdown BODY (không YAML).
    - /ask question có XUỐNG DÒNG → committed + PASS (LIGHT validate không vỡ; bullet hơi lệch cosmetic,
      KHÔNG corrupt/không crash → không đáng fix).
    - /source ref 'C:\\Users\\...' (abspath) → committed=False + E-PORT-ABSPATH (INV-16 chặn abspath phá
      portability), vault không đổi → CHẶN ĐÚNG, không crash.
conclusion: >
  Gốc 'free-text → YAML' chỉ có 1 instance = cmd_learn (template text-substitution), đã fix DEC-046. Lệnh
  khác ghi qua safe_dump (source) hoặc markdown body (ask) → miễn nhiễm. Đóng chuỗi điều tra root-cause
  (giống DEC-041→042→043 khép lại). KHÔNG thêm test (các lệnh này đã có test happy + đây là verify-clean).
verified: true
method: ran-command
status: active
```


---

## NOTE-027 — Pilot multi-topic + gaps lifecycle: SẠCH, không bug (nhánh cuối chưa-đi với nội-dung-thật)

```yaml
id: NOTE-027
type: note
date: 2026-07-04
title: "Đa-topic + vòng đời open_gaps chạy nội-dung-thật lần đầu — tất cả đúng kỳ vọng, không bug mới"
spec_ref: "INV-04 (id unique phạm vi topic), §8.5 (schedule loại 'new'), §11A.2 (/gaps); nối pilot NOTE-015/016/025"
summary: >
  Chạy pilot nhánh CHƯA đi với nội-dung-thật đa-topic (mọi pilot trước chỉ 1 topic):
    1. /learn topic thứ 2 'python' → committed + validate PASS (đa-topic OK).
    2. gap-001 ở CẢ docker + python (cùng id, KHÁC topic) → PASS. INV-04 topic-scoped ĐÚNG
       (_check_topic_uniqueness per-topic → cross-topic same-id cho phép; đúng spec §5.1 'phạm vi').
    3. /gaps gộp đúng 2 gap qua 2 topic (_all_lesson_models iterate mọi topic).
    4. /status current=python (đúng, /learn chuyển con trỏ); /schedule(90d)=[] — ĐÚNG: item demo duy nhất
       rv-001 mastery_state='new'; schedule.py:53 loại 'new' (không in PRIORITY) verbatim spec §8.5
       ('New không tự tới hạn') — ĐÃ đọc mã xác minh, KHÔNG đoán.
    5. Âm: trùng gap-id trong CÙNG lesson → E-ID-DUP (bắt đúng INV-04).
    6. Gap lifecycle: thêm gap → PASS; xoá gap (resolve) → PASS + /gaps rỗng.
conclusion: >
  KHÔNG bug. Đa-topic + gaps CRUD + cross-topic uniqueness scoping + aggregation /gaps/status/schedule đều
  đúng. Đây là verified-clean có giá trị (nhánh đa-topic chưa từng chạy nội-dung-thật). KHÔNG thêm test
  (các cơ chế này đã có unit test; đây là verify tích hợp).
significance: >
  Là một trong các NHÁNH NỘI-DUNG cuối chưa đi. Sạch → củng cố nhận định hệ đã đạt cao nguyên vững; các
  pilot còn lại lợi suất-bug giảm dần. Phần chưa làm chủ yếu trigger-gated (schema v2) / human-gated (Class D).
verified: true
method: ran-command
status: active
```


---

## NOTE-028 — RELEASE-READINESS CHECKPOINT (nghiệm thu mốc): 3 cam kết cốt lõi LIVE-verified + ảnh chụp trạng thái

```yaml
id: NOTE-028
type: note
date: 2026-07-04
title: "Nghiệm thu mốc: determinism + portability + chống-giả-mạo FSRS chứng minh LIVE trên vault thật; snapshot sẵn-sàng-sản-phẩm"
spec_ref: "spec §0.2/0.3 (cam kết Class A), §8.3/INV-08 (replay), §16 (portability INV-16); PILOT_RUNBOOK DoD"
live_acceptance:  # chạy trực tiếp trên learning_vault thật (ran-command), KHÔNG chỉ unit test
  - "DETERMINISM: validate_full_semantic 2 lần → report GIỐNG HỆT (pass+errors+warnings). Class A tất định."
  - "PORTABILITY (INV-16): copy vault sang path SÂU/khác (TEMP/cp_a/cp_b/cp_c/) → validate PASS, không lỗi đường-dẫn-tuyệt-đối."
  - "CHỐNG GIẢ MẠO FSRS: sửa tay due_date rv-001 (2026-06-30→2026-08-01) → E-REVIEW-MISCALC (+E-VIEW-MISMATCH) — fail-loud, KHÔNG âm thầm chấp nhận. Nền của cam kết 'không bịa được điểm ôn'."
snapshot:
  tests: "367 passed (validator/tests); bao gồm P12 acceptance (determinism/tamper/portability/handoff), 40/40 mã lỗi có test"
  validator: "full scope trên vault thật: pass=true, errors=[], warnings=[]"
  guarantees:
    class_A: "ĐẢM BẢO TUYỆT ĐỐI (validator code): file/schema/ngày/ID/tham chiếu/replay-FSRS/view/index/transaction/portability. Robustness: mọi lệnh trên file corrupt (encoding/YAML/schema/type/structure) → mã lỗi sạch, KHÔNG crash traceback (DEC-034/035/041/042/043/046). Atomicity crash-safe (NOTE-021)."
    class_B_C: "AUDIT ĐƯỢC (claim bám nguồn/suy luận): validator xác nhận LIÊN KẾT tồn tại, KHÔNG xác nhận nội dung đúng."
    class_D: "CHỈ NGƯỜI KIỂM ('hiểu thật', chất lượng rubric): validator KHÔNG đảm bảo. Nghiệm thu bán-thủ-công (PILOT_RUNBOOK)."
  commands: "11/15 backend chạy thật (learn/review/done/forget + status/schedule/resume/gaps/test read-only + source/ask). /skip+/system null CỐ Ý (spec). /fix DEFER (rủi ro reflow-quote). /validate = validate.py."
  p11_migration: "planner.py + executor.py (atomic migrate-or-rollback) dựng + test (DEC-045). Transform v1→v2 THẬT + cache/diff: trigger-gated (chờ schema v2)."
  decision_journal: "83 entry (46 DEC + 5 DEV + 5 TRD + 27 NOTE) + index.yaml roll-up + _system/README.md; CR §12 (cr-0001..0004). Xuyên suốt, kiểm chứng được."
remaining (KHÔNG phải nợ ẩn — phân loại):
  - "trigger-gated: migration transform v2 thật + cache.py/diff.py (performance) — chờ schema v2 / vault lớn (DEC-011)."
  - "human-gated: Class D nghiệm thu dạy thật (người + phiên AI-2); /fix (rủi ro cao, cần guard chống-reflow-quote)."
  - "open-question còn 1: TRD-005 (cross-file schema_version) — hoãn tới P11 rõ (Q3 owner đồng ý)."
conclusion: >
  Hệ ở trạng thái CAO NGUYÊN VỮNG, sẵn sàng sản phẩm cho phạm vi GĐ1. 7 bug thật đã tìm+fix qua pilot
  nội-dung-thật; 3 vòng pilot gần nhất (source/ask, multi-topic+gaps) + audit (crash-safety, round-trip,
  FSRS-determinism) đều SẠCH → lợi-suất-bug của tự-động đã tới giới hạn. Phần còn lại cần trigger/người.
verified: true
method: ran-command
status: active
```


---

## NOTE-029 — Bài học process: lệnh-GHI dùng để kiểm chứng đã mutate vault THẬT → phải khôi phục

```yaml
id: NOTE-029
type: note
date: 2026-07-04
title: "Chạy /resume để 'valid' START_HERE đã ghi open_session vào learning_vault THẬT → đã khôi phục sạch"
spec_ref: "an toàn dữ liệu người dùng; DEC-047 (validate START_HERE)"
summary: >
  Khi kiểm 'lệnh trong START_HERE chạy đúng không', chạy `session.py resume` trên learning_vault THẬT →
  resume là lệnh GHI (CR-0003/DEC-028: mở open_session) → để lại 3 side-effect trên vault thật:
  (1) vault_state.md: open_session.lesson_id set + utc_offset quoted→unquoted (safe_dump round-trip);
  (2) thư mục .tx/ RỖNG (commit dọn tx_id, chừa .tx cha); (3) transaction_log.md (materialize_log).
  Khôi phục vault_state.md ban đầu CHỈ sửa (1) → full suite ĐỎ 1 test (test_bad_grade_raises_no_transaction:
  copy vault kèm .tx rỗng → assert not .tx.exists() fail). Chính 'valid thật kỹ' (full suite) BẮT được
  cleanup thiếu. Sau đó xóa .tx + transaction_log.md → learning_vault về đúng gốc (chỉ topics + vault_state.md);
  full suite 370 passed, validator PASS.
lesson: >
  Validation/demo KHÔNG được để lại thay đổi trên DỮ LIỆU NGƯỜI DÙNG. Lệnh-GHI (resume/review/done/forget/
  learn/source/ask) để lại NHIỀU artifact: state file + .tx/ (rỗng) + transaction_log.md. Khôi phục phải dọn
  ĐỦ CẢ BA, không chỉ state file. Dùng lệnh CHỈ-ĐỌC (status/schedule/gaps/validate) cho kiểm chứng; nếu buộc
  chạy lệnh-GHI thì làm trên VAULT COPY TẠM (như mọi pilot trước). Bài học kép: (a) side-effect rộng hơn 1 file;
  (b) full suite là lưới bắt cleanup-thiếu — luôn chạy sau khi đụng vault thật.
verified: true
method: ran-command
status: active
```


---

## NOTE-030 — Soạn CR-0005 (roadmap) + CR-0006 (buổi-ôn) dạng PENDING theo §12; kèm khuyến nghị trung thực

```yaml
id: NOTE-030
type: note
date: 2026-07-04
title: "2 tính năng 'tiện dụng' người dùng muốn → formalize thành CR pending (design-first, chưa code); phân tích bản chất"
spec_ref: "§12 (change request); §14 (Sessions); yêu cầu người dùng (roadmap + file-ôn-mỗi-buổi)"
summary: >
  Theo design-first: 2 tính năng người dùng mô tả (lộ trình + file-ôn-mỗi-buổi) đụng cấu trúc/hành vi → soạn
  CR pending để owner valid THIẾT KẾ trước khi build (đúng 'chuẩn bị thiết kế rồi mới triển khai'). Đã đọc
  spec để phân tích BẢN CHẤT (không bịa):
  - CR-0005 (Lộ trình): THỰC SỰ MỚI (spec không có roadmap cấp-topic). Khuyến nghị CÓ nhưng LIGHT-TOUCH —
    section '## Lộ trình' trong topic.md (content optional), AI-authored, KHÔNG nâng thành INV cứng v1
    (tránh coupling). Cần tạo topic.template.md + sửa cmd_learn.
  - CR-0006 (file-ôn-mỗi-buổi): nhu cầu ĐÃ ĐƯỢC ĐÁP ỨNG bởi lesson.md '## Sessions' (spec §14 dòng
    1026/1142/1383: mỗi buổi = block '### Session <ngày>'; /resume,/status đọc buổi gần nhất). Khuyến nghị
    KHÔNG tạo file .md riêng (trùng lặp + xung đột INV-25 + phá giả định /resume) → TÁI DÙNG ## Sessions.
key_insight: >
  Phân biệt 'tính năng mới thật' (roadmap) vs 'nhu cầu đã có cơ chế' (file-ôn = ## Sessions). Với cái thứ 2,
  fix bản chất = KHÔNG thêm artifact, dùng cái đã validate — tránh nguồn-sự-thật-thứ-2 (anti-drift DEC-005/012).
status_process: >
  2 CR ở change_requests/pending/ — AI CHỈ ghi pending, chờ owner duyệt (pending/README). full suite 377
  passed (CR là markdown, không đụng test/validator). CHƯA code gì.
verified: true
method: read-source
status: active
```

## NOTE-031 — Đánh giá handoff test trên bản copy người dùng (kết luận: CHƯA đạt, không phải bug hệ)

```yaml
id: NOTE-031
type: note
date: 2026-07-05
title: "AI khác chạy trên copy C:\\Users\\toann\\Desktop\\ai-learning-system chỉ /learn rồi dừng — test CHƯA kết luận được"
summary: >
  Người dùng copy folder ra Desktop và cho một AI khác chạy. Người đánh giá (AI này) soi bản copy:
  - AI khác CHỈ chạy /learn tạo scaffold topic 'docker' (topic.md có ## Lộ trình 1 dòng, sources.md rỗng,
    lesson_notes template). KHÔNG dạy: lesson.md ## Sessions trống, lesson_state status=not_started,
    review_items=[], mastery 5 trục=0. KHÔNG /done. Để open_session treo. KHÔNG tạo HANDOFF_RESULT.md.
  - Copy mang kèm .venv + .pytest_cache + 111 __pycache__ (trái HANDOFF_TEST §7 — nên loại khi zip).
  - validator full scope trên copy: pass:true; .tx rỗng → TOÀN VẸN OK (không bug hệ).
verdict: >
  Test CHƯA kết luận (mới /learn rồi dừng). Không cần sửa code hệ. Xử lý = làm lại test cho đúng.
lessons:
  - "Copy để test portability THẬT phải LOẠI .venv/.pytest_cache/__pycache__ (buộc AI kia tự bootstrap) — nếu không, phần cốt lõi 'dựng lại môi trường' không được kiểm."
  - "PHẦN B (dạy thật) cần NGƯỜI HỌC thật ngồi trả lời — AI kia không tự hoàn thành một mình được."
  - "Câu hỏi phụ KHÔNG có file riêng — ở ## Hỏi phụ trong lesson.md (giải thích cho người dùng, xem DEC-056)."
verified: true
method: ran-command
status: active
```

---

## NOTE-032 — Nghiên cứu nguồn học thật trên mạng (nền cho R1/R4 + TRD-006)

```yaml
id: NOTE-032
type: note
date: 2026-07-05
title: "Repos/nguồn để dựng giáo trình + lộ trình Docker mẫu (web search, có dẫn nguồn)"
summary: >
  Tra web (có cite): nguồn tốt để dựng giáo trình — roadmap.sh + kamranahmedse/developer-roadmap (thứ tự
  học), EbookFoundation/free-programming-books (tài liệu chiều sâu), practical-tutorials/project-based-learning
  (đề bài thực hành → exam), donnemartin/system-design-primer (nội dung sâu), freeCodeCamp (ý tưởng bài),
  + tài liệu chính chủ (vd docker.com/learning-paths) để đối chiếu độ chính xác.
docker_path_10_diem: >
  (1) nền Linux CLI → (2) vì sao Docker + kiến trúc client/daemon/registry → (3) container & image →
  (4) Dockerfile & build & Hub → (5) volumes/bind mounts → (6) networking → (7) Compose →
  (8) tối ưu (multi-stage, .dockerignore) → (9) bảo mật/debug/logging → (10) Swarm→Kubernetes.
  Cổng 1–7 = 'biết dùng'; 8–10 = 'production'.
decision_link: "Dùng ON-DEMAND (TRD-006) — đăng ký nguồn + kéo lát cắt liên quan, không clone bulk."
verified: true
method: ran-command
status: active
note: "Thứ tự/tên chủ đề từ roadmap = Class A/B dùng được; độ chính xác NỘI DUNG để chấm = Class D (ưu tiên nguồn chính chủ + người/AI kiểm)."
```

## NOTE-033 — ĐÍNH CHÍNH DEC-055: Task 2 (schema) + CR-0007 ĐÃ áp (phát hiện qua kiểm code thật)

```yaml
id: NOTE-033
type: note
date: 2026-07-05
title: "Đính chính: DEC-055 ghi 'CHƯA code' nhưng thực tế Task 2 (schema curriculum+exam_results) ĐÃ hiện thực + CR-0007 ĐÃ approved; full suite 384→386"
summary: >
  Khi bắt đầu Task 2, đọc models.py để làm RED-first thì PHÁT HIỆN code đã có sẵn: models Curriculum/
  CurriculumPoint/ExamResults/ExamResult; schemas/curriculum.schema.md + exam_results.schema.md; validate.py
  đã thêm 'curriculum.md'/'exam_results.md' vào _SYSTEM_DATA_NAMES (INV-18); test_schemas_consistency đã có
  curriculum+exam_results trong MODEL_BY_SCHEMA. change_requests/approved/ có cr-0007 (status approved,
  date_decided 2026-07-05, THAM CHIẾU DEC-055); changelog có 1 dòng cr-0007 (không lặp). pending còn cr-0008,
  cr-0009. grep xác nhận Task 3+ CHƯA làm (không có _check_curriculum/E-CURR/cmd_curriculum...).
verified_state (ran-test):
  - "full suite = 386 passed (turn trước 384; +2 = drift-guard curriculum + exam_results)."
  - "test_schemas_consistency 8 passed (gồm curriculum, exam_results)."
  - "validate --scope full trên vault ship = pass (chưa kiểm lại turn này — sẽ chạy)."
timeline_honesty: >
  Việc áp Task 2 + move CR-0007 approved XẢY RA GIỮA turn trước (tôi chạy 384) và turn này (386), KHÔNG nằm
  trong chuỗi thao tác tôi tự thực hiện turn này. Nhiều khả năng do trình thực-thi-task/hook của Kiro hoặc
  owner áp (cr-0007 approved trùng khớp nội dung bản pending tôi viết + tham chiếu DEC-055 → là công việc của
  chính luồng feature này, đã áp). CHƯA xác định chắc chắn tác nhân → cần owner xác nhận (chống xung đột đồng thời).
corrections:
  - "DEC-055 câu 'CHƯA code' + 'CR-0007 pending' KHÔNG còn đúng: Task 2 XONG + CR-0007 APPROVED. Phần 'chưa code' nay chỉ đúng cho Task 3..11."
  - "NOTE-003 baseline cập nhật 384 → 386."
next: "Trước khi làm Task 3 (validator E-CURR RED-first): owner xác nhận ai đã áp Task 2/CR-0007 (tránh 2 tác nhân sửa song song). Nếu chỉ mình tôi tiếp tục → Task 3 an toàn."
verified: true
method: ran-test
status: active
```

## NOTE-034 — Chuyển máy THẬT lần 2 (toann → k.nguyen.manh.toan): venv rebuild + re-verify TOÀN BỘ baseline

```yaml
id: NOTE-034
type: note
date: 2026-07-06
title: "Bản copy mở trên máy MỚI (k.nguyen.manh.toan): .venv cũ trỏ Python máy toann → dựng lại; 452 passed + validator PASS + selfcheck NGUYÊN VẸN trên máy mới"
spec_ref: "INV-16 (portability thuần-file); TRD-001 (transaction tự viết portable); nối tiếp NOTE-001"
summary: >
  Đơn vị ai-learning-system được mở trên máy mới (workspace C:\Users\k.nguyen.manh.toan\...\system-prompt\
  ai-learning-system). Đúng như NOTE-001 (nhưng chiều NGƯỢC lại): .venv mang theo đường dẫn tuyệt đối base
  interpreter của máy CŨ nên không chạy được. Đã dựng lại venv bằng Python hệ thống máy mới rồi tái kiểm
  TOÀN BỘ baseline — tất cả khớp con số transcript (452), nâng bằng chứng portability từ 'transcript' sang
  'ran-command/ran-test' trên MÁY THỨ HAI độc lập.
root_cause: >
  Không phải lỗi code. virtualenv KHÔNG relocatable: launcher .venv\Scripts\python.exe ghi cứng path base
  interpreter lúc tạo (máy toann: C:\Users\toann\scoop\apps\python313\current\python.exe). Copy sang máy khác
  → path đó không tồn tại. Đây là minh hoạ sống cho portability: phần DỮ LIỆU + CÔNG CỤ THUẦN-FILE (learning_vault,
  validator, spec, decision journal) mang đi hoàn hảo; chỉ .venv (môi trường máy) phải dựng lại — đúng thiết kế
  (venv nằm ngoài phần portable, luôn dựng lại từ pyproject/requirements).
resolution (ran-command):
  - "1) `.venv\\Scripts\\python.exe` báo: did not find executable at 'C:\\Users\\toann\\scoop\\apps\\python313\\current\\python.exe'."
  - "2) `py --version` → Python 3.11.9 (Python hệ thống máy mới; `python` là Store-alias không dùng được). requires-python '>=3.10' → 3.11 hợp lệ."
  - "3) Remove-Item -Recurse .venv; `py -m venv .venv` (Python 3.11.9)."
  - "4) pip install fsrs==6.3.1 pydantic>=2.13,<3 PyYAML>=6,<7 markdown-it-py>=4,<5 pytest → EXIT=0."
  - "5) pytest validator\\tests -q → 452 passed in 69.68s (KHỚP baseline transcript)."
  - "6) validate.py --system . --vault ..\\learning_vault --level full --scope full --at 2026-07-06T12:00:00+07:00 --json → {pass:true, errors:[], warnings:[]}."
  - "7) selfcheck.py → KẾT QUẢ CẤU TRÚC: NGUYÊN VẸN (14 file + 3 dir cốt lõi + Python 3.11.9 + .venv)."
note_on_python_version: >
  Máy cũ dùng Python 3.13 (scoop), máy mới 3.11.9. Cả hai hợp lệ (requires-python >=3.10) và cùng cho 452 passed
  → khẳng định thêm NOTE-002 (lock đa-phiên-bản) + tính bất biến hành vi trong dải Python hỗ trợ. KHÔNG regenerate
  lock (chỉ đổi máy/Python trong dải đã hỗ trợ, không nâng lib — theo NOTE-002 recommendation). Lần này cài KHÔNG
  --require-hashes (cài nhanh theo dải pyproject); nếu cần môi-trường-tin-cậy chặt thì dùng --require-hashes -r requirements.txt.
verified: true
method: ran-command
status: resolved
lesson: >
  Chuyển máy giữa phiên là chuyện BÌNH THƯỜNG với đơn vị này: luôn kiểm .venv trước (path máy cũ → dựng lại),
  rồi chạy selfcheck → pytest → validator để xác nhận NGUYÊN VẸN trước khi tiếp tục. Đừng tin con số transcript
  cho tới khi có output thật trên máy đang chạy.
reversible: "n/a (dựng lại môi trường; .venv luôn tái tạo từ pyproject/requirements)."
```

## NOTE-035 — Cross-AI handoff test ĐẠT (Claude Opus 4.6 via Antigravity): chấm R1–R7 + đóng NOTE-031

```yaml
id: NOTE-035
type: note
date: 2026-07-06
title: "AI KHÁC (Claude Opus 4.6, Antigravity IDE) chạy HANDOFF_TEST.md trên bản copy Desktop đến HẾT Phần A → ĐẠT rubric R1–R7; đóng NOTE-031 (lần trước AI kia chỉ /learn rồi dừng)"
spec_ref: "HANDOFF_TEST.md §6 rubric R1–R7; DEC-070 (hardening HANDOFF); NOTE-031 (attempt trước thất bại)"
summary: >
  Bản copy C:\\Users\\k.nguyen.manh.toan\\Desktop\\ai-learning-system đã được một AI KHÁC (Claude Opus 4.6
  qua Google Deepmind Antigravity IDE, chạy-được-lệnh) thực thi trọn HANDOFF_TEST.md (bản đã hardening
  DEC-070: Phần A1 lõi + A2 vòng giáo trình v2.7), để lại HANDOFF_RESULT.md tự-báo-cáo có dán output thật.
grading (chấm theo rubric §6):
  - "R1 selfcheck.py: ĐẠT — exit 0, 'NGUYÊN VẸN'."
  - "R2 pytest: 451 passed / 1 failed. Fail DUY NHẤT = test_bootstrap_pointers_all_exist (spec cha không đi theo copy) — KHÔNG phải regression hệ mà là TEST-DEFECT (over-assert pointer ngoài-đơn-vị), ĐÃ fix ở DEC-072. 451 test còn lại (validator/session/drift-guard/schema/E2E) xanh."
  - "R3 validate --scope full: ĐẠT — pass:true, errors:[] (toàn vẹn Class A giữ nguyên sau thao tác)."
  - "R4 audit + transaction_log: ĐẠT — 6 tx committed khớp từng bước self-report (learn/collect/curriculum/insert/next_lesson/grade), không dựng chuyện."
  - "R4b curriculum + exam_results: ĐẠT — insert-at hoán vị đúng (cp-001 order1, cp-003 order2 chèn, cp-002 order3); exam_results ref tương đối '../../../exam/git-basics/bai.txt' (portable); validate --scope full vẫn PASS."
  - "R5 dạy thật (Phần B): N/A — SOLO không người học, bỏ ĐÚNG luật (không tính trượt)."
  - "R6 decision mới: ĐẠT — AI kia ghi NOTE-035 trong journal của BẢN COPY (không phải workspace này)."
  - "R7 trung thực: ĐẠT (xuất sắc) — khai thẳng 1 test fail + friction PowerShell quoting JSON (double→single quote) + bỏ Phần B; không phóng đại."
verdict: >
  ĐẠT. Rubric: ĐẠT khi R1–R4b đạt + R7 trung thực (R5 bỏ được nếu SOLO). R3/R4b KHÔNG fail → HỆ GIỮ NGUYÊN
  TOÀN VẸN KHI SANG AI KHÁC (chính điều NOTE-031 chờ). Vết gợn duy nhất (R2 1-fail) là test-defect đã đóng
  bằng DEC-072 → bản copy portable sạch về sau sẽ 454/454.
findings:
  - "Bản copy Desktop CHƯA sạch: còn .venv (1) + __pycache__ (145) + .pytest_cache (1) — §7 HANDOFF_TEST yêu cầu bỏ. Nhẹ, không chặn (AI kia tự rebuild venv 3.11.9). Lần đóng gói sau nên loại 3 thứ này."
  - "NOTE-035 trong bản copy ≠ NOTE-035 này (workspace nguồn-sự-thật). Hai journal tách biệt; bản copy là artifact test, không merge ngược."
verified: true
method: ran-command
status: active
closes: "NOTE-031 → chuyển resolved: attempt handoff nay ĐẠT (Phần A trọn vẹn, trung thực). Class D (dạy thật, Phần B) vẫn cần người học — ngoài phạm vi test cơ chế."
```

## NOTE-036 — Cross-AI handoff #2 ĐẠT (Gemini 3.5 Flash via Antigravity): chấm R1–R7 + phát hiện bug tích hợp THẬT

```yaml
id: NOTE-036
type: note
date: 2026-07-06
title: "AI KHÁC (Gemini 3.5 Flash, Antigravity IDE) chạy HANDOFF_TEST.md trên bản copy 'ai-learning-system - Copy' đến HẾT Phần A → ĐẠT rubric; ĐIỂM CỘNG LỚN: phát hiện bug tích hợp E-EXAM-REF-BROKEN transaction-overlay mà pilot/E2E của ta bỏ sót (→ fix ở DEC-073)"
spec_ref: "HANDOFF_TEST.md §6 rubric R1–R7; DEC-070/072 (hardening HANDOFF + fix test-defect); NOTE-035 (handoff #1 Claude); DEC-073 (fix bug Gemini phát hiện)"
summary: >
  Bản copy '...\\ai-learning-system - Copy' (đã có fix DEC-072, baseline 454) được một AI KHÁC (Gemini 3.5
  Flash qua Antigravity, chạy-được-lệnh, Python 3.11.9 qua py) thực thi trọn HANDOFF_TEST Phần A, để lại
  HANDOFF_RESULT.md dán output thật. Đọc trực tiếp báo cáo đó (read-source) + TỰ tái kiểm bug qua probe
  RED-first trong workspace chính (ran-command) làm cơ sở chấm.
grading (chấm theo rubric §6):
  - "R1 selfcheck.py: ĐẠT — exit 0, 'NGUYÊN VẸN'."
  - "R2 pytest ban đầu: ĐẠT — 454 passed / 0 (fix DEC-072 hiệu quả, hết đỏ oan trên copy sạch). Sau khi Gemini chạy writes thật (git-basics/docker), test_shipped_vault_clean.py FAIL 2 test (topics_empty + pointers_null) — ĐÚNG THIẾT KẾ (vault ship bị bẩn do ghi topic), KHÔNG phải bug."
  - "R3 validate --scope full: ĐẠT — pass:true, errors:[] (bước 2 + bước 10 sau A2)."
  - "R4 audit + transaction_log: ĐẠT — các tx committed khớp từng bước self-report (learn/collect/curriculum/insert/next_lesson/grade)."
  - "R4b curriculum + exam_results: ĐẠT — insert-at hoán vị đúng; exam_results ref tương đối; validate --scope full PASS."
  - "R5 dạy thật (Phần B): N/A — SOLO không người học, bỏ ĐÚNG luật."
  - "R6 decision mới: Gemini ghi NOTE-036 trong journal của BẢN COPY (artifact test, KHÔNG merge ngược vào nguồn-sự-thật này)."
  - "R7 trung thực: ĐẠT (xuất sắc) — khai thẳng friction py-vs-python + JSON quoting PowerShell + bỏ Phần B + KHAI THẲNG đã tự sửa validate.py trong copy."
bug_found (điểm cộng lớn — pilot/E2E của ta BỎ SÓT):
  - "Gemini phát hiện E-EXAM-REF-BROKEN GIẢ: sau khi 1 topic có exam_results.md (từ /grade), lệnh FULL-transaction (vd /learn topic-mới) chạy validate trên overlay TEMP (thiếu sibling exam/) → resolve ref sai → abort oan. LÀ BUG TÍCH HỢP THẬT (tôi tái kiểm bằng probe: next_lesson committed False [E-EXAM-REF-BROKEN])."
  - "Fix của Gemini (trong copy) KHÔNG DÙNG: nó detect tên tempdir 'tx_overlay_' + hardcode Path(__file__).../exam → phá portability INV-16 (bỏ qua vault_root truyền vào). Workspace chính áp fix GỐC đúng ở DEC-073 (thread vault root THẬT, layout-agnostic)."
honesty_boundary: >
  TÔI KHÔNG trực tiếp quan sát Gemini chạy — chấm dựa trên đọc HANDOFF_RESULT.md của bản copy (read-source)
  + tái kiểm ĐỘC LẬP bản chất bug qua probe RED-first trong workspace chính (ran-command, bằng chứng mạnh
  nhất). Journal bản copy (NOTE-036 của copy) TÁCH BIỆT với entry này; không merge ngược.
evidence:
  - "read-source: '...\\ai-learning-system - Copy\\HANDOFF_RESULT.md' (bootstrap 454/0, A1+A2 output thật, mục Trung thực khai đã vá validate.py + shipped_vault_clean fail đúng-thiết-kế)."
  - "read-source: '...- Copy\\_system\\validator\\validate.py' — fix hack của Gemini (if 'tx_overlay_' in str(vault_root): Path(__file__)...) → xác nhận không phù hợp portability."
  - "ran-command (workspace chính, tái kiểm bug): probe curriculum+grade→exam_results.md→next_lesson(FULL) TRƯỚC fix = committed False [E-EXAM-REF-BROKEN]; SAU fix DEC-073 = committed True []."
verified: true
method: read-source
status: active
```

## NOTE-037 — Chuyển máy THẬT lần 3 (k.nguyen.manh.toan → toann): venv rebuild qua scoop py313 + re-verify baseline

```yaml
id: NOTE-037
type: note
date: 2026-07-06
title: "Workspace về lại máy 'toann' (C:\\Users\\toann\\...). .venv cũ trỏ Python máy k.nguyen.manh.toan + py launcher KHÔNG có → dựng lại venv bằng scoop python 3.13.12; re-verify 454 passed TRƯỚC khi fix DEC-073"
spec_ref: "NOTE-001/002/034 (chuyển máy + venv không relocatable + lock đa-phiên-bản); INV-16 (portability)"
summary: >
  Tiếp tục từ end.md (phiên trước trên máy k.nguyen.manh.toan). Trên máy toann hiện tại: .venv\\Scripts\\
  python.exe báo 'No Python at ...k.nguyen.manh.toan...Python311' (venv KHÔNG relocatable, đúng NOTE-001);
  `py` launcher KHÔNG cài trên máy này ('No installed Python found'). Python khả dụng = scoop
  C:\\Users\\toann\\scoop\\apps\\python313\\current\\python.exe (3.13.12). Dựng lại venv bằng python đó +
  pip install fsrs==6.3.1/pydantic/PyYAML/markdown-it-py/pytest (dải pyproject >=3.10, 3.13 hợp lệ — NOTE-002).
  Re-verify TOÀN BỘ TRƯỚC khi sửa gì: pytest 454 passed; validate --scope full --at pass:true errors:[]
  warnings:[]; selfcheck NGUYÊN VẸN. Chỉ .venv dựng lại (đúng thiết kế INV-16); dữ liệu+journal thuần-file
  mang đi nguyên vẹn.
lesson: >
  Máy toann dùng scoop (không có 'py' launcher như máy k.nguyen.manh.toan). Lệnh chuẩn phiên sau nếu còn ở
  máy toann: dựng venv bằng đường dẫn scoop python313 (KHÔNG dùng 'py'). Vẫn: kiểm .venv trước → rebuild →
  selfcheck → pytest → validator để xác nhận NGUYÊN VẸN trước khi tiếp tục.
evidence:
  - "ran-command: .venv\\Scripts\\python.exe --version → 'No Python at ...k.nguyen.manh.toan...Python311'; py --version → 'No installed Python found'."
  - "ran-command: Get-Command python → C:\\Users\\toann\\scoop\\apps\\python313\\current\\python.exe (3.13.12)."
  - "ran-command: rebuild venv + pip install → pytest 454 passed; validate --scope full --at 2026-07-06T12:00:00+07:00 pass:true; selfcheck NGUYÊN VẸN."
verified: true
method: ran-command
status: resolved
reversible: "n/a (sửa môi trường; .venv luôn dựng lại từ pyproject/requirements)."
```

## NOTE-038 — Audit đối kháng tính năng blueprint: KHÔNG bug + 6 regression bền (đồng bộ vào notes.md)

```yaml
id: NOTE-038
type: note
date: 2026-07-07
title: "Audit đối kháng Topic_Blueprint (chủ động, theo phương pháp đã lộ DEC-073) — KHÔNG tìm thấy bug; thành 6 regression bền test_blueprint_audit.py"
spec_ref: "mandatory-curriculum-framework; DEC-073/074/075; NOTE-036 (bài học E2E happy-path bỏ sót bug tích hợp)"
reconcile_note: >
  Entry này ĐÃ có dòng cuộn trong index.yaml (mục NOTE-038) từ phiên blueprint, NHƯNG khối đầy đủ CHƯA được
  ghi vào notes.md (phiên đó chỉ cập nhật index.yaml). Phiên này (toann/py3.13.12) bổ sung khối đầy đủ để
  đồng bộ file ↔ index (kỷ luật README: 'ghi vào file loại tương ứng VÀ cuộn vào index.yaml'). Nội dung
  đã TÁI KIỂM: 6 test thuộc test_blueprint_audit.py nằm trong 505 passed chạy thật phiên này.
summary: >
  Sau khi blueprint hoàn tất, chủ động audit đối kháng (đúng phương pháp đã giúp Gemini lộ bug DEC-073 mà
  E2E happy-path bỏ sót). Probe các khoảng E2E happy-path chưa phủ, biến thành 6 regression BỀN
  (test_blueprint_audit.py). KHÔNG tìm thấy bug — báo trung thực.
scenarios_locked:
  - "A1: /done auto-advance DƯỚI blueprint approved (DEC-065 × blueprint) — _check_blueprint chạy trong transaction-overlay FULL, area_refs bảo toàn, coverage giữ → commit PASS."
  - "A2: overlay tường minh KHÔNG false-positive (blueprint/curriculum nằm TRONG vault, khác exam/ sibling NGOÀI vault của DEC-073 → overlay-an-toàn by-construction)."
  - "A3: robustness blueprint.md sửa-tay-hỏng (areas=chuỗi / status ngoài enum) → E-SCHEMA sạch, KHÔNG crash (lớp DEC-071, qua _load_blueprint_validated)."
  - "A4: INV-16 — source_refs abspath → E-PORT-ABSPATH."
  - "A5: tất định thứ tự phát mã E-BP-*."
  - "A6: amend approved XÓA area đang-được-curriculum-tham-chiếu → E-BP-AREA-REF-BROKEN → rollback (toàn vẹn tham chiếu giữ vững)."
conclusion: >
  Tầng blueprint VỮNG dưới tích hợp + overlay + robustness. KHÔNG như DEC-073 (lần đó exam/ là sibling NGOÀI
  vault nên overlay sinh false-positive); blueprint nằm TRONG vault → overlay an toàn by-construction, nay có
  test khoá lại. 499→505 passed (+6).
evidence:
  - "read-source: validator/tests/phase12/test_blueprint_audit.py (6 test A1–A6)"
  - "ran-test (phiên này): full suite 505 passed (6 test audit nằm trong đó); validate --scope full pass:true"
verified: true
method: ran-test
status: active
reversible: "n/a (thêm regression test; gỡ chỉ làm giảm độ phủ)"
```

---

## NOTE-039 — ⚠️ Giới hạn workflow: KHÔNG áp được blueprint approved lên curriculum ĐÃ teachable (không có retrofit area_refs)

```yaml
id: NOTE-039
type: note
date: 2026-07-07
title: "Blueprint-first là luồng DUY NHẤT đi được: curriculum teachable dựng TRƯỚC (không area_refs) → không approve blueprint về sau + không có lệnh gắn area_refs cho point đã có"
spec_ref: "mandatory-curriculum-framework R2/R3/R5.1/R5.4; DEC-074/075; TRD-008 (quyết định xử lý); E-BP-POINT-OUTSIDE/E-BP-AREA-UNCOVERED"
finding: >
  Truy vết luồng approve (đọc code THẬT phiên này, không đoán). Nếu topic đã có curriculum teachable KHÔNG
  mang area_refs, rồi mới muốn áp một blueprint approved lên topic đó:
    - approve chạy transaction-FULL → _check_blueprint (coverage teachable-gated, DEC-075) kích vì
      curriculum.teachable==true → mọi point cũ thiếu area_refs vi phạm E-BP-POINT-OUTSIDE + các mandatory
      area chưa phủ vi phạm E-BP-AREA-UNCOVERED → transaction ABORT → approve KHÔNG thành (blueprint giữ draft).
    - KHÔNG có lệnh nào gắn/sửa area_refs cho Curriculum_Point ĐÃ CÓ: cmd_curriculum TỪ CHỐI nếu curriculum.md
      tồn tại ('chỉ DỰNG mới'); cmd_curriculum_insert chỉ THÊM point mới (mang area_refs), không sửa point cũ.
  ⇒ Ngõ cụt: curriculum-first (teachable) rồi áp-khung-về-sau KHÔNG đi được.
root_cause (KHÔNG phải ngọn): >
  Bản chất là THIẾU NĂNG LỰC (không có đường retrofit area_refs), KHÔNG phải bug. Validator ép ĐÚNG bất biến:
  R3.3 (còn mảng bắt buộc chưa phủ → giữ chưa-teachable) + R5.1/R5.2 (point phải map area khi blueprint
  approved). Cổng coverage=teachable-gate (DEC-075) là thiết kế đúng (tránh brick-vault). Vấn đề chỉ là
  KHÔNG có công cụ đưa curriculum-đã-lỡ-teachable vào trạng thái phủ đủ.
not_a_bug_not_a_violation: >
  (1) KHÔNG phải bug — validator đúng R3/R5 (đã probe xác nhận phiên trước). (2) KHÔNG vi phạm requirements —
  R5.4 backward-compat (no-blueprint/draft → hành vi cũ) vẫn giữ; KHÔNG requirement nào bắt buộc retrofit;
  R2 hình dung dựng blueprint 'khi bắt đầu topic' (blueprint-first). (3) vault ship RỖNG → không ai bị kẹt.
supported_workflow: >
  BLUEPRINT-FIRST: /blueprint <topic> (dựng draft) → [tùy chọn --approve] → /curriculum <topic> với area_refs
  trỏ các Mandatory_Area → (nếu blueprint còn draft) /blueprint --approve. Vì area_refs được nhập NGAY lúc
  dựng curriculum, coverage phủ đủ → teachable + approve đều PASS. (Có thể dựng curriculum khi blueprint còn
  DRAFT: E-BP-AREA-REF-BROKEN vẫn ép ref hợp lệ, nhưng coverage chưa ép tới khi approved + teachable.)
disposition: "Xử lý theo TRD-008 = GHI NHẬN ràng buộc (blueprint-first), CHƯA xây retrofit. Nếu owner muốn luồng curriculum-first→áp-khung → mở CR (phương án B của TRD-008)."
evidence:
  - "read-source (phiên này): session.py cmd_curriculum '~L751 if cpath.is_file(): raise SessionError(... chỉ DỰNG mới)'"
  - "read-source: session.py cmd_curriculum_insert (chỉ insert point mới; đọc area_refs từ --point JSON; không có nhánh sửa area_refs point cũ)"
  - "read-source: spec §3.6 dòng 232 'Phủ là CỔNG của teachable ... chỉ ép khi approved VÀ teachable==true'"
  - "cross-ref: TRD-008 (quyết định), DEC-075 (cổng teachable)"
verified: true
method: read-source
status: resolved
resolution: >
  ĐÃ GIẢI ngày 2026-07-08 (owner chọn phương án B của TRD-008): thêm lệnh retrofit
  /curriculum --set-area-refs <cp-id> --area-refs <json> (CR-0015/DEC-076) — gắn/sửa area_refs cho điểm ĐÃ CÓ.
  Luồng curriculum-first→áp-khung nay đi được: retrofit dưới blueprint draft từng điểm → /blueprint --approve.
  E2E test_e2e_retrofit_blueprint.py chứng minh (513 passed). Ngõ cụt KHÔNG còn.
reversible: "Đảo = gỡ CR-0015/DEC-076 → quay lại ràng buộc blueprint-first (ghi nhận ở entry này)."
```

---

## NOTE-040 — Chuyển máy THẬT lần 4 (về toann) + re-verify baseline 505 phiên này + quan sát bản sao system-prompt2

```yaml
id: NOTE-040
type: note
date: 2026-07-07
title: "Máy toann phiên này: .venv trỏ máy cũ (k.nguyen.manh.toan) → rebuild scoop py3.13.12; re-verify 505 passed + validate PASS + selfcheck NGUYÊN VẸN. Phát hiện thư mục CHA có git repo sẵn (từ phiên blueprint) + bản sao lồng system-prompt2/"
spec_ref: "INV-16 (portable, venv không mang theo); NOTE-001/034/037 (chuỗi chuyển máy); DEC-074 (git init ở thư mục cha)"
summary: >
  Tiếp quản trên máy toann (workspace C:\\Users\\toann\\Desktop\\WORK_PRO\\system-prompt). .venv mang theo
  đường dẫn interpreter máy cũ 'k.nguyen.manh.toan\\...\\Python311' + không có 'py' launcher trên toann
  (giống NOTE-037 chiều ngược). Dựng lại venv bằng scoop python 3.13.12
  (C:\\Users\\toann\\scoop\\apps\\python313\\current\\python.exe) + pip install --require-hashes -r
  requirements.txt + pip install pytest. Re-verify TOÀN BỘ: selfcheck NGUYÊN VẸN, pytest 505 passed,
  validate --scope full pass:true errors:[] warnings:[]. Chỉ .venv dựng lại (đúng INV-16); dữ liệu + code +
  journal thuần-file mang đi nguyên vẹn.
git_state_observed: >
  Thư mục CHA (system-prompt/) ĐÃ là git repo (khởi tạo ở phiên blueprint — DEC-074), HEAD ở commit 788b440
  'audit: adversarial blueprint audit ... [505 passed]' với 9 commit từ baseline da15d9b. git status: end.md
  modified (do đọc/đối chiếu) + system-prompt2/ untracked. → khác NOTE-001/034/037 (lúc đó KHÔNG phải git repo).
system_prompt2_observation: >
  Có thư mục system-prompt/system-prompt2/system-prompt/ai-learning-system/ — một BẢN SAO LỒNG NHAU của cả
  dự án (chứa StarHillGuestApp/VisionPlatform cùng cấp → có vẻ là backup/workspace khác của owner). Bản sao
  này LÀM Ô NHIỄM grep/file_search (khớp trùng đường dẫn). CẢNH BÁO cho AI phiên sau: LUÔN dùng
  excludePattern 'system-prompt2/**' khi grep/search để chỉ làm trên dự án CHÍNH. KHÔNG tự xóa system-prompt2
  (có thể là backup có chủ đích của owner — thao tác xóa là hard-to-reverse, cần owner xác nhận).
python_version_note: >
  Máy này 505 passed trên Python 3.13.12; chuỗi lịch sử: NOTE-034 (3.11 lẫn 3.13 đều 452), NOTE-037 (3.13.12,
  454). Khẳng định lại NOTE-002 (lock đa-phiên-bản, wheel cp313 có sẵn) + bất biến hành vi cross-Python trong
  dải requires-python '>=3.10'.
evidence:
  - "ran-command (phiên này): .venv\\Scripts\\python cũ báo 'No Python at ...k.nguyen.manh.toan\\...Python311'; where.exe python → scoop\\apps\\python313; python -m venv .venv (3.13.12)"
  - "ran-command: pip install --require-hashes -r requirements.txt → Successfully installed fsrs-6.3.1 pydantic-2.13.4 ... ; pip install pytest"
  - "ran-command: selfcheck.py → 'KẾT QUẢ CẤU TRÚC: NGUYÊN VẸN'"
  - "ran-test: pytest validator/tests → 505 passed; validate.py --scope full --json → pass:true, errors:[], warnings:[]"
  - "ran-command: git log --oneline → HEAD 788b440 (9 commit); git status → 'M end.md', '?? system-prompt2/'"
verified: true
method: ran-test
status: active
reversible: "n/a (việc môi trường; .venv luôn dựng lại từ requirements.txt)"
```
