# (2) Những chỗ AI phải ĐỔI so với yêu cầu/spec ban đầu

Các điểm spec ban đầu (v2.5) không khả thi hoặc sai giả định khi gặp thực tế thư viện/nền tảng,
buộc phải đổi. Mọi thay đổi đều được gói vào change request nâng spec (→ v2.6).

---

## DEV-001 — Bỏ giả định `State.New` của FSRS (F-A)

```yaml
id: DEV-001
type: deviation
date: 2026-07-01
title: "py-fsrs KHÔNG có State.New → đổi mô hình trạng thái 'chưa review'"
spec_ref: "spec v2.5 mục 5.1/6.2 (giả định card.state == New)"
summary: >
  Spec v2.5 giả định tồn tại trạng thái New. Thực tế py-fsrs 6.3.1 chỉ có
  State = {Learning:1, Review:2, Relearning:3}. Đổi: 'chưa review' được biểu diễn bằng
  last_review is None / review_log == [] / stability is None, KHÔNG bằng một State.New.
rationale: >
  Không thể dùng thứ thư viện không có. Bám API thật thay vì ép spec lên thư viện.
  Đây là 'dùng tool của họ, không tự chế lại' đúng như định hướng.
evidence:
  - "repo_lab/repo_evaluations/fsrs.md: 'F-A (schema): py-fsrs KHÔNG có State.New ...'"
  - "repo_lab/repo_evaluations/fsrs.md SPIKE Q4/State enum: '{Learning,Review,Relearning} — không có New'"
verified: true
method: read-source
status: active
reversible: "Không nên đảo — sẽ mâu thuẫn API thư viện thật."
```

---

## DEV-002 — So sánh theo `due_date` thay vì `due_at_utc` exact (F-B)

```yaml
id: DEV-002
type: deviation
date: 2026-07-01
title: "Không quantize stability-trước-due được cross-platform → chuẩn hoá về due_date (ngày)"
spec_ref: "spec v2.5 mục 8.3 / INV-08 (đòi quantize stability TRƯỚC khi tính due + so due_at_utc exact)"
summary: >
  py-fsrs tính due nội bộ trong review_card từ stability (float siêu việt), KHÔNG có hook để
  quantize trước khi ra due. Spec v2.5 đòi so due_at_utc chính xác tuyệt đối → không khả thi
  sạch cross-platform. Đổi: dùng due_date (mức ngày) làm chuẩn so cho trạng thái Review.
rationale: >
  Float transcendental cross-platform không đảm bảo bit-khớp; ép exact sẽ sinh sai lệch giả.
  Chuẩn hoá về ngày là mức chính xác vừa đủ, ổn định, kiểm chứng được — bản chất bài toán ôn tập
  theo ngày chứ không theo micro giây.
evidence:
  - "repo_lab/repo_evaluations/fsrs.md: 'F-B (determinism): ... KHÔNG có hook quantize-trước-due ... chuyển sang so due_date'"
  - "repo_lab/repo_evaluations/fsrs.md risks: 'due tính bên trong review_card từ stability float → cross-platform boundary'"
verified: true
method: read-source
status: active
reversible: "Chỉ đảo nếu py-fsrs mở API quantize-trước-due; hiện không có."
```

---

## DEV-003 — Nâng spec v2.5 → v2.6 để hợp thức hoá DEV-001/DEV-002

```yaml
id: DEV-003
type: deviation
date: 2026-07-01
title: "Đóng gói DEV-001 + DEV-002 thành change request nâng spec lên v2.6"
spec_ref: "spec v2.5 → v2.6"
summary: >
  Hai phát hiện F-A/F-B ảnh hưởng SPEC nên không sửa lén trong code mà được nâng thành phiên bản
  spec v2.6 (đúng quy trình change-request của dự án).
rationale: >
  Thay đổi chạm spec phải đi qua thay đổi spec có phiên bản, không sửa nóng — để truy vết và
  giữ nhất quán 'nguồn sự thật'.
evidence:
  - "change_requests/approved/cr-0001-fsrs-spec-v2.6.md — CR chính thức (ghi hồi tố, DEC-010)"
  - "PROMPT_LEARNING_SYSTEM.md header: 'vá theo SPIKE FSRS thật v2.6 ngày 2026-07-01 (F-A ...; F-B ...)'"
  - "repo_lab/repo_evaluations/fsrs.md: F-A/F-B + '→ gói vào change request nâng spec v2.6'"
verified: true
method: read-source
status: active
note: "Vết CR đã được hợp thức hoá bởi DEC-010/CR-0001 (trước đó chỉ ở mức transcript)."
reversible: "n/a"
```

---

## DEV-004 — Version schema dùng SỐ NGUYÊN, không phải "semver" như spec INV-19 ghi

```yaml
id: DEV-004
type: deviation
date: 2026-07-03
title: "INV-19 spec ghi 'semver' nhưng code dùng int; đã chốt int (spec tự mâu thuẫn)"
spec_ref: "spec INV-19 (ghi 'semver'); validate.py._check_schema_version"
summary: >
  Spec INV-19 dùng chữ 'semver' cho schema_version, nhưng model + validator hiện dùng SỐ NGUYÊN
  (schema_version: int; _system/VERSION = '1'). Code chốt int và ghi chú rằng dòng 'semver' của spec là
  tự mâu thuẫn cần dọn. Planner P11 (DEC-011) cũng theo int (bước vN_to_vN+1 liên tiếp).
rationale: >
  Migration vN→vN+1 (spec 10.7) và so sánh <, > cần thứ tự toàn phần đơn giản; int đủ và nhất quán
  giữa models.py, validate.py, VERSION, planner. 'semver' sẽ thừa và mập mờ (không ai định nghĩa
  cách so minor/patch cho schema vault).
evidence:
  - "validator/validate.py: comment '_check_schema_version' — 'Dùng SỐ NGUYÊN ... spec ghi \"semver\" là dòng tự mâu thuẫn cần dọn'"
  - "validator/models.py: schema_version: int (mọi model doc)"
  - "_system/VERSION = '1'; test_inv19_version.py dùng int"
verified: true
method: read-source
status: active
todo: "Dọn từ 'semver' trong spec INV-19 → 'số nguyên' qua change request để spec khớp code (hiện code là chân lý)."
reversible: "n/a"
```

---

## DEV-005 — `/resume` chuyển từ CHỈ-ĐỌC sang GHI (đảo một phần DEC-016) qua CR-0003

```yaml
id: DEV-005
type: deviation
date: 2026-07-04
title: "/resume mở phiên (ghi open_session) thay vì chỉ đọc — sửa mâu thuẫn commands.md ↔ §5.4/§11B.2"
spec_ref: "spec §5.4, §11B.2 (/resume mở lại phiên học); commands.md (trước đây ghi /resume 'chỉ đọc')"
summary: >
  DEC-016 ban đầu chốt /resume read-only (cửa vào 11B, chỉ tóm tắt trạng thái). Nhưng §5.4/§11B.2 nói
  /resume MỞ LẠI phiên — tức phải GHI open_session. commands.md (registry) cũng ghi sai '/resume chỉ đọc',
  mâu thuẫn spec. Đổi: /resume nay chạy transaction-LIGHT set open_session.lesson_id/started_at trên
  current_lesson (no-op nếu không có current_lesson), trả (committed, report|None, info) thay vì dict thuần.
  Đây là ĐỔI bề mặt lệnh (read→write) nên đi qua change request CR-0003 (đúng kỷ luật §12, không sửa nóng).
rationale: >
  Nguồn sự thật là spec §5.4/§11B.2; commands.md và DEC-016 lệch spec ở điểm này. Sửa cho khớp bản chất
  'resume = tiếp tục phiên' (phải có phiên mở để /status theo dõi + /done đóng). LIGHT (không FULL) vì chỉ
  đụng vault_state.open_session, không chạm FSRS/view/cross-ref — đúng phân loại transaction §10.8.
  Giữ no-op an toàn khi chưa có lesson để tránh mở phiên rỗng.
evidence:
  - "change_requests/approved/cr-0003-resume-opens-session.md — CR chính thức"
  - "change_requests/changelog.md — dòng cr-0003"
  - "commands.md: dòng /resume đổi 'chỉ đọc' → 'vault_state.open_session (transaction-LIGHT)'"
  - "validator/session.py cmd_resume(vault, system, at) → (committed, rep|None, info); _READONLY_COMMANDS bỏ 'resume'; main() có nhánh write riêng"
  - "tests/phase10/test_session_status_resume.py: test_resume_returns_info_and_opens_session (write) + test_status_readonly (status vẫn read-only)"
  - "ran-test: 316 passed; validator full scope pass:true"
supersedes_part_of: DEC-016
verified: true
method: ran-test
status: active
reversible: "Đảo bằng cách revert CR-0003 + trả cmd_resume về read-only; nhưng sẽ tái mâu thuẫn spec §5.4/§11B.2."
```

## DEV-006 — Nâng spec v2.6 → v2.7 (thêm học-theo-giáo-trình) qua CR-0009

```yaml
id: DEV-006
type: deviation
date: 2026-07-06
title: "Sửa spec gốc PROMPT_LEARNING_SYSTEM.md: thêm khái niệm Curriculum nhiều bài + vùng reference/ + vùng exam/ (§3.2/§3.4/§3.5/§11A.2/§14), bump v2.6→v2.7, qua CR-0009 approved"
spec_ref: "CR-0009 approved; spec curriculum-driven-learning (.kiro/specs); DEC-055; CR-0007/0008; DEV-003 (tiền lệ bump spec qua CR)"
change: >
  Spec v2.6 hình dung 'một topic nhiều lesson' nhưng KHÔNG mô tả cơ chế giáo trình, vùng reference/, vùng
  exam/ → tính năng curriculum-driven-learning (đã hiện thực CR-0007/0008, 433 test PASS) thiếu gốc spec.
  Đổi (chỉ THÊM, tương thích ngược): (1) tiêu đề + dòng trạng thái v2.6→v2.7; (2) §3.2 layout topic thêm
  curriculum.md/reference//exam_results.md (đều TÙY CHỌN); (3) §3.4 mới: reference/ chỉ .md on-demand +
  exam/ NGOÀI vault (bài nộp có thể code, chỉ exam_results.md metadata trong vault — diễn giải INV-17);
  (4) §3.5 mới: Curriculum/Curriculum_Point + teachable + topic_state.lessons[] vẫn nguồn sự thật index
  (INV-25) + Curriculum_Validator 7 mã lỗi Class A; (5) §11A.2 +5 lệnh; (6) §14 bước 4b auto-advance.
rationale: >
  Spec là 'hiến pháp' → đổi phải qua CR §12 (không sửa nóng), như DEV-003 (v2.5→v2.6). Áp SAU khi code XANH
  để spec phản ánh đúng cái ĐÃ kiểm-được (tránh spec 'hứa' trước code — CR-0009 §5). Bump v2.7 là MINOR
  (thêm tính năng, không phá cấu trúc): topic không có curriculum.md vẫn hợp lệ, validator chỉ kích khi tồn
  tại. KHÔNG bump _system/VERSION (=1): curriculum/exam dùng schema_version:1 additive → không migration
  (khác bản chất semver tài liệu, xem DEV-004). Changelog cột VERSION v2.6→v2.7; DEC-055..067 là chuỗi hiện thực.
evidence:
  - "read-source: PROMPT_LEARNING_SYSTEM.md tiêu đề 'v2.7', §3.2 (curriculum.md/reference/ layout), §3.4/§3.5 (mục mới), §11A.2 (5 dòng lệnh mới), §14 bước 4b"
  - "read-source: change_requests/approved/cr-0009-...md (status approved, date_decided 2026-07-06, mục 6 liệt kê 6 sửa đổi); changelog.md dòng cr-0009 (VERSION v2.6→v2.7)"
  - "read-source: _system/VERSION giữ '1' (test_planner_up_to_date_with_real_system_version đọc =1 — không đổi)"
  - "ran-test: test_change_requests_scaffold 2 passed (states↔folders + cr-0001 vẫn khớp sau move cr-0009); full suite 433 passed (spec là tài liệu, không đổi hành vi code); validator full scope PASS (đã chạy các task trước)"
verified: true
method: ran-test
status: active
reversible: "Revert 6 khối sửa spec về v2.6 + move cr-0009 approved→(pending|rejected) + gỡ dòng changelog. Code CR-0007/0008 KHÔNG phụ thuộc chuỗi spec (drift-guard bám commands.md/validation_rules, không bám prose spec) → gỡ spec không làm đỏ test."
```
