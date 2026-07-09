# (1) Quyết định AI tự ra mà spec KHÔNG nói

Các lựa chọn AI tự quyết vì spec (`PROMPT_LEARNING_SYSTEM.md`) chỉ nói ở mức cao hoặc không đề cập.
Mỗi entry có `evidence` kiểm chứng được.

---

## DEC-001 — Tiêu chí cụ thể cho INV-17 (E-MIX-CODE: không code/deps trong vault)

```yaml
id: DEC-001
type: decision
date: 2026-07-03
title: "Chốt danh sách cụ thể thư mục/đuôi/tên-file cấm trong learning_vault"
spec_ref: "INV-17 (spec mô tả mức cao: 'không repo/dependency/code trong vault')"
summary: >
  Spec chỉ nêu nguyên tắc. AI tự chốt bộ tiêu chí cụ thể để enforce mà không bắt oan:
  thư mục cấm (.git, node_modules, .venv, __pycache__, dist, build, target, .pytest_cache...),
  đuôi code/binary (.py .js .ts .jar .exe .dll .so .whl .egg...), tên manifest deps
  (package.json, requirements.txt, pyproject.toml, cargo.toml, go.mod, uv.lock...).
  Bỏ qua vùng transient _scratch/ và .tx/ (INV-20).
rationale: >
  Tiêu chí mờ → hoặc bắt oan (vi phạm 'không bịa') hoặc bỏ sót. Danh sách tường minh +
  os.walk prune vừa nhanh vừa kiểm chứng được, không đụng file .md dữ liệu học hợp lệ.
evidence:
  - "validator/validate.py: hằng _VAULT_FORBIDDEN_DIRS / _VAULT_FORBIDDEN_EXT / _VAULT_FORBIDDEN_NAMES"
  - "validator/validate.py: def _check_no_code_in_vault (os.walk + prune _scratch/.tx)"
verified: true
method: read-source
status: active
reversible: "Sửa 3 hằng danh sách trong validate.py; nên qua change request."
```

---

## DEC-002 — Tiêu chí cụ thể cho INV-18 (E-MIX-DATA: không dữ liệu học trong _system)

```yaml
id: DEC-002
type: decision
date: 2026-07-03
title: "Chốt tên-file dữ liệu học + vùng loại trừ công cụ trong _system"
spec_ref: "INV-18 (spec mô tả mức cao: 'không dữ liệu học/cá nhân trong _system')"
summary: >
  AI tự chốt: file dữ liệu học cấm = {vault_state.md, topic_state.md, lesson_state.md,
  sources.md, lesson.md, lesson_notes.md, topic.md} và thư mục 'topics/'. Loại trừ vùng công cụ
  _SYSTEM_SKIP_DIRS = {validator, .venv, venv, __pycache__, .pytest_cache, .cache, .tx, repo_lab, .git}.
rationale: >
  _system/ chứa code validator + .venv → rủi ro bắt oan rất cao. Nhận diện theo TÊN dữ liệu học
  cụ thể + prune vùng công cụ để chỉ bắt đúng dữ liệu học lạc chỗ, không đụng mã nguồn/thư viện.
evidence:
  - "validator/validate.py: hằng _SYSTEM_DATA_NAMES / _SYSTEM_SKIP_DIRS"
  - "validator/validate.py: def _check_no_data_in_system (os.walk + prune _SYSTEM_SKIP_DIRS)"
verified: true
method: read-source
status: active
reversible: "Sửa 2 hằng trong validate.py; nên qua change request."
```

---

## DEC-003 — Hoãn enforce INV-17/18 cho tới khi có tiêu chí rõ

```yaml
id: DEC-003
type: decision
date: 2026-07-02
title: "Cố ý CHƯA enforce INV-17/18 ở giai đoạn đầu để tránh bắt oan"
spec_ref: "INV-17/18"
summary: >
  Ở mốc 197 test, INV-17/18 được cố ý để trống vì tiêu chí 'repo/dependency/dữ liệu cá nhân'
  còn mờ. Chỉ enforce sau khi chốt được bộ luật cụ thể (→ DEC-001/DEC-002).
rationale: >
  Code vội trên tiêu chí mờ sẽ bắt oan — vi phạm nguyên tắc 'không bịa, không suy đoán'.
  Thà để một invariant chưa cắm điện còn hơn cắm sai.
evidence:
  - "end.md: đoạn 'Chỉ còn INV-17/18 ... cố ý chưa làm vì tiêu chí còn mờ'"
  - "Đã đóng sau đó: validate.py hiện có _check_no_code_in_vault + _check_no_data_in_system"
verified: false
method: transcript
status: superseded
superseded_by: DEC-001
reversible: "n/a (đã được thay thế bằng việc enforce thật)."
```

---

## DEC-004 — Tắt fuzzing của FSRS để đảm bảo tất định

```yaml
id: DEC-004
type: decision
date: 2026-07-01
title: "Set enable_fuzzing=False cho FSRS Scheduler"
spec_ref: "none (spec silent — đây là chi tiết thư viện py-fsrs)"
summary: >
  py-fsrs mặc định enable_fuzzing=True (thêm nhiễu ngẫu nhiên vào interval). AI tự quyết set False
  để 2 lần chạy cùng input cho cùng due/stability (tất định) — điều kiện tiên quyết cho INV-08 (replay).
rationale: >
  Hệ thống cần tất định để validate bằng cách replay log và so khớp. Fuzzing phá tính này.
evidence:
  - "repo_lab/repo_evaluations/fsrs.md: SPIKE Q3 'enable_fuzzing mặc định True → phải set False'"
  - "repo_lab/repo_evaluations/fsrs.md: 'Determinism: enable_fuzzing=False → 2 lần chạy cùng due + stability'"
verified: true
method: read-source
status: active
reversible: "Đổi cờ trong fsrs_adapter/cấu hình; nhưng sẽ phá tất định — không khuyến nghị."
```

---

## DEC-005 — Thêm "drift-guard": test buộc docs khớp code (single-source-of-truth)

```yaml
id: DEC-005
type: decision
date: 2026-07-02
title: "Mỗi rules file có khối máy-đọc + test đối chiếu với hằng số code"
spec_ref: "none (spec yêu cầu có rules/, không yêu cầu cơ chế chống trôi)"
summary: >
  AI tự thêm cơ chế: review_rules↔MAP_GRADE_TO_RATING, teaching_rules↔_GATE,
  validation_rules↔tập mã E-* thật, claim_rules↔_CLAIM_CLASSES/_CLAIM_STATUS, commands↔subcommands CLI.
  Đổi ở code mà quên đồng bộ docs (hoặc ngược lại) → test đỏ.
rationale: >
  Tài liệu vận hành nếu trôi khỏi code sẽ khiến AII vận hành sai trong dài hạn. Ràng docs vào code
  bằng test biến tài liệu thành hợp đồng kiểm chứng được, đúng tinh thần 'chính xác lâu dài'.
evidence:
  - "rules/validation_rules.md: khối 'error_codes (máy đọc)'"
  - "rules/commands.md: khối 'backends (máy đọc)'; test phase10/test_commands_registry.py (theo transcript)"
  - "validator/session.py: CLI_COMMANDS + _build_parser() dùng cho introspect"
verified: true
method: read-source
status: active
reversible: "Xoá test consistency (không khuyến nghị — mất lá chắn chống trôi)."
```

---

## DEC-006 — Tách `_build_parser()` khỏi `main()` để test introspect được CLI

```yaml
id: DEC-006
type: decision
date: 2026-07-02
title: "Refactor session.py: tách builder argparse + hằng CLI_COMMANDS"
spec_ref: "none (spec silent về tổ chức code CLI)"
summary: >
  AI tự refactor để test có thể introspect subcommand thật của CLI mà không chạy tiến trình,
  phục vụ drift-guard commands.md ↔ CLI (DEC-005).
rationale: >
  Muốn kiểm 'registry lệnh khớp CLI thật' một cách rẻ và ổn định thì cần điểm truy cập parser
  thuần dữ liệu. Đây là thay đổi tổ chức, giữ nguyên hành vi CLI.
evidence:
  - "validator/session.py:307 CLI_COMMANDS = ('review','done','forget')"
  - "validator/session.py:310 def _build_parser(); main() gọi _build_parser().parse_args(argv)"
verified: true
method: read-source
status: active
reversible: "Gộp lại vào main() nếu bỏ nhu cầu introspect (mất khả năng test rẻ)."
```

---

## DEC-007 — Định dạng & vị trí của chính Nhật ký quyết định này

```yaml
id: DEC-007
type: decision
date: 2026-07-03
title: "Đặt decision journal ở _system/decisions/ dạng .md + index.yaml máy-đọc"
spec_ref: "none (người dùng yêu cầu 'lưu định dạng tốt nhất cho AI dùng')"
summary: >
  Chọn markdown (người-đọc) + khối/tệp YAML máy-đọc, đặt tại _system/decisions/ — theo đúng
  quy ước sẵn có của dự án (repo_lab/repo_evaluations dùng phiếu .md + YAML).
rationale: >
  Nhất quán với hệ sinh thái file hiện có; vừa cho người đọc vừa cho AI parse; INV-18 an toàn
  (đã kiểm tên file không trùng _SYSTEM_DATA_NAMES).
evidence:
  - "repo_lab/repo_evaluations/fsrs.md (tiền lệ phiếu quyết định .md + YAML)"
  - "validator/validate.py: _SYSTEM_DATA_NAMES (đã đối chiếu tên file thư mục này không trùng)"
verified: true
method: read-source
status: active
reversible: "Di chuyển/đổi định dạng thư mục nếu cần."
```

---

## DEC-008 — `schemas/` là bản mô tả ràng-buộc-test, KHÔNG phải nguồn chân lý thứ hai

```yaml
id: DEC-008
type: decision
date: 2026-07-03
title: "Dựng schemas/*.schema.md dạng mô tả người-đọc + khối máy-đọc schema_fields, drift-guard vào models.py"
spec_ref: "spec mục 2 liệt kê _system/schemas/*.schema.md; nhưng KHÔNG chốt định dạng"
summary: >
  Spec khai báo cần 5 file schema nhưng 'chân lý schema' thực tế nằm ở validator/models.py (pydantic
  strict). AI quyết: schemas/ chỉ là TÀI LIỆU mô tả, và khối máy-đọc `schema_fields` (tập required/
  optional theo khóa document = alias nếu có) bị test đối chiếu CHÍNH XÁC với Model.model_fields.
  models.py vẫn là single-source-of-truth; schemas/ không được phép là nguồn thứ hai trôi tự do.
rationale: >
  Hai nguồn schema song song sẽ trôi khỏi nhau. Ràng doc vào model bằng test (alias-aware, required-aware)
  biến schemas/ thành hợp đồng kiểm chứng được thay vì prose. Trước khi viết, đã introspect model_fields
  thật (không hand-guess) để tập field khớp 100%.
evidence:
  - "schemas/{lesson_state,vault_state,topic_state,sources,review_item}.schema.md — mỗi file có khối schema_fields"
  - "validator/tests/phase10/test_schemas_consistency.py — 6 passed (5 parametrize + present)"
  - "Lệnh đã chạy: pytest full → 224 passed; validate.py --scope full → pass:true (schemas/ không kích INV-18)"
  - "models.py: field alias 'schema' (schema_name), required suy từ is_required() — đã introspect verify"
verified: true
method: ran-test
status: active
reversible: "Xoá schemas/ + test; models.py không phụ thuộc schemas/ nên không ảnh hưởng validator."
```

---

## DEC-009 — Lớp `prompts/` với drift-guard ở chỗ testable, prose bám spec verbatim

```yaml
id: DEC-009
type: decision
date: 2026-07-03
title: "Dựng prompts/ (system_prompt, router_prompt, system_change_prompt) — mắt xích cuối P10-agent"
spec_ref: "spec mục 2 (layout prompts/), 0.x, 11, 11A, 12, 13, 14"
summary: >
  Dựng 3 file prompt vận hành. Vì phần lớn là prose, AI quyết đặt drift-guard ở chỗ CÓ THỂ kiểm:
  - router_prompt.md: khối máy-đọc `router` với commands == registry commands.md (backends) và
    intents == đúng 7 intent spec 11 → test đỏ nếu lệch.
  - system_prompt.md / system_change_prompt.md: prose bám spec (0.x/13/14 và 12 verbatim), guard mức
    presence + non-empty. Nội dung KHÔNG bịa: mỗi mục trỏ đúng mục spec nguồn.
rationale: >
  Không cố ép test lên prose thuần (sẽ giả tạo); thay vào đó ràng phần cấu trúc-hoá được (tập lệnh/intent)
  và trích spec verbatim cho phần luật. Router là surface thứ 3 của tập lệnh (sau commands.md↔CLI) → thêm
  một lớp chống trôi.
alternatives:
  - "Ép mọi câu prose thành test → giả tạo, dễ vỡ, không đo đúng cái cần."
  - "Không test gì cho prompts → trôi tự do. Loại."
evidence:
  - "prompts/{system_prompt,router_prompt,system_change_prompt}.md"
  - "validator/tests/phase10/test_router_prompt_consistency.py: 3 test (commands↔registry, intents↔spec11, presence)"
  - "Lệnh đã chạy: pytest full → 227 passed; validate.py --scope full → pass:true (prompts/ không kích INV-18)"
verified: true
method: ran-test
status: active
reversible: "Xoá prompts/ + test; validator không phụ thuộc prompts/ (chúng là lớp vận hành AI, không phải lõi kiểm)."
```

---

## DEC-010 — Scaffolding `change_requests/` + ghi hồi tố CR-0001 (khép vòng truy vết v2.6)

```yaml
id: DEC-010
type: decision
date: 2026-07-03
title: "Dựng change_requests/{pending,approved,rejected}/ + changelog.md; CR-0001 hồi tố cho F-A/F-B"
spec_ref: "spec §12 (change request 7 bước)"
summary: >
  Dựng scaffolding CR theo §12 + ghi hồi tố CR-0001 hợp thức hoá thay đổi spec v2.5→v2.6 (F-A/F-B) vốn
  đã áp 2026-07-01 nhưng chưa có 'vết' CR chính thức. CR-0001 đặt ở approved/ (đã áp), có changelog.
  Thêm drift-guard: states trong system_change_prompt.md phải có thư mục thật + changelog tồn tại + CR-0001 logged.
rationale: >
  'Mọi thay đổi spec đều phải có vết CR' (§12). DEV-001/002/003 trước đây chỉ verified qua transcript;
  giờ có file CR kiểm chứng được, đóng vòng. Đây là build-time scaffolding (không qua runtime /system) —
  ghi rõ retroactive: true để trung thực, không giả vờ là CR mới.
alternatives:
  - "Không dựng CR, để DEV-003 mãi ở mức transcript → thiếu vết chính thức. Loại."
  - "Giả vờ CR đi qua pending như CR mới → sai sự thật (nó đã áp rồi). Loại → dùng retroactive:true."
evidence:
  - "change_requests/{changelog.md, approved/cr-0001-fsrs-spec-v2.6.md, pending/README.md, rejected/README.md}"
  - "validator/tests/phase10/test_change_requests_scaffold.py: 2 passed"
  - "Lệnh đã chạy: pytest full → 229 passed; validate.py --scope full → pass:true (change_requests/ không kích INV-18)"
verified: true
method: ran-test
status: active
reversible: "Xoá change_requests/ + test; không ảnh hưởng lõi validator."
```

---

## DEC-011 — P11: chỉ dựng LÕI planner tất định, KHÔNG bịa bước migration khi chưa có schema v2

```yaml
id: DEC-011
type: decision
date: 2026-07-03
title: "migrations/planner.py (tính đường di trú) + hợp đồng thực thi; hoãn lớp execution tới khi có schema thật"
spec_ref: "spec 10.7/10.3b, INV-19, PHASE_11"
summary: >
  P11 gồm cache/diff/migration. AI quyết chỉ triển khai phần KIỂM CHỨNG ĐƯỢC NGAY: planner tất định
  (up_to_date/ahead/migratable/no_path) + discover_steps (parse tên file vN_to_vN+1). KHÔNG dựng bước
  v1→v2 hay lớp execution transaction-FULL, vì hệ thống mới VERSION=1 — chưa có schema v2 để migrate;
  viết bước/execution bây giờ = bịa dữ liệu biến đổi không tồn tại.
rationale: >
  'Chỉ triển khai cái kiểm chứng được' (kỷ luật người dùng). Planner là bản chất bài toán di trú, test
  được đầy đủ bằng fixture. Hợp đồng execution (transaction-FULL, validate-at-target, rollback-on-fail)
  đã ghi ở migrations/README.md để lớp sau bám, không cần bịa để 'cho có'.
alternatives:
  - "Dựng luôn v1→v2 + execution → phải bịa một schema v2 và phép biến đổi không có thật. Loại."
  - "Bỏ qua P11 hoàn toàn → mất khung planning kiểm-được cho tiến hoá lâu dài. Loại."
evidence:
  - "migrations/planner.py (thuần, tất định) + migrations/README.md (hợp đồng execution)"
  - "validator/tests/phase11/test_migration_planner.py: 11 test (4 status + discover + nhất quán version thật)"
  - "Lệnh đã chạy: pytest full → 240 passed; validate.py --scope full → pass:true"
verified: true
method: ran-test
status: active
todo: "Khi có schema v2 (qua change request): dựng v1_to_v2.py + lớp execution + test golden PASS/rollback (PHASE_11)."
reversible: "Xoá migrations/planner.py + test; validator không phụ thuộc."
```

---

## DEC-012 — `memory_rules.md` + `anti_drift_rules.md`: khép bộ rules/, tách rõ code-enforced vs process-enforced

```yaml
id: DEC-012
type: decision
date: 2026-07-03
title: "Dựng 2 rules còn lại; anti_drift phân minh 'code chặn được' vs 'chỉ quy trình chặn'"
spec_ref: "spec §17 (anti-drift), §74–78 + §11B.1 + §15.1 (memory); layout §2"
summary: >
  Hoàn tất rules/ theo layout spec (6 file). Quyết định thiết kế mấu chốt của anti_drift_rules.md: chia
  hai lớp — code_enforced (có mã lỗi validator thật) và process_enforced (chỉ quy trình/con người chặn,
  KHÔNG có mã). Không gộp lẫn để khỏi tạo ảo giác 'validator chặn hết' (đúng giới hạn §0.3).
rationale: >
  Lý do CHỌN (chính xác, kiểm-được): (1) spec §17 cho list anti-drift cụ thể + nhiều điểm ánh xạ mã lỗi
  thật → drift-guard được (codes ⊆ validation_rules.error_codes). (2) memory có cơ sở §11B.1 (boot whitelist)
  → guard khớp danh sách nạp. (3) Trung thực §0.3: nhiều nguyên tắc chống-drift KHÔNG có mã code (vd 'không
  tự nhận PASS') — phải nói rõ là process-enforced, không giả vờ code chặn.
alternatives:
  - "Gộp mọi anti-drift thành 'validator chặn' → sai sự thật (LLM có thể nói dối, §0.3). Loại."
  - "Bỏ qua memory_rules vì thiếu section riêng → nhưng có §11B.1/§74-78/§15.1 đủ ground. Không bỏ."
evidence:
  - "rules/anti_drift_rules.md (khối anti_drift: code_enforced + process_enforced) — §17 verbatim"
  - "rules/memory_rules.md (khối context_boot) — §11B.1"
  - "validator/tests/phase10/test_anti_drift_memory_consistency.py: 4 passed (codes⊆error_codes; boot==§11B.1; presence)"
  - "Lệnh đã chạy: pytest full → 244 passed; validate.py --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Xoá 2 file + test; validator không phụ thuộc."
```

---

## DEC-013 — `templates/` dùng đuôi `.template.md`; topic mới = rỗng với hash view THẬT

```yaml
id: DEC-013
type: decision
date: 2026-07-03
title: "Template dùng đuôi .template.md (tránh INV-18) + topic_template rỗng với empty-view hash thật"
spec_ref: "spec §2 (layout templates/), §3 (lesson 3 file), §5, INV-09/18"
summary: >
  Dựng templates/{topic_template,lesson_template}. Hai quyết định AI tự ra (spec không nói):
  (1) file template mang đuôi `.template.md` thay vì tên dữ liệu trần (lesson_state.md...);
  (2) topic_template khởi tạo RỖNG (lessons=[]) với generated_from_hash = hash canonical list rỗng.
rationale: >
  (1) LÝ DO CHÍNH XÁC (đã verify): file tên 'lesson_state.md'/'topic_state.md'... trong _system/ trùng
  _SYSTEM_DATA_NAMES → validator báo E-MIX-DATA (INV-18) trên chính hệ thống. Đuôi .template.md (giống
  .schema.md) khử trùng-tên tại GỐC, mà INV-18 VẪN quét templates/ (bắt được nếu ai để file dữ liệu thật
  vào đây) — defense-in-depth, tốt hơn thêm templates/ vào skip-list (skip sẽ tắt luôn phát hiện).
  (2) Topic rỗng có view rỗng → hash tất định = canonical_hash([]); thêm lesson là việc REGEN của /learn,
  không bake được hash 'có lesson' vào template. Hash bake được test đối chiếu views.py → KHÔNG bịa.
alternatives:
  - "Đặt tên dữ liệu trần + thêm templates/ vào _SYSTEM_SKIP_DIRS → sửa lõi validator + tắt phát hiện data lạc trong templates/. Loại (fix ngọn + giảm an toàn)."
  - "Gõ tay hash view 'có sẵn lesson' → bịa, sai INV-09. Loại."
evidence:
  - "templates/topic_template/{topic_state,sources}.template.md; templates/lesson_template/{lesson,lesson_state,lesson_notes}.template.md; templates/README.md"
  - "validator/tests/phase10/test_templates_valid.py: 5 passed (schema + hash==views.py + empty-topic vault FULL validate PASS)"
  - "Lệnh đã chạy: pytest full → 249 passed; validate.py --scope full → pass:true (templates/ .template.md KHÔNG kích INV-18 — verify thực nghiệm)"
verified: true
method: ran-test
status: active
todo: "Khi dựng backend /learn: instantiate template + REGEN view + cập nhật index lessons (INV-25) trong transaction-FULL; test golden 'topic có lesson' PASS."
reversible: "Xoá templates/ + test; validator không phụ thuộc."
```

---

## DEC-014 — Backend `/learn`: tạo topic mới tất định từ template (phần calibrate là tầng AI)

```yaml
id: DEC-014
type: decision
date: 2026-07-03
title: "cmd_learn tạo topic+lesson-001 từ template trong transaction-FULL; Q1–Q3 calibrate KHÔNG ở backend"
spec_ref: "spec 11A.1 (/learn), §3, §10.3; templates DEC-013"
summary: >
  Dựng backend CLI `session.py learn` (lệnh ghi thứ 4, sau review/done/forget). Quyết định ranh giới:
  backend chỉ nhận input ĐÃ RESOLVE (topic_id/title/lesson-title/objective) và tạo file tất định; phần
  hỏi calibrate Q1–Q3 + đề xuất 3–7 lesson (spec 11A.1) là tầng AI-chat, KHÔNG nhét vào CLI (CLI phải
  tất định + testable). Chỉ tạo topic MỚI (đã tồn tại → E-DRIVER). Cập nhật commands.md backends
  '/learn' null→'session.py learn'.
rationale: >
  Lý do CHỌN (chính xác): (1) CLI là engine ghi tất định — nhét Q&A tương tác vào sẽ không test được;
  (2) view sinh bằng views.py từ lesson mới (review_items=[] ⇒ view rỗng) — KHÔNG bake/bịa hash;
  (3) chỉ list lesson-001 trong index vì INV-25 đòi index khớp lesson TRÊN ĐĨA (list 5 lesson đề xuất mà
  chưa tạo folder → E-INDEX-MISMATCH). Sửa backends là WIRING (lệnh /learn đã có sẵn trong registry),
  không phải thêm/xóa lệnh → không cần CR; test_commands_registry vẫn xanh (backends↔CLI↔CLI_COMMANDS khớp).
alternatives:
  - "Nhét Q1–Q3 vào CLI → mất tính tất định/testable. Loại (đúng ranh giới driver vs AI-chat)."
  - "List đủ 3–7 lesson đề xuất vào index ngay → E-INDEX-MISMATCH (lesson chưa có trên đĩa). Loại."
evidence:
  - "validator/session.py: cmd_learn + 'learn' trong CLI_COMMANDS + parser; commands.md backends['/learn']='session.py learn'"
  - "validator/tests/phase10/test_session_learn.py: 5 passed (tạo valid + FULL validate PASS + đồng bộ con trỏ + từ chối topic tồn tại/id xấu)"
  - "Lệnh đã chạy: registry+router guard 7 passed; pytest full → 254 passed; validate.py --scope full → pass:true"
verified: true
method: ran-test
status: active
todo: "Backend còn null (đều đọc/không-ghi hoặc trong-phiên): /status /resume /schedule /gaps /ask /source /test /skip /fix — dựng khi cần chạy thật đầu-cuối."
reversible: "Gỡ cmd_learn + 'learn' khỏi CLI_COMMANDS + đặt lại backends['/learn']=null + xoá test."
```

---

## DEC-015 — Engine "item tới hạn" (spec 8.5) dùng chung + `/schedule` read-only; mở rộng n-ngày

```yaml
id: DEC-015
type: decision
date: 2026-07-03
title: "schedule.py (due engine 8.5) tách riêng, tất định; /schedule là consumer read-only; days>0 là mở rộng"
spec_ref: "spec 8.5 (cần ôn hôm nay), 11A.2 (/schedule)"
summary: >
  Dựng engine due tất định `validator/schedule.py` (due_within/due_today) — bản chất dùng chung cho
  /review, /status, /schedule (grep xác nhận CHƯA có logic này ⇒ không trùng lặp). Wire lệnh CHỈ-ĐỌC
  `session.py schedule` (không transaction). Loại item mastery_state='new' khỏi due (spec 8.5 + priority
  không có nhóm cho 'new'). days=0 = ĐÚNG spec 8.5 'hôm nay'.
rationale: >
  Lý do CHỌN (chính xác): (1) '/review liệt kê' + '/status đếm due' + '/schedule n ngày' đều cần cùng phép
  tính 8.5 → build một chỗ ở gốc, tránh rải logic (fix gốc). (2) Bám review_rules.md/spec 8.5 verbatim
  (thứ tự priority→due_date→due_at_utc→lesson_id→item_id; logical_today với day_cutoff CHỈ cho Review).
  (3) /schedule read-only ⇒ không cần transaction ⇒ rủi ro thấp; test đối chiếu tính tay + demo vault.
decisions_extra:
  - "days>0 (n-ngày) là MỞ RỘNG của AI: spec 8.5 chỉ chốt 'hôm nay' (days=0). Chân trời: Review→due_date<=logical_today+days; Learning/Relearning→due_at_utc<=now_utc+days. Đánh dấu rõ để không nhầm là spec."
alternatives:
  - "Mỗi lệnh tự tính due → rải logic, dễ lệch nhau. Loại."
  - "Đưa engine vào views.py (đã có build_review_schedule) → nhưng đó là VIEW (mọi item, sắp theo due), khác 'due filter hôm nay'. Tách module riêng rõ nghĩa hơn."
evidence:
  - "validator/schedule.py (due_within/due_today/logical_today, thuần); grep xác nhận không trùng logic cũ"
  - "validator/session.py: cmd_schedule + 'schedule' CLI_COMMANDS + parser --days; commands.md backends['/schedule']='session.py schedule'"
  - "tests: phase11/test_schedule_due.py 6 passed (new-excluded, per-state due, priority, days-horizon, day-cutoff); phase10/test_session_schedule.py 3 passed (demo new not due, read-only, CLI)"
  - "Lệnh đã chạy: guards+schedule 16 passed; CLI 'schedule --json' → due:[]; pytest full → 263 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ schedule.py + cmd_schedule + 'schedule' khỏi CLI_COMMANDS + backends['/schedule']=null + xoá test."
```

---

## DEC-016 — Backend `/status` + `/resume` (read-only) — khép cửa VÀO vòng ngày (spec 11B)

```yaml
id: DEC-016
type: decision
date: 2026-07-03
title: "cmd_status + cmd_resume read-only; /status tái dùng engine due 8.5; cảnh báo phiên chưa /done (11B.2)"
spec_ref: "spec 11B (daily workflow), 11B.2 (open-session recovery), 8.5"
summary: >
  Dựng 2 backend CHỈ-ĐỌC. /status (cửa vào): topic/lesson hiện tại + đếm due hôm nay (tái dùng
  schedule.due_today — DEC-015) + cảnh báo open_session.lesson_id != null (11B.2) + gợi ý lệnh
  (review nếu due, else resume/learn). /resume: current_lesson + next_action + status.
  Gom nhóm dispatch _READONLY_COMMANDS (schedule/status/resume): không transaction, không committed.
rationale: >
  Lý do CHỌN (chính xác): (1) spec 11B định nghĩa nhịp ngày 'vào bằng /status hoặc /resume' — đây là
  cửa VÀO còn thiếu; có nó = vòng học mở–đóng đủ. (2) /status tái dùng đúng engine 8.5 vừa build (một
  nguồn tính due, không tính lại) — đúng 'fix/đặt ở gốc'. (3) Read-only ⇒ không transaction ⇒ rủi ro
  thấp; test đối chiếu demo vault + kiểm read-only (mtime không đổi) + ca open_session.
  Ranh giới trung thực: boot-sequence 11B.1 (chỉ nạp *_state+notes+Sessions gần nhất) là kỷ luật CONTEXT
  của AI (memory_rules), KHÔNG phải việc backend — backend chỉ trả con trỏ + next_action.
evidence:
  - "validator/session.py: cmd_status/cmd_resume + _READONLY_COMMANDS + _print_readonly; parser status/resume không --lesson"
  - "commands.md backends['/status']='session.py status', ['/resume']='session.py resume'"
  - "tests: phase10/test_session_status_resume.py 5 passed (demo status/resume, read-only mtime, open_session warn, CLI); guards 7 passed"
  - "CLI thật: /status → 'due hôm nay: 0 | gợi ý: /resume'; /resume → next_action demo"
  - "Lệnh đã chạy: pytest full → 268 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
todo: "Backend còn null: /gaps (read) + /ask /source /test /skip /fix (ghi trong phiên, LIGHT)."
reversible: "Gỡ cmd_status/cmd_resume + khỏi CLI_COMMANDS/_READONLY_COMMANDS + backends về null + xoá test."
```

---

## DEC-017 — Test tích hợp E2E chuỗi lệnh CLI (tất định) — nghiệm thu vòng lõi

```yaml
id: DEC-017
type: decision
date: 2026-07-03
title: "phase12/test_cli_loop_composition — chuỗi learn→status→review→done→forget, FULL PASS mỗi bước"
spec_ref: "spec 11B (vòng ngày), 10.8 (FULL), PHASE_12 (pilot)"
summary: >
  Dựng test tích hợp CHẠY CÁC LỆNH THẬT NỐI NHAU trên bản sao vault, assert validate_full_semantic
  (FULL=core+semantic) PASS sau MỖI bước ghi + kiểm hệ quả (item rời 'new', open_session clear, topic
  rỗng sau forget, tombstone vào transaction_log). Tất định (at cố định, không AI, không ngẫu nhiên).
rationale: >
  Lý do CHỌN (chính xác): mỗi lệnh đã test RIÊNG nhưng chưa test GHÉP — bug tích hợp (view/index lệch
  sau chuỗi, con trỏ sai sau forget) chỉ lộ khi chạy chuỗi. Đây là nghiệm thu 'phần đã làm cohere' trước
  khi mở rộng (đúng 'valid nhiều lần'). Dùng full_semantic (không chỉ core) vì đó là mức transaction thật dùng.
scope_honesty: >
  ĐÂY KHÔNG phải P12 pilot đầy đủ. Pilot thật cần AI DẠY một topic thật + cross-AI handoff (một AI khác
  đọc vault tiếp tục đúng) — phần đó CÒN LẠI, không tự động hoá bằng test được. Test này là nền tất định.
evidence:
  - "validator/tests/phase12/test_cli_loop_composition.py: 3 passed (baseline; full loop; forget cần confirm)"
  - "Lệnh đã chạy: pytest full → 271 passed; validate.py --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Xoá test (không ảnh hưởng code sản phẩm)."
```

---

## DEC-018 — Backend `/source` nạp nguồn raw ở mức transaction-LIGHT

```yaml
id: DEC-018
type: decision
date: 2026-07-03
title: "cmd_source thêm nguồn status=raw vào sources.md (tạo nếu thiếu); transaction-LIGHT (spec 10.8)"
spec_ref: "spec 15 (nguồn raw), 5.3 (schema sources), 10.8/11A (mức validate)"
summary: >
  Dựng backend /source: thêm 1 source {id: src-NNN auto, kind, ref, status: raw, trust, scope, added,
  anchors: []} vào topics/<topic>/sources.md; tạo file nếu topic chưa có (schema_version khớp vault).
  Chạy transaction-LIGHT. Phân loại kind/trust là tầng AI-chat; backend ghi tất định.
rationale: >
  Lý do CHỌN mức LIGHT (chính xác, grounded): spec 10.8 + 11A nói RÕ 'ghi-trong-phiên dùng transaction-LIGHT';
  nguồn raw KHÔNG đụng FSRS/view/cross-ref (INV-13 chỉ kích khi có CLAIM trỏ nguồn raw — chưa có lúc nạp),
  nên LIGHT vừa đúng spec vừa an toàn; lưới an toàn cuối vẫn là /done FULL (spec 10.8: không gì 'đã chốt'
  tới khi qua FULL). Giá trị: mở khoá nhánh nguồn→claim lớp B (mảng INV-12/13 lớn) để chạy đầu-cuối.
evidence:
  - "validator/session.py: cmd_source + _next_src_id + _run_tx(level='light'); 'source' trong CLI_COMMANDS + parser; commands.md backends['/source']='session.py source'"
  - "tests/phase10/test_session_source.py: 5 passed (tạo sources.md, id tăng dần, kind sai bị chặn LIGHT, topic lạ→E-DRIVER, raw vẫn FULL PASS)"
  - "Lệnh đã chạy: pytest full → 280 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ cmd_source + 'source' khỏi CLI_COMMANDS + backends về null + xoá test."
```

---

## DEC-019 — Fix GỐC INV-16: ABSPATH_RE báo oan URL (`https://`) là đường dẫn tuyệt đối

```yaml
id: DEC-019
type: decision
date: 2026-07-03
title: "Sửa regex ABSPATH_RE để ổ-đĩa là chữ cái ĐỘC LẬP (negative lookbehind), không bắt oan scheme URL"
spec_ref: "INV-16 (E-PORT-ABSPATH); spec 5.3 (ref được là URL)"
summary: >
  Bug phát hiện khi test /source: ref='https://docs.docker.com' → E-PORT-ABSPATH oan. Gốc: ABSPATH_RE cũ
  `[A-Za-z]:/` khớp 's:/' trong 'https://' (chữ 's' + ':/'). Nhưng ổ đĩa Windows là MỘT chữ cái ĐỘC LẬP
  (C:\), không phải chữ nằm trong từ. Sửa: `(?<![A-Za-z])[A-Za-z]:[\\/]|/Users/|/home/`.
root_cause_analysis: >
  Không fix ngọn (không né URL trong /source, không tắt INV-16). Sửa đúng ĐỊNH NGHĨA 'ổ đĩa' ở regex gốc:
  negative lookbehind loại trường hợp chữ cái bị 1 chữ khác đứng trước (scheme 'http'/'https'). URL là
  PORTABLE (không phụ thuộc máy) nên spec 5.3 cho phép; INV-16 chỉ nên bắt path THEO-MÁY (C:\, /home/, /Users/).
impact:
  - "INV-16 vẫn bắt C:\\, C:/, /home/, /Users/ (test regression khoá lại)."
  - "Đánh đổi nhỏ: ổ đĩa dán liền sau 1 từ (vd 'xC:\\') sẽ bị bỏ — pathological, không thực tế; chấp nhận."
evidence:
  - "validator/vault_io.py: ABSPATH_RE mới + comment giải thích"
  - "tests/phase05_io/test_abspath_url_regression.py: 4 passed (URL/git/ftp không bắt; C:\\, D:/, /home/, /Users/ vẫn bắt)"
  - "Lệnh đã chạy: pytest full → 280 passed (KHÔNG hồi quy); validate --scope full → pass:true"
verified: true
method: ran-test
status: active
note: "Đây là bug-fix cho khớp spec 5.3 (không phải đổi spec). /Users//home/ vẫn có thể oan nếu URL chứa các chuỗi đó — edge hiếm, chưa xử lý; ghi nhận."
reversible: "Khôi phục ABSPATH_RE cũ (sẽ tái báo oan URL)."
```

---

## DEC-020 — Backend `/gaps` (read-only) — khép nhóm lệnh ĐỌC

```yaml
id: DEC-020
type: decision
date: 2026-07-03
title: "cmd_gaps liệt kê open_gaps mọi lesson (read-only)"
spec_ref: "spec 11A.2 (/gaps → liệt kê open_gaps, chỉ đọc); 5.1 (OpenGap {id:gap-*, desc, detected})"
summary: >
  Dựng /gaps chỉ-đọc: duyệt mọi lesson_state → gom open_gaps kèm lesson_id. Không ghi, không transaction.
  Khép nhóm lệnh đọc (schedule/status/resume/gaps).
rationale: >
  Lý do CHỌN (chính xác): rẻ + rủi ro ~0 + grounded (schema OpenGap đã có); hoàn tất nhóm đọc để mục 1
  gần đóng, dồn sức cho mục 2 (pilot). Read-only ⇒ không cần transaction.
evidence:
  - "validator/session.py: cmd_gaps + 'gaps' trong CLI_COMMANDS/_READONLY_COMMANDS/parser/_print_readonly; commands.md backends['/gaps']='session.py gaps'"
  - "tests/phase10/test_session_gaps.py: 4 passed (demo rỗng; liệt kê khi có gap; read-only; CLI)"
  - "Lệnh đã chạy: pytest full → 284 passed; validate --scope full → pass:true; CLI /gaps → '0 open_gap'"
verified: true
method: ran-test
status: active
reversible: "Gỡ cmd_gaps + 'gaps' khỏi CLI/_READONLY + backends về null + xoá test."
```

---

## DEC-021 — E2E hệ claim/nguồn ở mức TOÀN VAULT (nghiệm thu nhánh kiến thức confirmed)

```yaml
id: DEC-021
type: decision
date: 2026-07-03
title: "Test E2E soạn sources.md+lesson_notes.md thật → validate_full_semantic; dương + 4 âm"
spec_ref: "spec 0.1/5.5/15.1; INV-12/13/15/23; PHASE_12 bước 5"
summary: >
  Dựng test toàn-vault cho nhánh nguồn→claim (trước chỉ test đơn vị _check_claims). Soạn nguồn confirmed
  + anchor + claim lớp B trỏ anchor vào vault docker → validate_full_semantic PASS. 4 ca âm: nguồn raw
  làm anchor (E-SRC-RAWUSED), B thiếu anchor (E-CLAIM-NOSRC), claim thiếu class (E-CLAIM-UNCLASSED),
  claim ngoài '## Claims' (E-CLAIM-LOC).
rationale: >
  Lý do CHỌN (chính xác): đây là nhánh 'kiến thức chính thức' — trọng tâm §0 — nhưng CHƯA từng chạy GHÉP
  (chỉ unit). Trước khi verify wiring, đã ĐỌC validate_full_semantic xác nhận nó parse sources.md →
  _check_claims(sources_index) (không giả định). Soạn claim/source như AI làm trong phiên (nội dung
  AI-authored, validate ở /done) — shape bám test_claim_sources.py + models + spec 5.5, không bịa.
scope_honesty: >
  Đây là phần TẤT ĐỊNH của P12. Phần AI-dạy-thật (tạo claim TỪ hội thoại, chấm rubric) + cross-AI handoff
  vẫn CÒN LẠI, không auto-test được.
evidence:
  - "validator/tests/phase12/test_e2e_claim_source.py: 5 passed (1 dương + 4 âm)"
  - "Đã đọc validate.py: validate_full_semantic wiring sources.md → _check_claims (INV-12/13/15/23/26)"
  - "Lệnh đã chạy: pytest full → 289 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Xoá test (không đụng code sản phẩm)."
```

---

## DEC-022 — Bộ nghiệm thu P12 tất định (determinism + chống giả mạo FSRS + portability)

```yaml
id: DEC-022
type: decision
date: 2026-07-03
title: "test_p12_acceptance: 3 cam kết cốt lõi §0/§1 theo Definition-of-Done PHASE_12 (phần auto-test)"
spec_ref: "PHASE_12 DoD; spec §0 (Class A đúng tuyệt đối), §1 (portable, tái lập), INV-08/16"
summary: >
  Dựng bộ nghiệm thu tất định: (1) determinism — validate 2 lần giống hệt (PASS lẫn FAIL);
  (2) chống giả mạo FSRS — ôn rv-001 rồi sửa tay last_reviewed_at_utc/due_date → E-REVIEW-MISCALC;
  (3) portability — copy vault sang path tuyệt đối khác/sâu hơn → vẫn PASS (INV-16).
rationale: >
  Lý do CHỌN (chính xác): đây là checklist DoD verbatim của PHASE_12, verify TRỰC TIẾP các lời hứa
  cốt lõi chưa test E2E: 'không thể bịa điểm ôn' (tamper→MISCALC) là nền của cam kết Class A; determinism
  + portability là nền 'tái lập/mang đi được'. Tamper last_reviewed_at_utc cô lập MISCALC (đã đọc
  cards_equal: nó so exact last_reviewed_at_utc + due_date; không vào view/derive_mastery → không cascade).
scope_honesty: >
  Phần AI-dạy-thật (tạo claim/chấm rubric TỪ hội thoại) + cross-AI handoff KHÔNG auto-test được — CÒN LẠI,
  sẽ là nghiệm thu bán-thủ-công (soạn kịch bản hướng dẫn, không giả lập bằng code = không bịa).
evidence:
  - "validator/tests/phase12/test_p12_acceptance.py: 5 passed (determinism clean+error, tamper last_reviewed cô lập, tamper due_date, portability 2 path)"
  - "Đã đọc fsrs_adapter.cards_equal: xác nhận field so khớp (không đoán)"
  - "Lệnh đã chạy: pytest full → 294 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Xoá test (không đụng code sản phẩm)."
```

---

## DEC-023 — Pilot Runbook (nghiệm thu bán-thủ-công P12) + drift-guard runbook↔CLI

```yaml
id: DEC-023
type: decision
date: 2026-07-03
title: "_system/PILOT_RUNBOOK.md — quy trình người+AI+validator cho phần P12 không auto-test được"
spec_ref: "PHASE_12 DoD; spec §11B (nhịp ngày), §0.3 (giới hạn)"
summary: >
  Soạn runbook: chuẩn bị env → kịch bản pilot 1 topic (§11B) với LỆNH CLI THẬT + checkpoint validate
  sau mỗi ghi → cross-AI handoff → determinism/portability/tamper thủ công → DoD checklist đánh dấu
  [AUTO] vs [MANUAL] → ranh giới Class A/B/D (§0.3). Thêm khối máy-đọc pilot_commands + test drift-guard.
rationale: >
  Lý do CHỌN (chính xác): phần AI-dạy-thật + cross-AI handoff KHÔNG auto-test được (là chất lượng phán
  đoán, không phải logic). Giả lập bằng code = bịa. Runbook biến nó thành quy trình tái lập được bằng
  người + validator thật — đúng tinh thần §0.3 (phòng tuyến cuối là con người chạy validator). Lệnh trong
  runbook bám parser CLI thật (đã đọc _build_parser), + drift-guard buộc pilot_commands ⊆ CLI thật.
root_fix_note: >
  Lần đầu đặt khối yaml dưới heading '## 6 (...)' level 2 → test tìm không thấy (None). Fix GỐC: theo
  đúng quy ước dự án '### <name> (máy đọc)' level 3 (như mọi drift-guard khác), KHÔNG sửa test thành ngoại lệ.
evidence:
  - "_system/PILOT_RUNBOOK.md (6 mục + khối pilot_commands máy-đọc)"
  - "validator/tests/phase12/test_pilot_runbook.py: 3 passed (tồn tại; lệnh có thật; phủ nhịp ngày lõi)"
  - "Lệnh đã chạy: pytest full → 297 passed; validate --scope full → pass:true (runbook không kích INV-18)"
verified: true
method: ran-test
status: active
reversible: "Xoá PILOT_RUNBOOK.md + test."
```

---

## DEC-024 — Backend `/ask` ghi câu hỏi phụ vào `## Hỏi phụ` (LIGHT)

```yaml
id: DEC-024
type: decision
date: 2026-07-03
title: "cmd_ask chèn bullet '- [ngày] <q>' dưới '## Hỏi phụ' của lesson.md; transaction-LIGHT"
spec_ref: "spec 14A (mẫu lesson.md, section '## Hỏi phụ'), §11 (câu hỏi phụ ghi vào Hỏi phụ), 10.8"
summary: >
  Dựng /ask: chèn câu hỏi phụ vào '## Hỏi phụ' (tạo section nếu thiếu); LIGHT (ghi body lesson.md
  trong phiên, không đụng FSRS/view). lesson.md KHÔNG có front-matter → xử lý text thuần (không _load_raw).
  Chèn ngay dưới heading; LIGHT validate lại (AST) sau — text-edit không được tin mù, validator là lưới.
rationale: >
  Lý do CHỌN (chính xác): §14A/§11 chốt '## Hỏi phụ' là chỗ gom câu hỏi đào sâu (bullet tự do, không
  schema chặt) → chèn bullet là đúng bản chất, không cần quyết định report-vs-write như /test. LIGHT đúng
  spec 10.8 (in-session). Không dùng #### Question (dành cho Sessions review-item) để tránh đụng máy qid.
evidence:
  - "validator/session.py: _append_hoiphu + cmd_ask + 'ask' CLI_COMMANDS/parser/dispatch; commands.md backends['/ask']='session.py ask'"
  - "tests/phase10/test_session_ask.py: 5 passed (chèn đúng dưới heading; tạo section nếu thiếu; LIGHT chặn abspath trong câu hỏi; lesson lạ→E-DRIVER; CLI)"
  - "Lệnh đã chạy: pytest full → 302 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ cmd_ask + 'ask' khỏi CLI_COMMANDS + backends về null + xoá test."
```

---

## DEC-025 — `/test` read-only (báo cáo learned_gate) — ÁP QUA change-request CR-0002

```yaml
id: DEC-025
type: decision
date: 2026-07-03
title: "cmd_test read-only tái dùng _check_gate_and_evidence (probe status=learned); đổi registry qua CR-0002"
spec_ref: "spec 9.3 (learned_gate), 11A.3 (đổi lệnh qua CR), §12; CR-0002"
summary: >
  /test = CHỈ ĐỌC: báo cáo từng trục (score/threshold/meets) + gate_pass + danh sách lỗi chặn, bằng cách
  chạy validate._check_gate_and_evidence trên BẢN SAO lesson đặt status='learned' (model_copy) → KHÔNG
  nhân đôi luật INV-07/22. KHÔNG ghi. Vì đổi phạm-vi-ghi của lệnh trong registry (transaction→chỉ đọc),
  đã đi QUA change-request CR-0002 (ghi approved/ + changelog + sửa commands.md) thay vì sửa nóng.
rationale: >
  Lý do CHỌN read-only (chính xác): nâng 'learned' là mốc gắn evidence (INV-07/22); làm nó thành tác dụng
  phụ của /test dễ 'learned oan' dựa trên điểm rubric chủ quan (Class D §0.3). Tách: /test CHỈ báo, việc
  đặt learned để luồng dạy + /done. Tái dùng _check_gate_and_evidence = single-source luật cổng.
  Đi qua CR vì §11A.3 buộc đổi lệnh phải qua change request — đồng thời NGHIỆM THU quy trình CR chạy thật.
evidence:
  - "validator/session.py: cmd_test (read-only, probe model_copy) + 'test' CLI/_READONLY/parser/dispatch/_print_readonly"
  - "change_requests/approved/cr-0002-test-readonly.md + changelog.md; commands.md ('/test' → chỉ đọc + backend)"
  - "tests/phase10/test_session_test_cmd.py: 6 passed (gate fail điểm; điểm đạt nhưng thiếu evidence; default lesson; read-only; lesson lạ; CLI)"
  - "Lệnh đã chạy: guards+CR scaffold 15 passed; pytest full → 308 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ cmd_test + 'test' khỏi CLI + backends null + revert commands.md (qua CR ngược) + xoá test."
```

---

## DEC-026 — Chốt disposition bề mặt lệnh: skip/system null-đúng-thiết-kế, fix defer

```yaml
id: DEC-026
type: decision
date: 2026-07-03
title: "11/15 lệnh có backend; /skip + /system null CỐ Ý; /fix defer (rủi ro) — có drift-guard"
spec_ref: "commands.md; spec §11A (/skip không đổi state), §12 (/system chỉ CR), §11A (/fix chỉ hình thức)"
summary: >
  Chốt: bề mặt lệnh coi như đủ dùng. 3 lệnh còn null: (1) /system — đúng thiết kế (chỉ tạo change-request,
  không backend ghi); (2) /skip — đúng thiết kế (bỏ qua câu ôn KHÔNG đổi state → thuần session-flow,
  không ghi file → không cần backend); (3) /fix — DEFER (auto-format rủi ro cao). Thêm drift-guard: tập
  backend-null ⊆ {/skip,/system,/fix} (lệnh mới quên backend → đỏ).
rationale: >
  Lý do CHỌN (chính xác): không dựng backend 'cho có'. /skip/system về bản chất KHÔNG ghi file nên null
  là ĐÚNG (không phải thiếu sót). /fix defer vì: auto-format phải tuyệt đối KHÔNG đụng ngữ nghĩa — đặc biệt
  cấm reflow 'evidence.quote' (spec §11A: /fix chạy LIGHT, không có INV-22b bắt lại) → rủi ro cao, giá trị
  modest → chưa làm là an toàn hơn (đúng 'hướng lâu dài'). Khi làm phải có test chống-reflow-quote nghiêm.
alternatives:
  - "Dựng /skip/system backend no-op cho 'đủ 15/15' → thừa, gây hiểu nhầm có ghi. Loại."
  - "Làm /fix ngay → rủi ro sửa hỏng evidence.quote khi chưa có guard chặt. Defer an toàn hơn."
evidence:
  - "validator/tests/phase10/test_commands_registry.py::test_null_backends_are_intentional (null ⊆ {skip,system,fix})"
  - "Lệnh đã chạy: registry 5 passed; pytest full → 309 passed"
verified: true
method: ran-test
status: active
todo: "/fix: khi làm, BẮT BUỘC test 'sau /fix, mọi evidence.quote byte-identical' trước khi cho chạy."
reversible: "n/a (quyết định phạm vi)."
```

---

## DEC-027 — Fix GỐC: đường regen view sinh lại `has_draft_knowledge` (stage='full')

```yaml
id: DEC-027
type: decision
date: 2026-07-03
title: "_regen_topic_views đổi stage 'core'→'full' + set has_draft_knowledge (INV-26/§15.1); RED-first"
spec_ref: "INV-26, §15.1 (draft knowledge), §4 (has_draft_knowledge là view); PHASE_11 (wiring /done GĐ2)"
summary: >
  Gap: _regen_topic_views regen stage='core' → KHÔNG sinh has_draft_knowledge. Khi có draft claim,
  topic_state.has_draft_knowledge (false cũ) lệch thực tế (true) → /done (và /review //forget) FULL
  validate FAIL E-DRAFT-IN-MAP → KHÔNG đóng sổ được. Fix tại ĐƯỜNG REGEN DÙNG CHUNG: stage='full' +
  claim_texts (topic.md + lesson_notes.md, khớp validate._collect_topic_claims) + _apply set
  has_draft_knowledge. Vá cùng lúc mọi lệnh regen (không per-command).
rationale: >
  Fix GỐC không ngọn: sửa nơi SINH view (một chỗ, đúng bản chất 'has_draft_knowledge là view tính từ
  claim'), KHÔNG nới lỏng INV-26 ở validate. Tái dùng views.build_has_draft_knowledge sẵn có (không viết
  logic mới). _topic_claim_texts khớp đúng tập file validator đếm (không lệch nguồn); bỏ lesson exclude
  cho /forget (draft của lesson sắp xoá không tính).
verification_red_green: >
  RED trước (chứng minh gap): test_done_with_draft_claim_syncs_has_draft FAIL với đúng
  'E-DRAFT-IN-MAP: has_draft_knowledge=False != thực tế=True' → xác nhận nguyên nhân gốc bằng thực nghiệm.
  GREEN sau fix: 2 passed; no-draft giữ false (không set bừa).
impact:
  - "Đóng được hạng mục PHASE_11 'wiring /done GĐ2 regen has_draft_knowledge' — mở khoá luồng draft (§15.1)."
  - "Ảnh hưởng /done+/review+/forget (cùng đường regen) — full suite 311 passed, không hồi quy."
evidence:
  - "validator/session.py: _topic_claim_texts + _regen_topic_views(stage='full') + _apply_views_to_topic_raw(has_draft_knowledge)"
  - "tests/phase10/test_done_draft_knowledge.py: 3 passed (draft→true+PASS; no-draft→false; /forget lesson-draft→exclude→false+PASS — khoá nhánh exclude_lesson_id)"
  - "Lệnh đã chạy: pytest full → 312 passed; validate --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Đổi lại stage='core' + bỏ set has_draft (sẽ tái mở gap)."
```

---

## DEC-028 — Nối dây vòng đời `open_session` (§5.4/§11B.2): /learn + /resume MỞ phiên, /done ĐÓNG

```yaml
id: DEC-028
type: decision
date: 2026-07-04
title: "Kích hoạt cơ chế phát hiện phiên chưa đóng: /learn và /resume SET open_session.lesson_id"
spec_ref: "spec §5.4, §11B.2 (open_session: mở khi vào phiên, /done clear, /status cảnh báo chưa đóng)"
summary: >
  Phát hiện (đọc mã, kiểm chứng): cảnh báo 'phiên chưa /done' của /status là CODE CHẾT — không lệnh
  nào từng SET open_session.lesson_id, nên nhánh unclosed_session không bao giờ kích. Fix GỐC (nối dây
  đúng bản chất vòng đời, không vá cảnh báo): (1) cmd_learn set open_session.lesson_id/started_at trong
  CÙNG write vault_state khi tạo topic/lesson mới (không cần CR — /learn vốn đã ghi vault_state, không đổi
  phạm vi lệnh). (2) cmd_resume chuyển từ read-only → ghi open_session qua transaction-LIGHT (phần này
  ĐỔI bề mặt lệnh nên đi qua CR-0003, xem DEV-005). cmd_done vẫn clear lesson_id/started_at như cũ → vòng
  đời khép kín: MỞ (learn|resume) → cảnh báo (status) → ĐÓNG (done).
rationale: >
  'Fix tận gốc đừng fix ngọn': gốc là thiếu bên GHI open_session, không phải logic cảnh báo. Vá cảnh báo
  (đọc suy diễn) sẽ che dấu gap thật. Set trong cùng write vault_state của /learn là ghi ĐÚNG-MỘT-LẦN,
  atomic qua transaction, không phát sinh ghi thừa. Dùng FA.canonical_reviewed_at cho started_at để khớp
  chuẩn thời gian canonical toàn hệ (offset vault), tất định, kiểm chứng được.
evidence:
  - "validator/session.py cmd_learn: 'MỞ phiên (§5.4/§11B.2)' set open_session trong cùng write vault_state"
  - "validator/session.py cmd_done: clear lesson_id/started_at + set last_full_validate (đã có)"
  - "tests/phase10/test_open_session_lifecycle.py: test_learn_opens_session, test_learn_then_done_clears_session, test_resume_opens_session, test_resume_then_done_clears_session — ĐỀU PASS"
  - "RED-first: test_open_session_lifecycle xác nhận gap (cảnh báo không kích) TRƯỚC khi nối dây; GREEN sau"
  - "ran-command: session.py resume --json trên bản copy → committed=true, vault_state.open_session.lesson_id=docker/lesson-001, started_at='...+07:00'"
  - "Suite đầy đủ: 316 passed; validator --level full --scope full → pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ 3 dòng set open_session trong cmd_learn + revert cmd_resume (kèm CR-0003) nếu đảo thiết kế."
```

---

## DEC-029 — Enforce phần THỜI GIAN của INV-05 (`updated <= today`) ở validator, tách khỏi model

```yaml
id: DEC-029
type: decision
date: 2026-07-04
title: "INV-05 `updated <= today`: kiểm ở validate.py (có utc_offset + mốc now), giữ model thuần; now bơm được để tất định"
spec_ref: "spec dòng 666 (`created <= updated <= today`), dòng 559 ('INV-05 dùng today = ngày lịch thật; KHÔNG day_cutoff; hai mốc tách biệt'), §5.1 (comment 'updated ... <= hôm nay')"
summary: >
  Đóng gap NOTE-009 (đã kiểm chứng): models.py CHỈ ép `created <= updated` (thuần, parse-time); phần
  `updated <= today` CHƯA bao giờ enforce → state 'đến từ tương lai' lọt lưới (phá audit trail + có thể
  lệch so-ngày). Fix GỐC bằng cách TÁCH đúng bản chất hai nửa của INV-05:
    - Cấu trúc `created <= updated`: thuần, không cần đồng hồ/offset → GIỮ ở model (models.py) như cũ.
    - Thời gian `updated <= today`: cần utc_offset (vault_state, cross-document) + mốc now → ĐẶT ở
      validate.py (_check_updated_not_future, gọi trong validate_full_core cho lesson_state + topic_state).
  'today' = now.astimezone(offset).date() — ngày lịch THẬT, KHÔNG áp day_cutoff_hour (spec §8.5 tách bạch:
  day-cutoff chỉ cho lọc 'ôn hôm nay', không đụng dấu ngày created/updated). Mã lỗi = E-SCHEMA (nhất quán
  INV-05 ở model + fixture E-SCHEMA__bad_date).
  Mốc now BƠM ĐƯỢC (không phải đồng-hồ-cứng trong model) để giữ TẤT ĐỊNH:
    - validate.py CLI thêm --at (ISO aware); mặc định = now(UTC) thật (audit).
    - Transaction mang self.now; validate_staged truyền vào validate_full_semantic; session._run_tx truyền
      `at` của thao tác (mỗi cmd_*). Nhờ vậy: updated ghi theo `at` thì 'today' lúc validate cũng theo `at`
      ⇒ /review /done /learn /forget ở bất kỳ `at` nào (kể cả test tương lai) vẫn nhất quán, không lệ đồng hồ.
rationale: >
  KHÔNG nhét now vào pydantic model vì: (a) model là hàm thuần → gọi datetime.now() phá tất định, test hoá
  phụ-thuộc-đồng-hồ; (b) model không có utc_offset (thuộc vault_state) → không đủ dữ kiện. Validator là nơi
  duy nhất có ngữ cảnh vault + offset + điểm bơm thời gian ⇒ đúng chỗ theo bản chất. now-injection nhân đôi
  đúng pattern --at của session.py (đồng nhất codebase). Không cần CR: đây là code KHỚP LẠI spec (không đổi
  spec/registry/bề mặt lệnh); --at chỉ là cờ phụ-trợ additive, backward-compatible (mặc định giữ nguyên hành vi).
evidence:
  - "validator/validate.py: _today_local + _check_updated_not_future; validate_full_core(now=None) tính today_local; validate_full_semantic(now) truyền xuống; main() thêm --at"
  - "validator/transaction.py: Transaction(now=None) + validate_staged truyền now=self.now"
  - "validator/session.py: _run_tx(now) → Transaction(now=...); cmd_review now=reviewed_at, cmd_done now=done_at, cmd_learn/forget/source/ask/resume now=at"
  - "RED-first: tests/phase07a_core/test_inv05_updated_today.py — 5 test (updated tương lai default-now + inject-now cho lesson & topic + demo PASS). Chạy RED = 5 failed (1 assertion + 4 TypeError), GREEN = 5 passed"
  - "ran-command: validate.py --at 2026-06-29 trên demo → E-SCHEMA cho topic_state+lesson_state (updated 2026-06-30 > today 2026-06-29); --at bỏ (now thật) → pass:true"
  - "ran-test: full suite 321 passed (316 + 5); cập nhật test_cli_loop_composition + test_p12_acceptance dùng now=AT (tất định, không lệ đồng hồ)"
verified: true
method: ran-test
status: active
open_question: "Có mở rộng `<= today` cho sources[].added không? spec INV-05 văn bản gắn '<= today' vào updated; added chưa có cơ sở spec rõ → CHƯA làm (tránh vượt phạm vi). Ghi để cân nhắc."
reversible: "Gỡ _check_updated_not_future + tham số now (backward-compatible) nếu đảo; model vẫn giữ created<=updated."
```

---

## DEC-030 — `date_policy` enum-hoá `Literal["local_date"]` (chống cấu hình 'nói dối hành vi')

```yaml
id: DEC-030
type: decision
date: 2026-07-04
title: "Ràng buộc date_policy về đúng 1 giá trị spec (local_date) thay vì str tự do"
spec_ref: "spec §5.4 dòng 362 (date_policy: local_date — 'hôm nay' theo utc_offset, không UTC trôi)"
summary: >
  Audit hardening vault_state (sau khi soát các field khác đều chắc: day_cutoff_hour ge=0/le=23,
  export_policy enum, utc_offset regex, open_session đủ field gồm last_full_validate). Phát hiện
  date_policy khai `str` tự do, KHÔNG enum — trong khi mọi field enum khác đều Literal. Rủi ro: người
  dùng sửa tay `date_policy: utc` (mong hành vi UTC) sẽ được chấp nhận, nhưng code LUÔN dùng local_date
  theo utc_offset ⇒ cấu hình 'nói dối hành vi', sai âm thầm — trái triết lý strict của dự án
  ('bắt lỗi, không âm thầm ép/bỏ qua', spec 16.1). Fix: date_policy = DatePolicyT = Literal["local_date"].
rationale: >
  Spec §5.4 chỉ định nghĩa DUY NHẤT giá trị local_date (grep toàn spec: 1 lần, không có giá trị khác).
  Enum-hoá đúng chỗ = ở model (thuần, không cần clock/offset — khác INV-05-today ở DEC-029). Sai giá trị →
  pydantic ValidationError → E-SCHEMA (nhất quán taxonomy). KHÔNG cần CR: code khớp lại spec + siết theo
  triết lý strict, không đổi spec/registry/bề mặt lệnh. Nếu tương lai spec thêm chế độ ngày mới → mở rộng
  Literal qua change request (khai báo tường minh, không để str mờ).
evidence:
  - "spec dòng 362: 'date_policy: local_date'; grep date_policy toàn spec → chỉ 1 giá trị"
  - "models.py: DatePolicyT = Literal['local_date']; VaultState.date_policy: DatePolicyT = 'local_date'"
  - "RED-first: test_bad_date_policy_rejected (date_policy='utc' → DID NOT RAISE trước fix = RED; sau fix RAISE = GREEN) + test_default_and_explicit_local_date_ok"
  - "ran-test: full suite 323 passed (321 + 2); validator full scope demo pass:true (date_policy local_date)"
  - "đồng bộ doc: schemas/vault_state.schema.md dòng date_policy → 'enum, chỉ local_date'"
verified: true
method: ran-test
status: active
reversible: "Đổi lại thành str nếu cần nới (không nên — mất lưới bắt lỗi cấu hình)."
```

---

## DEC-031 — `/forget` đóng phiên nếu xoá lesson đang mở (fix gốc) + validator bắt `open_session` dangling

```yaml
id: DEC-031
type: decision
date: 2026-07-04
title: "Chống open_session dangling: cmd_forget clear open_session khi xoá lesson đang mở + validator kiểm open_session.lesson_id tồn tại"
spec_ref: "INV-03 (spec dòng 665: 'Mọi tham chiếu ... trỏ tới đối tượng tồn tại'); §11B.2 (vòng đời open_session); spec 10.3a (/forget)"
summary: >
  Phát hiện (đọc mã, kiểm chứng RED): cmd_forget chỉ đồng bộ current_lesson khi xoá lesson, KHÔNG dọn
  open_session. Nếu /forget lesson ĐANG là open_session.lesson_id → con trỏ phiên TREO vào lesson đã xoá
  (dangling). Validator cũng không bắt (INV-03 liệt kê tường minh prerequisites/current_lesson/lessons[].id/
  prompt_ref — KHÔNG có open_session). ⇒ state sai âm thầm: /status cảnh báo phiên trên lesson không tồn tại.
  Fix HAI TẦNG (phòng thủ theo chiều sâu, đúng vai validator = lưới an toàn cuối):
    (1) GỐC — cmd_forget: nếu open_session.lesson_id == lesson bị xoá → clear lesson_id/started_at trong
        CÙNG write vault_state (song song sync current_lesson). Ngăn hệ TẠO RA state xấu.
    (2) LƯỚI — validate_full_core: open_session.lesson_id (nếu != null) phải ∈ all_lesson_ids, else E-REF-BROKEN.
        Bắt vector khác: người dùng SỬA TAY vault_state trỏ bậy (hệ file cho phép sửa tay).
rationale: >
  'Fix tận gốc': gốc là cmd_forget bỏ quên một con trỏ tham chiếu tới lesson — sửa ở nơi tạo ra state.
  Thêm lưới validator vì INV-03 có TINH THẦN 'MỌI tham chiếu trỏ đối tượng tồn tại' (câu spec mở đầu bằng
  'Mọi tham chiếu'); open_session.lesson_id LÀ một tham chiếu tới lesson ⇒ diễn giải mở rộng danh sách
  tường minh của INV-03 để phủ nó. Đây là QUYẾT ĐỊNH DIỄN GIẢI (spec không liệt kê open_session tường minh)
  — ghi nhận trung thực, không tự nhận spec nói. E-REF-BROKEN (nhất quán mã với các ref khác).
evidence:
  - "RED-first (2 test): test_open_session_lifecycle::test_forget_open_lesson_clears_session (RED: open_session vẫn 'docker/lesson-001' sau forget) → GREEN sau fix cmd_forget"
  - "RED-first: test_inv03_refs::test_bad_open_session_lesson (RED: E-REF-BROKEN not in set()) → GREEN sau khi thêm check validator"
  - "session.py cmd_forget: khối (3) vs_dirty — clear open_session khi sess.lesson_id == lesson_id"
  - "validate.py validate_full_core: open_session.lesson_id ∉ all_lesson_ids → E-REF-BROKEN"
  - "ran-test: full suite 328 passed (326 + 2); validator full scope demo pass:true (open_session null → check bỏ qua)"
verified: true
method: ran-test
status: active
interpretation_note: "Mở rộng INV-03 (danh sách tường minh) sang open_session.lesson_id theo tinh thần 'Mọi tham chiếu'. Nếu chủ dự án muốn bó hẹp đúng danh sách → gỡ check validator, giữ fix driver (gốc)."
reversible: "Gỡ 3 dòng check validator (tầng lưới) và/hoặc khối clear open_session trong cmd_forget."
```

---

## DEC-032 — Đồng nhất duyệt TẤT ĐỊNH trong os.walk (INV-17/18) — khép guarantee determinism/portability

```yaml
id: DEC-032
type: decision
date: 2026-07-04
title: "Sort dirnames + sorted(filenames) trong _check_no_code_in_vault/_check_no_data_in_system"
spec_ref: "spec §0/§1 (determinism: 'validate 2 lần report giống hệt'); INV-16 (portable); INV-17/18"
summary: >
  Audit tính tất định thứ tự báo lỗi cross-machine. Toàn bộ codebase duyệt thư mục bằng sorted(...) (tất
  định), TRỪ 2 hàm INV-17/18 dùng os.walk THÔ — os.walk trả dir/file theo thứ tự FILESYSTEM (khác nhau
  giữa máy/OS). Hệ quả: vault/_system có NHIỀU vi phạm ⇒ thứ tự lỗi E-MIX-CODE/E-MIX-DATA (⇒ report) LỆCH
  giữa các máy, làm yếu lời hứa 'report giống hệt' + portable. Fix GỐC (đồng nhất, không vá ngọn):
    - dirnames[:] = sorted(...) → os.walk descend theo thứ tự tất định.
    - for fn in sorted(filenames) → thứ tự lỗi trong mỗi dir tất định.
  Kết quả: report = DFS top-down với anh-em đã sort ⇒ TẤT ĐỊNH mọi máy (không còn phụ thuộc FS).
rationale: >
  Determinism là cam kết cốt lõi (§0/§1) và test_p12 CHỈ kiểm 'chạy 2 lần CÙNG máy' → KHÔNG bắt được lệch
  cross-machine do os.walk. Đây là điểm DUY NHẤT lệch convention sorted() của dự án ⇒ sửa cho đồng nhất là
  đúng bản chất. Các iterdir không-sort khác đã xét: _collect_all_lesson_ids (kết quả là SET dùng cho 'in'
  → thứ tự vô hại) và _build_overlay (chỉ copy → vô hại) — KHÔNG cần đổi.
evidence:
  - "grep iterdir/rglob/glob/os.walk validator/*.py: chỉ 2 os.walk (INV-17/18) là non-sorted có ảnh hưởng thứ tự lỗi"
  - "RED-first: test_inv17_18_determinism.py monkeypatch os.walk trả filenames ĐẢO → trước fix lỗi ra đảo (đỏ), sau fix sorted (xanh)"
  - "test cây tmp thật: report = ['run.js','alpha/a.py','zeta/z.py'] (DFS top-down sorted-siblings) — thứ tự cố định, không theo FS"
  - "ran-test: full suite 336 passed (333 + 3); validator full scope demo pass:true"
verified: true
method: ran-test
status: active
note: "Thứ tự KHÔNG phải 'flat sorted' mà là 'DFS top-down, anh-em sorted' (os.walk phát cha trước con) — vẫn tất định tuyệt đối cross-machine, đó là điều cam kết cần."
reversible: "Gỡ .sort()/sorted() (không nên — tái mở lỗ hổng thứ tự lỗi theo FS)."
```

---

## DEC-033 — `occ_recheck` ABORT khi E-CONCURRENT-EDIT (khớp spec §10.3; chống .tx 'prepared' treo)

```yaml
id: DEC-033
type: decision
date: 2026-07-04
title: "OCC mốc-2 lệch → tx.abort() rồi mới raise (đồng nhất với nhánh validate-fail; không để manifest kẹt 'prepared')"
spec_ref: "spec §10.3 ('trước COMMIT... lệch → E-CONCURRENT-EDIT, abort'); §10.3 6b (aborted giữ .tx để truy vết)"
summary: >
  Audit vùng transaction recovery (chịu-lực nhất). Test P08 rất đầy đủ (happy/abort/crash-recover/
  atomic-manifest/OCC-2-mốc/retry/multi-root/finalize-after-commit). PHÁT HIỆN gap spec-vs-code: spec §10.3
  nói OCC mốc-2 lệch → 'E-CONCURRENT-EDIT, ABORT', nhưng occ_recheck() chỉ raise TxError, KHÔNG gọi abort()
  → manifest kẹt state 'prepared'. Hệ quả: (1) lệch chữ 'abort' của spec; (2) .tx/<id> treo mãi vì
  scan_incomplete CHỈ nhặt committing/interrupted/committed (không nhặt 'prepared') → rò rỉ .tx dần;
  (3) không đồng nhất với nhánh validate-fail (_run_tx gọi tx.abort()). Fix: occ_recheck() gọi self.abort()
  TRƯỚC khi raise. Sau fix: mọi thất bại TRƯỚC-COMMIT đều chuyển terminal 'aborted' (giữ .tx để truy vết, §6b);
  chỉ thất bại TRONG/ SAU commit mới đi đường recover roll-forward (KHÔNG abort — đúng, không đổi).
rationale: >
  occ_recheck là điểm kiểm DUY NHẤT ngay trước commit → abort-on-fail luôn đúng ngữ nghĩa ở đây (khác commit()
  không bao giờ được abort). Đặt abort() TRONG occ_recheck để MỌI caller (driver _run_tx + test + tương lai)
  có hành vi đúng spec, không phải nhớ abort thủ công. Fix ở gốc (hợp đồng OCC = detect+abort như spec ghép
  chung), không vá ngọn ở từng caller.
evidence:
  - "RED-first: siết test_concurrent_edit_between_begin_and_commit thêm assert state=='aborted' → trước fix 'prepared' (đỏ), sau fix 'aborted' (xanh); + assert file thật giữ bản sửa tay (không ghi đè)"
  - "transaction.py occ_recheck: self.abort() trước raise TxError('E-CONCURRENT-EDIT')"
  - "ran-test: phase08_tx 35 passed; full suite 336 passed; validator full scope demo pass:true"
verified: true
method: ran-test
status: active
known_minor: >
  Còn 2 ca .tx orphan MINOR (housekeeping, KHÔNG lệch spec, KHÔNG sai vault): (a) E-STALE-CONTEXT ở begin()
  raise TRƯỚC khi _save manifest → .tx/<id> có backup nhưng không manifest.json → scan_incomplete bỏ qua
  (đúng: spec 'abort=không stage', file thật chưa đụng); (b) crash đúng giữa begin và stage để lại state
  'prepared'. Cả hai real-vault-an-toàn; chỉ tích .tx rác rất hiếm. Dọn .tx rác (GC theo tuổi/aborted) là
  việc P11/housekeeping, ghi nhận để KHÔNG tự thêm luật GC lúc này (tránh over-reach — spec chưa yêu cầu).
reversible: "Gỡ self.abort() trong occ_recheck (sẽ tái lệch spec + .tx treo)."
```

---

## DEC-034 — Nối dây `E-IO-ENCODING` ở BIÊN validator (non-UTF-8 → report sạch, không crash)

```yaml
id: DEC-034
type: decision
date: 2026-07-04
title: "validate_light/core/semantic bọc EIoEncoding → rep.err('E-IO-ENCODING'); file non-UTF-8 không còn crash validator"
spec_ref: "spec §10.4 (bảng mã lỗi có E-IO-ENCODING); §19 dòng 1413 ('Decode fail → E-IO-ENCODING'); PHASE_05"
summary: >
  Truy từ audit coverage (NOTE-013): E-IO-ENCODING là mã spec §10.4 định nghĩa NHƯNG không nằm trong 39 mã
  emit thật. Đọc mã: vault_io.read_text() raise EIoEncoding (typed) đúng, và test_io.py chỉ test read_text ở
  mức UNIT — nhưng KHÔNG nơi nào ở validate.py/session.py/transaction.py CATCH EIoEncoding → file non-UTF-8
  trong vault làm EIoEncoding propagate UNCAUGHT → validator CRASH (traceback), KHÔNG trả report
  {pass:false, E-IO-ENCODING}. Robustness gap: user lưu file cp1252/latin-1 → crash thay vì FAIL sạch.
  Fix GỐC (ở BIÊN validator, không vá từng read site): 3 entry public (validate_light/validate_full_core/
  validate_full_semantic) tách thân → _impl, wrapper bọc try/except VIO.EIoEncoding → _emit_io_encoding
  (rep.err 'E-IO-ENCODING' + path tương đối). Mọi read site lồng nhau raise đều gom về biên → không crash.
  EIoEncoding mang thêm .path để báo đúng file. _emit_io_encoding dedupe theo file (core+semantic cùng đọc
  1 file lỗi → chỉ báo 1 lần, report tất định).
rationale: >
  Đặt ở BIÊN (3 entry) thay vì bọc từng read site: 1 chỗ/entry phủ MỌI read lồng nhau (fix gốc, không rải).
  Chọn catch trong chính hàm entry (không phải ở main()/validate_staged) để MỌI caller — CLI, transaction,
  test — đều nhận report sạch, không phải nhớ bọc. commit()/recover KHÔNG đụng (chỉ đọc validate). dedupe
  giữ report tất định (đúng cam kết §0/§1). Đây là mã spec-định-nghĩa bị under-wire, không phải luật mới.
evidence:
  - "RED-first: tests/phase07a_core/test_io_encoding_report.py (5 test: core/light/semantic trên lesson.md + lesson_state.md non-UTF-8 → phải emit; demo UTF-8 → không). Trước fix: 4 fail do EIoEncoding raise uncaught (crash). Sau fix: 5 passed"
  - "vault_io.py: EIoEncoding(.path); validate.py: _emit_io_encoding (dedupe) + 3 wrapper _impl"
  - "drift-guard test_validation_rules_codes bắt E-IO-ENCODING mới emit → đã đồng bộ rules/validation_rules.md (bảng + khối máy-đọc). Cả hai chiều doc↔code khớp lại"
  - "audit lại: EMITTED=40, thiếu-test=0 (mọi mã có test FAIL, kể cả E-IO-ENCODING mới)"
  - "ran-test: full suite 341 passed (336 + 5); validator full scope demo pass:true"
verified: true
method: ran-test
status: active
note: "NOTE-013 cập nhật: 39→40 mã emit, vẫn 40/40 có test FAIL. Đây là ví dụ drift-guard (DEC-005) tự bắt lỗi doc↔code khi thêm mã — đúng thiết kế."
reversible: "Gỡ 3 wrapper + _emit_io_encoding → EIoEncoding lại propagate (tái crash); gỡ E-IO-ENCODING khỏi validation_rules.md."
```

---

## DEC-035 — Driver `session.py main()` cũng báo `E-IO-ENCODING` sạch (hoàn tất robustness non-UTF-8)

```yaml
id: DEC-035
type: decision
date: 2026-07-04
title: "3 khối dispatch main() bọc VIO.EIoEncoding → E-IO-ENCODING (không crash driver trên file non-UTF-8)"
spec_ref: "spec §10.4 (E-IO-ENCODING); §19; nối tiếp DEC-034 (validator boundary)"
summary: >
  DEC-034 fix ở BIÊN validator. Nhưng DRIVER đọc file TRƯỚC transaction (cmd_* → _load_raw → VIO.read_text)
  và main() KHÔNG catch VIO.EIoEncoding: read-only block + resume block catch (OSError, SessionError) —
  EIoEncoding là ValueError, KHÔNG phải OSError → lọt; write block catch EReviewBadGrade/SessionError/TxError
  → lọt. ⇒ lệnh user chạy trực tiếp (vd /status, /review) trên vault có file non-UTF-8 → CRASH traceback
  thay vì report sạch. Fix: thêm 'except VIO.EIoEncoding → _emit E-IO-ENCODING, return 1' vào CẢ 3 khối
  dispatch (read-only, resume, write). Nay non-UTF-8 được xử lý sạch ở CẢ hai tầng: validator (DEC-034)
  + driver (DEC-035).
rationale: >
  Driver là bề mặt user chạy nhiều nhất → crash-vs-clean-error quan trọng ngang validator. Cùng mã spec
  E-IO-ENCODING (không chế mã mới). Đặt catch ở main() dispatch (điểm gom lỗi của driver, cùng chỗ đã catch
  SessionError/TxError) — đúng tầng, không rải vào từng cmd_*. Hoàn tất nhất quán câu chuyện robustness
  non-UTF-8 mà DEC-034 mở ra (fix gốc: mọi ĐƯỜNG VÀO đọc-file đều convert IO-error → report-error, không crash).
evidence:
  - "RED-first: test_session_cli.py::test_cli_review_non_utf8_reports_io_encoding + test_cli_status_non_utf8_reports_io_encoding (lesson_state non-UTF-8). Trước fix: main() raise EIoEncoding uncaught (crash). Sau fix: exit 1 + errors[0].error_code=='E-IO-ENCODING'"
  - "session.py main(): +except VIO.EIoEncoding ở read-only/resume/write dispatch"
  - "ran-test: full suite 343 passed (341 + 2); validator full scope demo pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ 3 except VIO.EIoEncoding trong main() (tái crash driver trên non-UTF-8)."
```

---

## DEC-036 — `begin()` dọn `.tx/<id>` dở khi lỗi trước-manifest (đóng orphan E-STALE-CONTEXT của DEC-033)

```yaml
id: DEC-036
type: decision
date: 2026-07-04
title: "begin() bọc _begin_impl: lỗi trước khi manifest bền vững → rmtree tx_dir dở (chống orphan backup rò rỉ)"
spec_ref: "spec §10.3 (E-STALE-CONTEXT: 'ABORT, KHÔNG stage'); nối tiếp DEC-033 known_minor (a)"
summary: >
  DEC-033 ghi known_minor: begin() khi raise E-STALE-CONTEXT đã mkdir staged/backup + copy vài backup NHƯNG
  raise TRƯỚC _save() → .tx/<id> có backup nhưng KHÔNG manifest.json → scan_incomplete bỏ qua (cần manifest)
  → orphan KHÔNG BAO GIỜ dọn → rò rỉ backup dần (vault chạy lâu). Fix GỐC (hygiene transaction chuẩn): begin()
  bọc _begin_impl trong try/except; lỗi bất kỳ (E-STALE-CONTEXT hoặc IO khi _save) TRƯỚC khi manifest bền
  vững → shutil.rmtree(tx_dir) rồi re-raise. Vì _save() là dòng CUỐI của _begin_impl nên mọi exception ⇒
  manifest chưa bền vững ⇒ dọn an toàn. tx_id unique (timestamp+uuid) nên rmtree không đụng tx khác.
rationale: >
  E-STALE-CONTEXT nghĩa là transaction CHƯA thực sự bắt đầu (chưa manifest, chưa stage, file thật chưa đụng)
  → KHÔNG có gì để 'truy vết' như aborted (§6b chỉ giữ .tx cho tx ĐÃ có manifest). Dọn phần dở của chính
  begin là đúng bản chất 'abort=không để lại residue'. Đây là fix GỐC (begin tự dọn khi thất bại), không
  phải GC quét-theo-tuổi (cái đó là housekeeping/P11, vẫn KHÔNG làm — tránh over-reach).
scope_note: >
  CÒN LẠI (known_minor (b) của DEC-033, CHƯA đóng): crash đúng khe giữa _save (state=prepared) và stage() →
  orphan 'prepared' CÓ manifest. begin()-cleanup KHÔNG phủ (begin đã xong). Dọn 'prepared' cần recover()
  discard-prepared hoặc GC — là quyết định policy (recover đang chỉ roll-forward committing/interrupted/
  committed). Real-vault vẫn an toàn (prepared = chưa commit). Để lại cho spec-owner/P11, KHÔNG tự thêm.
evidence:
  - "RED-first: siết test_stale_context_between_read_and_begin thêm assert 'not tx.tx_dir.exists()' → trước fix tx_dir tồn tại (đỏ), sau fix đã dọn (xanh)"
  - "transaction.py: begin() = try _begin_impl except BaseException → rmtree(tx_dir) + raise"
  - "ran-test: phase08_tx 35 passed; full suite 343 passed"
verified: true
method: ran-test
status: active
reversible: "Gỡ wrapper begin() (tái orphan .tx khi E-STALE-CONTEXT)."
```

---

## DEC-037 — `current_topic` phải trỏ topic tồn tại (hoàn tất reference-integrity vault_state, cùng diễn giải DEC-031)

```yaml
id: DEC-037
type: decision
date: 2026-07-04
title: "validate_full_core kiểm vault_state.current_topic trỏ topic có DIR; else E-REF-BROKEN (INV-03)"
spec_ref: "INV-03 ('Mọi tham chiếu ... trỏ tới đối tượng tồn tại'); cùng diễn giải đã chốt DEC-031"
summary: >
  Soát reference-integrity của MỌI con trỏ trong vault_state. Trước: kiểm current_lesson (INV-03 tường minh)
  + open_session.lesson_id (DEC-031, diễn giải 'mọi tham chiếu'). BỎ SÓT: current_topic — cũng là tham chiếu
  tới topic — KHÔNG được kiểm tồn tại. Vault sửa tay current_topic='ghost' (current_lesson=null) → dangling
  lọt lưới → /status báo topic không tồn tại. Fix: current_topic (nếu != null) phải có DIR topics/<current_topic>/.
  QUAN TRỌNG: kiểm DIR tồn tại, KHÔNG suy từ all_lesson_ids — vì topic RỖNG (có dir, 0 lesson) là HỢP LỆ
  (vd sau /forget lesson cuối) và không xuất hiện trong all_lesson_ids → dùng all_lesson_ids sẽ bắt oan.
rationale: >
  Nhất quán với diễn giải INV-03 đã thiết lập ở DEC-031 (open_session): 'Mọi tham chiếu' phủ current_topic.
  Hoàn tất bộ: cả 3 con trỏ vault_state (current_lesson, open_session.lesson_id, current_topic) đều được
  kiểm tồn tại → không còn dangling pointer nào lọt. Đây KHÔNG phải luật mới/over-reach: cùng đúng một diễn
  giải người dùng đã chấp nhận ở DEC-031; chỉ là bịt nốt con trỏ còn sót. Kiểm DIR (không all_lesson_ids)
  để tôn trọng topic rỗng hợp lệ — verified bằng test không-false-positive.
evidence:
  - "RED-first: test_inv03_refs.py::test_bad_vault_current_topic (current_topic='ghost-topic',current_lesson=null → trước fix set() rỗng/đỏ, sau fix E-REF-BROKEN) + test_valid_empty_topic_current_topic_ok (topic rỗng có dir → KHÔNG bắt oan)"
  - "validate.py _validate_full_core_impl: cur_topic không có dir topics/<cur_topic> → E-REF-BROKEN"
  - "ran-test: inv03_refs 7 passed; full suite 345 passed; validator full scope demo pass:true (current_topic='docker' có dir)"
verified: true
method: ran-test
status: active
reversible: "Gỡ 3 dòng check current_topic (tái mở dangling pointer)."
```

---

## DEC-038 — `read_text` dùng `utf-8-sig` (bỏ BOM) — chống 'thiếu front-matter' oan + lệch reader

```yaml
id: DEC-038
type: decision
date: 2026-07-04
title: "vault_io.read_text decode utf-8-sig: bỏ BOM đầu file (editor Windows hay thêm) — nếu không, split_frontmatter báo oan + driver/validator đọc lệch nhau"
spec_ref: "spec §19 (đọc UTF-8 rõ ràng, Windows-safe); phát hiện qua pilot self-simulate"
summary: >
  BUG (pilot): file *_state.md lưu bằng editor Windows (Notepad/PowerShell Set-Content -Encoding utf8) có
  BOM UTF-8 (EF BB BF) đầu file. read_text (encoding='utf-8') GIỮ BOM (\ufeff). Hệ quả LỆCH HAI READER:
    - validator split_frontmatter dùng text.startswith('---') → BOM → False → 'thiếu front-matter' (E-SCHEMA);
    - driver _load_raw._split dùng text.split('---',2) → BOM lọt vào prefix bỏ đi → VẪN đọc được.
  ⇒ /done regen view từ lesson (đọc được qua _load_raw) nhưng validator KHÔNG parse được → E-SCHEMA +
  E-VIEW-MISMATCH. Fix GỐC ở choke point DUY NHẤT: read_text decode 'utf-8-sig' → bỏ BOM đầu nếu có, file
  không-BOM đọc y nguyên, byte UTF-8 THẬT hỏng vẫn raise EIoEncoding (giữ E-IO-ENCODING/DEC-034). Cả hai
  reader nay nhất quán.
rationale: >
  BOM là artifact Windows RẤT phổ biến (spec §19 nhấn mạnh Windows-safe). 'thiếu front-matter' khi front-matter
  RÕ RÀNG có mặt là lỗi gây bối rối + che bug thật. Fix ở read_text (1 điểm) khiến MỌI reader (driver+validator)
  đồng nhất — đúng bản chất 'một nguồn đọc, không lệch'. Driver ghi (_dump_state → encode utf-8, KHÔNG BOM)
  không đổi; chỉ đường ĐỌC robust hơn.
evidence:
  - "RED-first: test_io.py::test_read_text_strips_utf8_bom (BOM+'---' → text.startswith('---') phải True) + test_read_text_bom_does_not_mask_real_bad_encoding (byte hỏng vẫn raise)"
  - "vault_io.read_text: encoding='utf-8-sig'"
  - "ran-command (pilot): trước fix /done python learned FAIL E-SCHEMA+E-VIEW-MISMATCH do BOM; sau fix qua được bước BOM"
  - "ran-test: phase05_io 8 passed; full suite 347→348 passed"
verified: true
method: ran-test
status: active
reversible: "Đổi lại 'utf-8' (tái intolerant BOM); không nên."
```

---

## DEC-039 — `/done`/`/review`/`/forget` regen ĐỒNG BỘ `topic_state.lessons[].status` (view §4)

```yaml
id: DEC-039
type: decision
date: 2026-07-04
title: "_regen_topic_views đính lesson_status; _apply_views_to_topic_raw đồng bộ index status từ lesson_state (spec §4/INV-25)"
spec_ref: "spec §4 ('topic_state.lessons[].status phải được sinh/đồng bộ từ lesson_state.status'); INV-25; pilot"
summary: >
  BUG (pilot self-simulate): đưa lesson tới 'learned' (status đổi not_started→learned) rồi /done → E-INDEX-
  MISMATCH: 'index status not_started != lesson_state learned'. Gốc: topic_state.lessons[].status là VIEW
  đồng bộ từ lesson_state.status (spec §4), nhưng driver regen (_apply_views_to_topic_raw) chỉ đồng bộ
  review_schedule/assessment/has_draft_knowledge — QUÊN lessons[].status. Index status chỉ set lúc /learn
  (creation) + /forget (xoá), KHÔNG re-sync khi status lesson đổi → stale → E-INDEX-MISMATCH ở validate kế.
  Auto-test loop cũ KHÔNG bắt vì không đổi lesson.status rồi regen. Fix: _regen_topic_views đính
  regen['lesson_status']={lid:status}; _apply_views_to_topic_raw set ts.lessons[].status theo đó (khớp id).
rationale: >
  Index status là VIEW (§4) → phải regen ở MỌI đường đụng topic_state, không chỉ 3 view kia. Đặt trong regen
  (1 chỗ) → /review /done /forget đều đồng bộ (fix gốc). cmd_learn dùng _regen_from_models (stage=core, KHÔNG
  có lesson_status) + set index thủ công lúc tạo → wrapper .get('lesson_status')=None → bỏ qua, không đụng.
  Validator _check_views tự regen riêng (stage=core) nên key phụ 'lesson_status' KHÔNG ảnh hưởng.
evidence:
  - "RED-first: test_session_done.py::test_done_syncs_topic_index_status_from_lesson (đổi lesson→needs_review; trước fix E-INDEX-MISMATCH/committed False, sau fix committed True + index='needs_review')"
  - "session.py _regen_topic_views: regen['lesson_status']={m.lesson_id:m.status}; _apply_views_to_topic_raw sync"
  - "ran-command (pilot): sau fix /done python learned → committed:true, pass:true; topic_state.lessons[0].status='learned', assessment avg khớp (concept/explain/apply=2, critique=1, teachback=2)"
  - "ran-test: full suite 348 passed; validate FULL độc lập trên pilot vault pass:true"
verified: true
method: ran-test
status: active
reversible: "Gỡ lesson_status trong regen (tái E-INDEX-MISMATCH khi status đổi)."
```


## DEC-040 — `Card.step` phải `Optional[int]` (py-fsrs đặt step=None ở state Review) — fix gốc under-modeling

```yaml
id: DEC-040
type: decision
date: 2026-07-04
title: "models.Card.step: int → Optional[int]=None; khớp thực tế py-fsrs (Review⇒step None) + spec §29 dòng 1; RED-first (pilot vòng 3)"
spec_ref: "spec §29 (bảng vá v2.5→v2.6, dòng 1: step Optional ràng buộc theo state); §8.2; F-A; INV-08/21"
summary: >
  BUG (pilot vòng 3, review nhiều lần tiến tới mastered): /review grade 3 (Easy) đẩy card từ
  Learning step0 → State.Review. py-fsrs đặt card.step=None ở Review (step CHỈ có nghĩa trong
  Learning/Relearning — vị trí trong learning_steps/relearning_steps). Nhưng model Card.step khai
  `int` (bắt buộc, không Optional) → khi cmd_review gọi _regen_topic_views re-parse LessonState →
  pydantic ValidationError 'review_items.0.card.step Input should be a valid integer, input=None' →
  driver CRASH (chưa vào transaction, vault không đổi nhưng lệnh thất bại hoàn toàn).
  Đây là under-modeling: model chặt hơn thực tế thư viện VÀ mâu thuẫn CHÍNH spec §29 (đã tự quyết
  step là Optional, ràng buộc theo state). stability/difficulty/last_reviewed_at_utc đã Optional từ
  trước — CHỈ step bị bỏ sót. Auto-test bỏ sót vì MỌI test review dùng grade=2 (Good, giữ Learning,
  step vẫn int); chưa test nào đẩy card sang Review.
root_cause: >
  Gốc là SCHEMA sai (thiếu phản ánh state=Review⇒step=None của py-fsrs), KHÔNG phải logic driver.
  Fix ở nguồn dữ liệu: Card.step -> Optional[int]=None (nhất quán với 3 field Optional cạnh nó).
why_not_enforce_state_step: >
  KHÔNG thêm model-invariant 'step None iff state==Review'. Lý do: (1) tính đúng đắn state↔step đã
  do REPLAY (INV-08) đảm bảo — cards_equal so a['step']!=b['step'], nên step giả (sai state) sẽ lệch
  card replay → E-REVIEW-MISCALC; đây cùng cơ chế bảo vệ stability/difficulty (Optional ở model,
  đúng-đắn ở replay). (2) Thêm invariant tĩnh trùng lặp lưới replay = ceremony, và rủi ro sai giả
  định về Relearning.step. Giữ tối giản, đúng bản chất: model chấp nhận cấu trúc py-fsrs sinh ra;
  validator replay là chốt đúng-đắn.
lifecycle_verified: >
  Chứng minh fix xử lý TOÀN BỘ vòng đời step qua CLI thật (pilot3_vault): Learning(step int) →
  [Easy] Review(step None, stability 8.30) → [Easy] Review(stability 65.62 ≥ 60 ⇒ mastered) →
  [Again] Relearning(step 0 int trở lại, need_redo). validate FULL PASS ở mọi bước.
evidence:
  - "RED-first: test_session_review.py::test_review_easy_enters_review_state_step_none (grade 3 → Review, step None; TRƯỚC fix ValidationError crash, SAU fix committed True + validate_full_core PASS)"
  - "py-fsrs verify trực tiếp (ran-command): Card(Learning,step0) --Rating.Easy--> state=Review, step=None, stability=8.2956"
  - "models.py: Card.step: Optional[int] = None (kèm comment spec §29 + INV-08)"
  - "ran-command (pilot): chuỗi /review grade 3,3,0 → mastered rồi need_redo; validate FULL --scope full pass:true mỗi bước (đạt mastered lần đầu qua CLI thật)"
  - "ran-test: full suite 349 passed (348 + 1 RED test)"
verified: true
method: ran-test
status: active
reversible: "Đổi lại step:int (tái crash khi card vào Review). Không nên."
```


## DEC-041 — Biên đọc-parse của driver suy biến duyên dáng: file on-disk hỏng → E-SCHEMA/E-SCHEMA-YAML SẠCH, không crash

```yaml
id: DEC-041
type: decision
date: 2026-07-04
title: "SchemaError(SessionError) ở _load_raw + _lesson_model_from_raw → main() báo mã lỗi sạch; chọn bọc-biên (C) thay pre-flight (B); RED-first (pilot vòng 4)"
spec_ref: "spec §10.4 (báo lỗi sạch), §10.6 (mã lỗi chuẩn E-SCHEMA/E-SCHEMA-YAML), §19 (robustness); an toàn sản phẩm thương mại"
summary: >
  BUG lớp robustness (pilot vòng 4, tổng quát hoá DEC-040): file lesson_state/topic_state bị SỬA TAY
  hỏng (schema sai / YAML hỏng / thiếu front-matter) khiến /review /done /forget CRASH bằng stack trace
  thô — vì tầng đọc-parse driver có 3 bề mặt lỗi KHÔNG được main() bắt: (1) _split → IndexError khi
  thiếu '---'; (2) _load_raw yaml.safe_load → YAMLError; (3) _lesson_model_from_raw M.LessonState() →
  pydantic ValidationError. Driver regen (_regen_topic_views) re-parse các file (target + sibling) TRƯỚC
  khi transaction FULL-validate kịp bắt → traceback lộ ra người dùng. Validator thì xử lý cả 3 duyên
  dáng (_parse_state_model + split_frontmatter → E-SCHEMA*), driver thì KHÔNG.
root_cause: >
  Bản chất: tầng đọc-parse của driver THIẾU BIÊN LỖI (error boundary). On-disk file không đảm bảo hợp lệ
  (người dùng sửa tay được) nhưng driver parse thẳng vào pydantic/yaml không bọc. Fix ở đúng tầng đó:
  _load_raw + _lesson_model_from_raw raise SchemaError(path, error_code, msg); main() dùng
  getattr(e,'error_code','E-DRIVER') → SchemaError ra E-SCHEMA/E-SCHEMA-YAML chính xác, SessionError
  thường vẫn E-DRIVER. Happy-path KHÔNG đổi (guard chỉ kích khi input hỏng).
design_choice: >
  Chọn (C) BỌC-BIÊN parse thay vì (B) PRE-FLIGHT validate cả-topic-trước-khi-mutate. Lý do CHÍNH XÁC
  (kiểm chứng thực nghiệm): (B) sẽ CHẶN NHẦM /forget một lesson ĐANG HỎNG — nhưng regen của /forget LOẠI
  lesson đó ra (exclude_lesson_id), không parse nó, nên forget PHẢI thành công (dọn được rác). (C) chỉ
  kích trên đúng file THỰC SỰ được parse → đúng cho MỌI lệnh. Ngoài ra (C) khớp cách validator đã làm
  (parse→emit E-SCHEMA), single choke point, không đụng spec/registry (không cần CR).
empirical_validation: >
  ran-command 2 ca chứng minh thiết kế: (a) /review khi SIBLING lesson-002 hỏng → E-SCHEMA sạch (sibling
  bị parse lúc regen → bắt); (b) /forget lesson-002 ĐANG HỎNG → committed=True, dir đã xoá (regen loại nó,
  không parse) — (B) sẽ sai ở ca này.
evidence:
  - "RED-first: test_session_cli.py::{test_cli_review_corrupt_schema_reports_clean → E-SCHEMA;
     test_cli_review_broken_yaml_reports_clean → E-SCHEMA-YAML; test_cli_review_missing_frontmatter_reports_clean
     → E-SCHEMA}. TRƯỚC fix: IndexError/YAMLError/ValidationError traceback thô; SAU fix: JSON mã lỗi sạch, committed False"
  - "session.py: class SchemaError(SessionError) {path,error_code}; _load_raw guard (thiếu-fm/YAMLError/non-dict);
     _lesson_model_from_raw try/except → SchemaError; 3 handler main() dùng getattr error_code; path threaded vào regen/all_lessons/test"
  - "ran-command: /done trên vault hỏng (score 99) → E-SCHEMA sạch kèm path; /review sibling hỏng → E-SCHEMA; /forget lesson hỏng → thành công"
  - "ran-test: full suite 352 passed (349 + 3 RED test)"
verified: true
method: ran-test
status: active
known_minor: "Message SchemaError mang ĐƯỜNG DẪN TUYỆT ĐỐI (driver helper không có vault_root context). Là diagnostic, KHÔNG phải vault content nên INV-16 không áp; chấp nhận (giúp user tìm file). Làm relative sẽ phải thread vault_root qua mọi helper — invasive, hoãn."
reversible: "Gỡ SchemaError + guard (tái crash traceback trên file hỏng). Không nên."
```


## DEC-042 — Driver validate vault_state qua model khi đọc (`_load_vault_state`): sai-kiểu → E-SCHEMA sạch, không crash

```yaml
id: DEC-042
type: decision
date: 2026-07-04
title: "_load_vault_state validate qua M.VaultState (cùng normalize validator) rồi trả raw; wire 14 site đọc vault_state; RED-first (pilot vòng 5)"
spec_ref: "spec §10.4/§10.6/§19 (robustness, mã lỗi sạch); §5.4 (vault_state); nối tiếp DEC-041"
summary: >
  BUG robustness (pilot vòng 5, tầng sâu hơn DEC-041): các lệnh ĐỌC (status/schedule/resume/…) thao tác
  trên RAW DICT vault_state, giả định kiểu field — vs_raw.get('open_session') rồi .get(...), '/' in
  current_lesson. Nếu vault_state YAML HỢP LỆ nhưng SAI KIỂU (open_session=chuỗi → AttributeError
  'str has no get'; current_lesson=int → TypeError 'int not iterable'), lệnh CRASH traceback thô. _load_raw
  guard (DEC-041) KHÔNG bắt vì YAML parse được — lỗi ở tầng truy cập field, không ở tầng parse.
root_cause: >
  Bản chất (cùng lớp DEC-038 driver-đọc-khác-validator + DEC-041 thiếu-biên-lỗi): driver đọc vault_state
  KHÔNG qua model validation, trong khi validator có M.VaultState bắt các lỗi này (E-SCHEMA). Fix ở tầng
  đọc: _load_vault_state(vault) = _load_raw (guard fm/YAML) + validate M.VaultState (cùng normalize_yaml_object
  + _STR_FIELDS như validator) → sai kiểu ra E-SCHEMA sạch; trả raw để lệnh dùng/ghi (raw đảm bảo đúng kiểu
  sau khi model PASS). Wire 14 site đọc vault_state (10 raw-only + 4 (raw,body)).
why_consistent_not_divergent: >
  Dùng ĐÚNG normalize_yaml_object + _STR_FIELDS của validator → driver và validator chấp nhận/từ chối
  CÙNG tập vault_state (đã kiểm: current_lesson/current_topic KHÔNG nằm _STR_FIELDS nên KHÔNG bị lossy-coerce
  int→str; strict=True reject → E-SCHEMA ở CẢ HAI). Không tái tạo lệch driver↔validator (bài học DEC-038).
  Happy-path KHÔNG đổi: 354 test cũ vẫn xanh ⇒ validate là no-op trên vault hợp lệ.
recursion_trap_avoided: >
  Định nghĩa _load_vault_state ban đầu chứa chính chuỗi _load_raw(vault / 'vault_state.md'); nếu global-replace
  chuỗi đó → helper tự gọi mình → đệ quy vô hạn. Đã đổi helper dùng biến trung gian `vs` (_load_raw(vs))
  TRƯỚC khi wire → tránh bẫy. (Ghi lại: cẩn trọng khi refactor global-replace đụng định nghĩa tự-tham-chiếu.)
evidence:
  - "RED-first: test_session_cli.py::{test_cli_status_vault_state_wrong_type_reports_clean (open_session=chuỗi → E-SCHEMA);
     test_cli_resume_vault_state_wrong_type_reports_clean (current_lesson=int → E-SCHEMA)}. TRƯỚC fix: AttributeError/TypeError traceback"
  - "session.py: def _load_vault_state (validate M.VaultState) + wire 10 (_load_raw(vault/vault_state.md)) + 4 (_load_raw(vs_path))"
  - "ran-command sweep: status/schedule/resume trên 2 corrupt (open_session=chuỗi, current_lesson=int) → đều E-SCHEMA sạch, KHÔNG còn crash thô"
  - "ran-test: full suite 354 passed (352 + 2 RED test); happy-path bất biến"
verified: true
method: ran-test
status: active
known_minor: "Lệnh đọc-nhiều-lần vault_state (source/done/forget/learn) nay validate 2 lần/lệnh (chi phí nhỏ, lệnh nhịp-người). Message mang path tuyệt đối (như DEC-041 known_minor)."
reversible: "Đổi _load_vault_state về _load_raw (tái crash sai-kiểu). Không nên."
```


## DEC-043 — Lệnh write validate authored-collection (topic_state.lessons + lesson_state) khi đọc: sai-kiểu → E-SCHEMA sạch, GIỮ self-heal view

```yaml
id: DEC-043
type: decision
date: 2026-07-04
title: "_load_topic_state (validate lessons qua LessonIndexEntry) + validate target lesson cmd_review + guard review_items cmd_forget; xử lý BẤT ĐỐI XỨNG có chủ đích; RED-first (pilot vòng 6)"
spec_ref: "spec §10.4/§10.6/§19 (robustness); §4 (view derived); INV-09/25; nối tiếp DEC-041/042"
summary: >
  BUG robustness (pilot vòng 6, tầng write): lệnh write ITERATE collection AUTHORED trên raw dict TRƯỚC
  khi regen/post-validate kịp bắt → sai-kiểu (YAML hợp lệ) gây crash thô: topic_state.lessons='chuỗi' →
  _apply_views_to_topic_raw 'str has no get' (review+done+forget); lesson_state.review_items sai cấu trúc →
  cmd_review/forget iterate crash; topic_state.lessons entry thiếu 'id' → forget e['id'] KeyError.
root_cause: >
  Cùng lớp DEC-042 (driver đọc raw không qua model) nhưng ở collection authored của topic_state/lesson_state
  trong lệnh write. Fix ở tầng đọc, NHƯNG với XỬ LÝ BẤT ĐỐI XỨNG CÓ CHỦ ĐÍCH (mỗi cái có lý do semantic):
    - topic_state: CHỈ validate 'lessons' (authored) qua M.LessonIndexEntry (đảm bảo id:str+status:enum).
      CỐ Ý KHÔNG validate review_schedule/assessment vì regen GHI ĐÈ chúng → validate cả M.TopicState sẽ
      CHẶN NHẦM self-heal (lệnh /done vốn sửa được view corrupt). Kiểm chứng: ca view-hash=int vẫn committed=True.
    - cmd_review target lesson: validate FULL M.LessonState (phải hợp lệ mới review được). AN TOÀN self-heal:
      card SAI-SỐ (schema hợp lệ) vẫn PASS model → cmd_review replay từ log ghi đè (INV-08); chỉ card
      SAI-SCHEMA bị reject (mà regen cũng reject — không mất năng lực).
    - cmd_forget deleted lesson: CHỈ guard review_items là list-of-map (structural). GIỮ nguyên tắc DEC-041
      'forget được rác': lesson mastery-corrupt (score 99, review_items OK) VẪN xoá được (kiểm chứng committed=True).
design_asymmetry_rationale: >
  Ba cách xử lý KHÁC nhau vì ngữ nghĩa KHÁC nhau, KHÔNG tùy tiện: review cần lesson hợp lệ (validate full);
  forget khoan dung lesson hỏng (chỉ structural, để dọn rác được); topic view tự-chữa (chỉ validate phần
  authored). Nguyên tắc chung: validate đúng phần KHÔNG được regen/recompute; để phần được tái tạo cho lớp
  regen + post-write-validate + INV-08 lo (không nhân đôi, không chặn self-heal).
evidence:
  - "RED-first: test_session_cli.py::{test_cli_done_topic_lessons_wrong_type_reports_clean; test_cli_review_topic_lessons_wrong_type_reports_clean} (lessons=chuỗi → E-SCHEMA; trước: AttributeError traceback)"
  - "session.py: _require_list_of_maps + _load_topic_state (LessonIndexEntry); wire review/done/forget; cmd_review +_lesson_model_from_raw(ls_raw); cmd_forget +_require_list_of_maps(review_items)"
  - "ran-command sweep: topic lessons=chuỗi → E-SCHEMA (review+done); view-hash=int → done VẪN committed=True (self-heal GIỮ); forget score=99 → committed=True (DEC-041 giữ); forget review_items structural → E-SCHEMA sạch"
  - "ran-test: full suite 356 passed (354 + 2 RED); happy-path bất biến"
verified: true
method: ran-test
status: active
reversible: "Gỡ _load_topic_state/guard (tái crash sai-kiểu lessons/review_items). Không nên."
```


## DEC-044 — Enforce `sources[].added <= today` (qua CR-0004 approved) — mở rộng toàn-vẹn-thời-gian INV-05

```yaml
id: DEC-044
type: decision
date: 2026-07-04
title: "_check_source_added_not_future ở validator: sources[].added > today → E-SCHEMA (CR-0004 approved); đóng DEC-029 open_question; RED-first"
spec_ref: "CR-0004 (approved); nguyên tắc INV-05 (created<=updated<=today); spec §5.3 (sources.added); §5.4/§8.5 (today=ngày lịch thật theo offset)"
summary: >
  Đóng DEC-029 open_question ('có ép sources[].added <= today không?') theo hướng CÓ, qua quy trình §12
  (CR-0004: soạn pending → spec-owner duyệt 'theo khuyến nghị' → approved → implement). Thêm
  _check_source_added_not_future trong validate.py, gọi ở _validate_topic (đường full_core, nơi đã có
  today_local + parse sources.md). Song song hoàn toàn với _check_updated_not_future (DEC-029): phần
  THỜI GIAN ở validator (cần utc_offset + mốc now cross-context), model giữ thuần.
rationale (bản chất, không ngọn): >
  `added` là dấu-thời-gian sự-kiện-thực (nạp nguồn) — không-thể-tương-lai. Bỏ nó khỏi invariant
  toàn-vẹn-thời-gian là OMISSION (spec không nhắc), KHÁC exemption-tường-minh của ca claim NOTE-012
  (spec nói rõ 'phạm vi cố ý hẹp'). Nên đây là under-enforce đáng fix. Driver cmd_source luôn set
  added=today → chỉ sửa tay mới tạo added tương lai → check bắt đúng tampering. Vì vẫn là MỞ RỘNG scope
  INV-05 ngoài spec text (khác DEC-029 vốn đã-trong-spec-text) → BẮT BUỘC qua CR (§12), không tự áp.
process_discipline: >
  Đây là lần đầu chuỗi robustness/enforcement đi TRỌN vòng §12 do AI khởi xướng: pending (turn trước) →
  approved (turn này, theo chỉ thị 'duyệt theo khuyến nghị' của spec-owner) → implement RED-first → changelog.
  Phân biệt rõ với DEC-029 (code-khớp-lại-spec, không cần CR) vs DEC-044 (mở-rộng-spec, cần CR).
evidence:
  - "RED-first: tests/phase07a_core/test_inv05_source_added.py (4 test: 2 âm added-tương-lai→E-SCHEMA, 2 dương→PASS). TRƯỚC fix: 2 âm đỏ (không bắt); SAU: xanh"
  - "validate.py: _check_source_added_not_future + wire _validate_topic (added=None bỏ qua Optional; today_local=None bỏ qua)"
  - "ran-test: full suite 362 passed (358 + 4); KHÔNG hồi quy nợ tất định (không test sources nào có added tương lai so với now)"
  - "ran-command: validator full scope vault thật PASS; CR-0004 moved pending→approved + changelog cập nhật"
verified: true
method: ran-test
status: active
reversible: "Gỡ _check_source_added_not_future + call (backward-compatible). Không nên."
```


## DEC-045 — P11 lớp THỰC THI migration (`executor.py`): chạy plan trong transaction-FULL + rollback (Q2)

```yaml
id: DEC-045
type: decision
date: 2026-07-04
title: "Dựng migrations/executor.py (execute_step/run_plan) — atomic migrate-or-rollback qua Transaction; chứng minh bằng schema-v2-giả-lập; RED-first (Q2=a)"
spec_ref: "spec §10.7/§10.3b (migration trong transaction-FULL, validate-at-target, rollback), INV-19; migrations/README.md hợp đồng bước; nối tiếp DEC-011"
summary: >
  Theo quyết định owner (Q2=a): dựng lớp THỰC THI migration mà DEC-011 từng hoãn. executor.py bám đúng
  hợp đồng README: _load_step (load vN_to_vM.py → migrate(vault)->list[Write]); execute_step (begin backup
  → stage → validate-at-target → occ_recheck → commit; FAIL→abort→vault giữ version N); run_plan (chuỗi
  bước tuần tự, DỪNG ở bước đầu FAIL). Toàn bộ qua Transaction engine hiện có (tái dùng atomicity NOTE-021).
proof_with_mock (trung thực, không bịa): >
  Cơ chế ORCHESTRATION được kiểm end-to-end bằng schema-v2-GIẢ-LẬP: mock step v1_to_v2 (bump schema_version
  1→2) sống TRONG tmp của test, KHÔNG để lại trong _system thật (đã verify migrations/ chỉ có executor.py+
  planner.py; không file giả). validate-at-target được INJECT (validate_staged_fn) vì validator-cho-version
  -đích THẬT chưa có. DEC-011 VẪN ĐÚNG cho phần transform + schema v2 THẬT: sẽ thêm v1_to_v2.py thật +
  golden test khi có version mới (qua change request) — không bịa bước giả trong _system.
cleanup (Q2 'dọn sạch'): >
  Sau khi làm OK: migrations/ chỉ giữ executor.py (infra thật) + planner.py; test dùng mock-trong-tmp;
  KHÔNG có schema v2 giả trong schemas/, KHÔNG có v1_to_v2.py giả trong migrations/. _system sạch.
design_choice: >
  validate_staged_fn là SEAM tường minh (mặc định = tx.validate_staged) — cho phép kiểm orchestration độc
  lập với validator-version-đích (chưa tồn tại), thay vì dựng validator v2 speculative (bịa). Đúng bản chất:
  phần RISKY & giá-trị (atomic migrate-or-rollback) được dựng+kiểm; phần chưa-có-cơ-sở (transform v2) hoãn.
evidence:
  - "RED-first: phase11/test_migration_executor.py (4 test: commit-on-pass + bump; rollback-on-fail giữ version cũ; run_plan stop-on-fail; happy single-step). TRƯỚC: ModuleNotFoundError; SAU: 4 passed"
  - "migrations/executor.py: _load_step/execute_step/run_plan; migrations/README.md cập nhật lớp thực thi"
  - "ran-command: migrations/ = {executor.py, planner.py} (không file giả); không stray temp"
  - "ran-test: full suite 366 passed (362 + 4)"
verified: true
method: ran-test
status: active
residual: "Bước migration THẬT (v1_to_v2.py) + validator-version-đích + golden v1→v2 PASS/FAIL→rollback: chờ schema v2 thật (DEC-011 vẫn hiệu lực cho phần này)."
reversible: "Xoá executor.py + test (backward-compatible; planner.py độc lập vẫn còn)."
```


## DEC-046 — `cmd_learn` escape free-text người-dùng vào front-matter YAML (title/objective/lesson_title có ':' '#' '"')

```yaml
id: DEC-046
type: decision
date: 2026-07-04
title: "_template_state thay free-text bằng scalar YAML-safe (json.dumps) ở front-matter; id/date raw; body markdown raw — chống crash yaml.ScannerError; RED-first (phát hiện từ walkthrough Q5)"
spec_ref: "spec §11A.1 (/learn tạo topic từ template); §10.4/§19 (robustness); nối chuỗi DEC-041→043 (biên khác: template substitution)"
summary: >
  BUG thật (lộ ra khi chạy Q5 walkthrough): /learn với objective='Hiểu đệ quy: hàm tự gọi...' (có ':') →
  cmd_learn CRASH yaml.ScannerError 'mapping values are not allowed here'. Gốc: _fill_template REPLACE THÔ
  giá trị free-text người-dùng (title/objective/lesson_title) vào FRONT-MATTER YAML của template → ký tự
  đặc biệt (':','#','\"', leading '-'...) phá cú pháp YAML → _template_state.yaml.safe_load raise (uncaught).
  Mục tiêu học / tiêu đề có ':' là RẤT thường → bug ảnh hưởng luồng /learn bình thường.
root_cause: >
  Cùng lớp bản chất DEC-041/042/043 (dữ liệu không-an-toàn đi vào YAML không qua escaping) nhưng ở biên
  KHÁC: template substitution (WRITE-path, đầu tạo topic). Fix ở tầng thay-chuỗi:
    - _template_state SPLIT front-matter/body TRƯỚC; front-matter: free-text (text_keys) → _yaml_scalar
      (json.dumps, ensure_ascii=False — JSON là tập con YAML flow nên quote/escape đúng ':','#','\"'); id/date
      giữ RAW (date phải giữ kiểu date qua yaml.safe_load, slug id an toàn); body markdown giữ RAW (không quote).
    - cmd_learn truyền text_keys={<<TOPIC_TITLE>>,<<LESSON_TITLE>>,<<OBJECTIVE>>} cho 3 call _template_state.
why_json_dumps: >
  JSON string là YAML flow double-quoted-scalar hợp lệ → yaml.safe_load parse đúng, giữ Unicode
  (ensure_ascii=False → tiếng Việt đọc được). Xử lý mọi ký tự đặc biệt bằng 1 cơ chế, không whack-a-mole.
  KHÔNG áp cho id/date vì quote sẽ biến date→str (pydantic strict reject) — phân biệt có chủ đích.
evidence:
  - "RED-first: test_session_learn.py::test_learn_special_chars_in_title_objective (title ':' + lesson_title '\"'/'#' + objective ':'). TRƯỚC fix: yaml.ScannerError crash; SAU: committed + round-trip đúng giá trị + validate_full_core PASS"
  - "session.py: _yaml_scalar + _fill_frontmatter + _template_state(text_keys=); cmd_learn truyền _TEXT_KEYS"
  - "ran-command (Q5 walkthrough): /learn objective có ':' → committed; trọn flow learn→author→done→cold-handoff PASS"
  - "ran-test: full suite 367 passed (366 + 1 RED)"
verified: true
method: ran-test
status: active
reversible: "Về _fill_template thô (tái crash ':' trong front-matter). Không nên."
```


## DEC-047 — `ai-learning-system/START_HERE.md`: mồi bootstrap cho AI mới (cross-AI handoff) + drift-guard

```yaml
id: DEC-047
type: decision
date: 2026-07-04
title: "Dựng START_HERE.md ở GỐC ai-learning-system (mệnh lệnh mồi cho AI/người mới) + drift-guard pointer + khối máy-đọc; RED-first"
spec_ref: "spec §0.3 (nói thật ranh giới), §11B (cửa vào), §16 (portability); PILOT_RUNBOOK [MANUAL] cross-AI handoff; đóng khoảng hở #3 (bootstrapping)"
summary: >
  Người dùng hỏi 'copy đi bất kỳ đâu + dùng bất kỳ AI nào để học được chưa'. Khoảng hở thật: KHÔNG có gì
  TỰ ĐỘNG bảo một AI mới nạp hiến pháp (prompts) trước khi hành động → phụ thuộc người-vận-hành-nhớ. Dựng
  START_HERE.md = mệnh lệnh mồi: trình tự bắt buộc (nạp system_prompt → README → decisions/index → dựng venv
  → status/resume → spec khi đổi-hệ), luật bất khả xâm phạm (pointer, không copy nội dung → chống drift),
  ranh giới Class A/B/C/D, điều-kiện-thực-tế (AI phải chạy-được-lệnh; venv rebuild; mồi là bước thủ công).
placement_decision: >
  Đặt ở GỐC ai-learning-system/ (KHÔNG trong _system/) — vì đó là thứ AI/người thấy ĐẦU TIÊN khi mở folder
  copy. Khác _system/README.md (bản đồ tooling, tầng trong). START_HERE = pointer-heavy, KHÔNG lặp nội dung
  system_prompt/README (tránh nguồn-sự-thật-thứ-2, đúng bài học Q7/NOTE-024).
honest_portable_unit (không bịa 'tự chứa 100%'): >
  Xác minh cấu trúc thực: PROMPT_LEARNING_SYSTEM.md (spec gốc) nằm ở thư mục CHA của ai-learning-system,
  KHÔNG bên trong. START_HERE nói CHÍNH XÁC: để HỌC → copy ai-learning-system/ là đủ (prompts/rules/validator
  /vault tự-chứa); để ĐỔI/AUDIT hệ → mang thêm ../PROMPT_LEARNING_SYSTEM.md. Không duplicate spec (chống drift).
drift_guard: >
  Bản chất START_HERE là POINTER — pointer mục (file đổi tên/di chuyển) làm AI mới CHẾT LẶNG. Thêm khối
  'bootstrap (máy đọc)' + test phase10/test_start_here_bootstrap.py: (1) START_HERE tồn tại+non-empty;
  (2) MỌI path trong khối phải tồn tại (relative gốc ai-learning-system); (3) read_order PHẢI gồm
  system_prompt.md (ép nạp hiến pháp). Pointer rot → test ĐỎ.
evidence:
  - "RED-first: test_start_here_bootstrap.py (3 test) — TRƯỚC: FileNotFoundError (START_HERE thiếu); SAU: 3 passed"
  - "ran-command: lệnh bước 5 (status/resume) chạy đúng như START_HERE mô tả (executable-true, self-describing next_action)"
  - "ran-test: full suite 370 passed (367 + 3); validator full PASS (START_HERE ở gốc, ngoài scope vault+_system, không ảnh hưởng)"
verified: true
method: ran-test
status: active
reversible: "Xoá START_HERE.md + test (mất mồi bootstrap; không ảnh hưởng runtime)."
```


## DEC-048 — `_system/selfcheck.py`: kiểm bản sao chạy-lần-đầu (stdlib-only, chưa cần venv)

```yaml
id: DEC-048
type: decision
date: 2026-07-04
title: "Dựng selfcheck.py — first-run self-check cho bản copy (kiểm file cốt lõi + chỉ dẫn bước tiếp); RED/teeth test"
spec_ref: "yêu cầu người dùng ('1 file test chạy lần đầu'); §16 portability; nối DEC-047 (START_HERE)"
summary: >
  Người dùng: 'copy folder ra, cho AI khác — tạo 1 file test chạy lần đầu'. Dựng _system/selfcheck.py:
  CHỈ thư viện chuẩn (không import gì trong _system) → chạy được trên bản sao TRẦN bằng Python hệ thống,
  CHƯA cần .venv. Kiểm: Python>=3.10, 14 file + 3 thư mục CỐT LÕI tồn tại, .venv có chưa; in báo cáo +
  BƯỚC TIẾP THEO (dựng venv → pytest → validate → status) + trỏ START_HERE. Exit 0=nguyên vẹn, 1=thiếu.
design: >
  Tách check(ai_root)->(ok,lines) THUẦN (test gọi được) + main() cho CLI. ai_root=parent của _system.
  KHÔNG chặn vì thiếu venv (venv phải dựng lại trên máy mới — không portable, đúng NOTE-001). Là 'cửa số 0'
  của START_HERE (thêm bước 0 + field first_run_check trong khối máy-đọc, drift-guard bao luôn).
evidence:
  - "ran-command: python selfcheck.py (Python HỆ THỐNG) → exit 0, báo 'NGUYÊN VẸN' + bước tiếp"
  - "test_selfcheck.py (3, teeth): repo thật ok=True; thư mục rỗng ok=False + [THIẾU]; REQUIRED khớp cấu trúc thực"
  - "START_HERE bước 0 + bootstrap.first_run_check; test_start_here_bootstrap bao path selfcheck"
  - "ran-test: full suite 373 passed (370 + 3); validator full PASS"
verified: true
method: ran-test
status: active
reversible: "Xoá selfcheck.py + test (không ảnh hưởng runtime)."
```


## DEC-049 — `_system/audit.py`: báo cáo CHỈ-ĐỌC 'folder đã được làm gì' (đánh giá vault người khác gửi)

```yaml
id: DEC-049
type: decision
date: 2026-07-04
title: "Dựng audit.py — verdict toàn-vẹn + topics/lessons/tiến-độ-ôn/gaps + lịch sử (transaction_log); read-only, robust; RED/teeth test"
spec_ref: "yêu cầu người dùng ('gửi folder xem ai đó đã làm gì'); read-only reporting trên validator+session+log"
summary: >
  Người dùng: 'lần sau tạo test đánh giá, tôi gửi folder xem ai đó đã làm gì'. Dựng _system/audit.py
  CHỈ-ĐỌC: (1) VERDICT toàn-vẹn = validate_full_semantic → PASS/FAIL + mã lỗi; (2) topics/lessons + status;
  (3) tiến độ ôn (mastery_state + due_date) + due_hôm_nay; (4) open_gaps; (5) LỊCH SỬ = parse
  transaction_log.md (tx nào, state, khi nào, ghi file gì, tombstone). CLI --vault [--at] [--json].
design: >
  Tái dùng validate + session (cmd_gaps/cmd_status read-only) + _load_raw, KHÔNG nhân đôi logic. Bọc mọi
  đọc bằng _safe() → vault HỎNG vẫn RA BÁO CÁO (integrity FAIL + phần đọc-được + đánh dấu 'unreadable'),
  KHÔNG crash (đúng triết lý robustness DEC-041→043). now bơm được (--at) để tất định; audit KHÔNG ghi gì.
evidence:
  - "ran-command: audit.py --vault ..\\learning_vault --at ... → in verdict PASS + docker/lesson-001 + lịch sử; vault SẠCH sau chạy (read-only, không side-effect)"
  - "test_audit.py (4, teeth): repo thật PASS+structure; corrupt score=99 → integrity FAIL không crash; sau /review → activity có tx; vault chưa log → activity=[]"
  - "README cập nhật (selfcheck+audit vào bản đồ tooling)"
  - "ran-test: full suite 377 passed (373 + 4); validator full PASS"
verified: true
method: ran-test
status: active
reversible: "Xoá audit.py + test (không ảnh hưởng runtime/dữ liệu)."
```


## DEC-050 — CR-0005 approved+áp: roadmap `## Lộ trình` trong topic.md (light-touch)

```yaml
id: DEC-050
type: decision
date: 2026-07-04
title: "Implement CR-0005: /learn tạo topic.md (## Lộ trình + ## Knowledge Map); AI-authored guidance, KHÔNG INV cứng; RED-first"
spec_ref: "CR-0005 (approved); yêu cầu người dùng (lộ trình điểm cần học); §12"
summary: >
  Owner duyệt ('Duyệt') → áp CR-0005 light-touch. Thêm templates/topic_template/topic.template.md
  (section '## Lộ trình' bullet [todo|doing|done] + '## Knowledge Map' rỗng). cmd_learn ghi topic.md
  (body markdown → _template_text raw subst, KHÔNG cần escape YAML vì không front-matter). Sync
  rules/teaching_rules.md (AI lập/cập nhật Lộ trình khi dạy; không claim ở Lộ trình — INV-23; Knowledge
  Map chỉ confirmed — INV-26).
design_choice: >
  KHÔNG nâng Lộ trình thành INV cứng (v1): nó là kế-hoạch-MỀM (điểm chưa thành lesson), ép khớp lessons sẽ
  sinh lỗi giả + coupling. Giữ là guidance content (như Knowledge Map là content, không phải state machine).
  topic.md giờ được /learn LUÔN tạo (trước: optional, chỉ khi có claim).
evidence:
  - "RED-first: test_session_learn.py::test_learn_creates_topic_md_with_roadmap (topic.md có '## Lộ trình' + validate_full_semantic PASS). TRƯỚC: topic.md không tồn tại; SAU: pass"
  - "session.py cmd_learn: topic_md=_template_text(...topic.template.md); TX.Write topic.md"
  - "ran-test: full suite 378 passed (377 + 1); validator full PASS; INV-23/26 không kích bởi topic.md mới"
  - "CR-0005 pending→approved + changelog"
verified: true
method: ran-test
status: active
reversible: "Gỡ topic.template.md + write topic.md khỏi cmd_learn (topic.md trở lại optional). Không đổi schema."
```

## DEC-051 — CR-0006 approved+áp: buổi ôn ghi vào `lesson.md ## Sessions` (KHÔNG artifact mới)

```yaml
id: DEC-051
type: decision
date: 2026-07-04
title: "Implement CR-0006: sync review_rules — buổi ôn = block '### Session — ôn tập' trong ## Sessions; KHÔNG tạo file/buổi"
spec_ref: "CR-0006 (approved); spec §14 (Sessions); INV-25; §12"
summary: >
  Owner duyệt → áp theo khuyến nghị: KHÔNG tạo file .md riêng mỗi buổi ôn (trùng lesson.md ## Sessions §14,
  xung đột INV-25, phá giả định /resume/status). Chỉ sync rules/review_rules.md mục 'Ghi buổi ôn tập':
  buổi ôn = thêm block '### Session <ngày> — ôn tập' vào ## Sessions; hỏi một-câu/lượt. KHÔNG code mới,
  KHÔNG artifact mới — cơ chế ## Sessions đã có + validate (AST §844).
rationale (fix bản chất): >
  Nhu cầu người dùng ĐÃ được đáp ứng bởi cơ chế hiện có. Thêm file/buổi = nguồn-sự-thật-thứ-2 (anti-drift).
  Chọn tái-dùng = đúng bản chất. Alias '/ôn'=/review HOÃN (tùy chọn UX; đụng registry → CR riêng nếu cần).
evidence:
  - "read-source: spec §14 dòng 1026/1142/1383 (## Sessions là nơi ghi buổi + /resume đọc buổi gần nhất)"
  - "rules/review_rules.md: mục 'Ghi buổi ôn tập' (CR-0006)"
  - "ran-test: full suite 378 passed (drift-guard review_rules không vỡ — prose thêm, không đụng khối grade_to_rating máy-đọc)"
  - "CR-0006 pending→approved + changelog"
verified: true
method: ran-test
status: active
reversible: "Gỡ mục review_rules (process-only; không code)."
```

## DEC-052 — `HUONG_DAN.md` (hướng dẫn NGƯỜI HỌC) + drift-guard lệnh↔registry

```yaml
id: DEC-052
type: decision
date: 2026-07-05
title: "Tạo HUONG_DAN.md ở gốc ai-learning-system (hướng dẫn người học tiếng Việt, lệnh giữ English) + test drift-guard 'commands (máy đọc)' ⊆ commands.md; pointer vào START_HERE + README"
spec_ref: "none (yêu cầu người dùng: 'cứ để tiếng anh rồi có file hướng dẫn'); dựa START_HERE (DEC-047) phân vai AI vs người học"
summary: >
  Người dùng muốn GIỮ lệnh tiếng Anh (KHÔNG thêm alias tiếng Việt vào registry) nhưng có file hướng dẫn
  dùng hằng ngày. AI tự quyết: (1) tạo HUONG_DAN.md ở GỐC ai-learning-system/ (cạnh START_HERE.md) —
  đối tượng là NGƯỜI HỌC (con người), tiếng Việt, bảng 'muốn gì → nói/gõ gì → điều xảy ra', nơi lưu dữ
  liệu, ranh giới Class A/D nói thật; lệnh liệt kê nguyên English khớp registry. (2) Khối 'commands (máy đọc)'
  liệt kê 19 lệnh + test drift-guard bắt buộc mọi lệnh trong khối phải TỒN TẠI trong commands.md (registry
  = nguồn sự thật) → nếu ai đổi tên/bịa lệnh trong hướng dẫn, người học gõ sẽ hỏng ⇒ test đỏ. (3) Pointer
  một chiều: START_HERE (mồi AI) thêm dòng 'người học đọc HUONG_DAN.md'; _system/README bản-đồ thêm dòng
  HUONG_DAN. KHÔNG đưa HUONG_DAN vào selfcheck.py REQUIRED (nó user-facing, không phải core vận hành —
  tránh coupling; đã có drift-guard test riêng bảo vệ).
rationale (chọn vì): >
  (1) Tách đối tượng: START_HERE mồi cho AI-vận-hành, HUONG_DAN cho người-học — không trộn vai, mỗi file
  một mục đích (đúng phân vai DEC-047). (2) KHÔNG alias tiếng Việt = tôn trọng yêu cầu + tránh sửa registry
  (đổi registry phải qua CR §12; ở đây không cần vì chỉ thêm tài liệu, không thêm lệnh). (3) Drift-guard
  '⊆ registry' thay vì '== registry' vì hướng dẫn có quyền không liệt kê hết lệnh hiếm, nhưng KHÔNG được
  nhắc lệnh không tồn tại — bất biến đúng là 'mọi lệnh nêu phải chạy được'. (4) KHÔNG coupling vào selfcheck
  vì HUONG_DAN không phải điều kiện để hệ VẬN HÀNH (khác 14 file core); ép vào sẽ khiến bản copy thiếu
  file user-facing bị báo 'hỏng cấu trúc' sai bản chất.
alternatives:
  - "Thêm alias /ôn /học... vào registry → đổi commands.md + router + CR §12; người dùng đã nói KHÔNG. Loại."
  - "Nhét hướng dẫn người học vào START_HERE → trộn hai đối tượng, file dài rối. Loại."
  - "Không drift-guard (prose thuần) → hướng dẫn trôi khỏi registry, người học gõ lệnh chết. Loại."
  - "Đưa HUONG_DAN vào selfcheck REQUIRED → coupling sai tầng (user-facing vs core). Loại."
evidence:
  - "ai-learning-system/HUONG_DAN.md (bảng dùng-hằng-ngày + nơi lưu + Class A/D + khối 'commands (máy đọc)' 19 lệnh)"
  - "validator/tests/phase10/test_huong_dan.py: 3 test (tồn tại+non-empty; mọi lệnh ⊆ commands.md; có /learn /review /done /status)"
  - "ran-test: full suite 381 passed (378 + 3 mới); KHÔNG hồi quy"
  - "ran-command: validate.py --level full --scope full --at 2026-07-04T12:00:00+07:00 → pass:true, errors:[]"
  - "read-source: START_HERE.md thêm dòng phân vai; _system/README.md bảng bản-đồ thêm dòng ../HUONG_DAN.md"
verified: true
method: ran-test
status: active
reversible: "Xoá HUONG_DAN.md + test_huong_dan.py + 2 dòng pointer; validator/lõi không phụ thuộc."
```

## DEC-053 — `HANDOFF_TEST.md`: bộ test cross-AI handoff (prompt cho AI khác + rubric đánh giá)

```yaml
id: DEC-053
type: decision
date: 2026-07-05
title: "Tạo HANDOFF_TEST.md ở gốc ai-learning-system — prompt tự-chứa để AI KHÁC tiếp quản + rubric R1..R7 người đánh giá dùng; đóng khoảng trống 'portability thật (AI khác vận hành)' vs 'portability mức-file'"
spec_ref: "none (yêu cầu người dùng: copy ra nơi khác, cho AI khác thực hiện, rồi tôi đánh giá); dựa START_HERE (DEC-047) + selfcheck (DEC-048) + audit (DEC-049)"
summary: >
  Người dùng muốn kiểm chứng THẬT tuyên bố portability: copy thư mục sang chỗ khác + một AI KHÁC vận hành,
  rồi gửi folder về cho tôi đánh giá. Tôi tạo HANDOFF_TEST.md (đặt trong ai-learning-system/ để ĐI THEO
  bản copy). Thiết kế: (1) ép bootstrap đúng (selfcheck→hiến pháp→dựng venv→pytest→validate) trước khi
  làm gì; (2) khai báo điều-kiện-tiên-quyết 'AI phải chạy-được-lệnh' (chat-only → test thất bại điều kiện,
  vì bảo đảm đến từ chạy validator thật — nói thẳng giới hạn §0.3); (3) chia 2 phần: PHẦN A cơ chế
  (KHÁCH QUAN, máy chấm: learn→validate→status/schedule→review→transaction_log, validator PASS mỗi bước ghi)
  + PHẦN B dạy thật (Class D, cần người học thật); (4) self-report mẫu HANDOFF_RESULT.md; (5) RUBRIC R1..R7
  CÔNG KHAI ngay trong prompt → test falsifiable, công bằng. Verify chữ ký CLI thật (đọc parser session.py/
  validate.py/audit.py) trước khi viết lệnh vào prompt → KHÔNG bịa lệnh (review cần --lesson --item --grade;
  mọi lệnh qua .venv\\Scripts\\python validator\\<script>.py từ _system/).
rationale (chọn vì): >
  (1) Portability tôi mới verify được MỨC FILE (validator PASS ở path khác, NOTE-028) — CHƯA verify 'một AI
  khác thật sự tiếp quản được'. Đây là cách duy nhất đóng khoảng trống đó, và người dùng chủ động làm.
  (2) Tách A/B vì Class D (hiểu thật/chất lượng dạy) BẢN CHẤT cần con người — không nhét vào phần máy-chấm
  được; nếu trộn sẽ tạo ảo giác 'test khách quan cả teaching'. A khách quan tuyệt đối (validator+transaction_log),
  B là điểm cộng định-tính. (3) Rubric công khai trong chính prompt = test không thể 'dời cột gôn' sau khi biết
  kết quả; và AI-đối-tượng biết trước sẽ bị chấm gì → tự-kỷ-luật. (4) Đặt file TRONG thư mục để tự đi theo copy
  (không cần người dùng nhớ mang riêng) — cùng lớp user-facing với START_HERE/HUONG_DAN, ngoài _system/ nên
  KHÔNG kích INV-18, KHÔNG ảnh hưởng validator/suite.
alternatives:
  - "Chỉ test cơ chế (bỏ Phần B) → không chạm mục đích học thật. Loại (giữ B là điểm cộng)."
  - "Chỉ test dạy (bỏ Phần A) → không có phần khách quan máy chấm → kết luận cãi nhau được. Loại."
  - "Không công khai rubric → người đánh giá tự chấm chủ quan, test không falsifiable. Loại."
  - "Đặt prompt ngoài thư mục (ở workspace cha) → người dùng phải nhớ mang kèm; dễ rớt. Loại (đặt trong)."
evidence:
  - "ai-learning-system/HANDOFF_TEST.md (7 mục: bối cảnh + điều kiện + bootstrap + luật + nhiệm vụ A/B + bằng chứng + self-report + rubric R1..R7)"
  - "read-source: verify chữ ký CLI thật — session.py parser (learn/status/schedule/review --lesson --item --grade/done --lesson), validate.py (--level/--scope/--at), audit.py (--vault), selfcheck.py (no-arg) — trước khi viết lệnh vào prompt"
  - "Không ảnh hưởng lõi: file ở gốc ai-learning-system/ (ngoài vault + _system) → validator không quét; suite 381 không tham chiếu"
verified: true
method: read-source
status: active
todo: "Khi người dùng gửi folder về: chạy R1..R7 độc lập → kết luận ĐẠT/điều-tra-gốc; ghi NOTE kết quả handoff thật."
reversible: "Xoá HANDOFF_TEST.md (+ HANDOFF_RESULT.md nếu có); không phụ thuộc lõi."
```

## DEC-054 — Tách demo khỏi vault ship: fixture riêng + `learning_vault` khởi đầu RỖNG

```yaml
id: DEC-054
type: decision
date: 2026-07-05
title: "Chuyển demo docker (vốn nằm trong learning_vault) thành fixture test riêng (validator/tests/fixtures/demo_vault); ship learning_vault RỖNG (topics/ trống + con trỏ null) để người dùng bắt đầu trắng"
spec_ref: "none (phát hiện từ câu hỏi người dùng: 'chưa nói học gì mà đã có lesson?'); INV-18 (_SYSTEM_SKIP_DIRS 'validator'); selfcheck REQUIRED_DIRS"
summary: >
  Người dùng bắt đúng: learning_vault ship kèm topic 'docker'/lesson-001 — người học mới tưởng đó là bài
  mình đã học. Điều tra (read-source + grep): docker là DỮ LIỆU DEMO tạo lúc build (created 2026-06-30),
  ĐỒNG THỜI là fixture mà 29 file test copytree(→tmp) để kiểm review/done/forget/status/schedule/portability;
  chính test tự gọi nó '# demo'. Gốc rễ: fixture-test và dữ-liệu-người-dùng bị TRỘN làm một (coupling smell).
  Fix TẬN GỐC (Phương án A, người dùng chọn): (1) copy nguyên demo → _system/validator/tests/fixtures/demo_vault/
  (đặt DƯỚI validator/ → INV-18 _SYSTEM_SKIP_DIRS bỏ qua, không kích E-MIX-DATA — verify); (2) trỏ 29 file test
  'ROOT.parent/learning_vault' → 'ROOT/validator/tests/fixtures/demo_vault' (fixture y hệt → suite giữ nguyên
  hành vi); (3) dọn learning_vault ship: xoá topics/docker, vault_state current_topic/current_lesson=null,
  giữ topics/ + thêm .gitkeep (để thư mục sống sót khi zip/copy — nếu mất, selfcheck báo THIẾU); (4) RED-first
  test_shipped_vault_clean.py (validate full PASS + topics/ rỗng + con trỏ null) — thấy 2 RED (docker còn) rồi
  dọn → 3 GREEN.
rationale (chọn vì): >
  (1) Fixture test KHÔNG PHẢI dữ liệu người dùng — trộn chung gây nhầm lẫn UX (đúng thứ người dùng vừa gặp)
  + coupling (đổi demo có thể vỡ test). Tách ra: người dùng mới bắt đầu SẠCH (đúng kỳ vọng sản phẩm thương mại),
  test có fixture bất biến riêng. (2) Đặt fixture dưới validator/ tận dụng skip-dir sẵn có (DEC-002) → KHÔNG cần
  nới lỏng INV-18 hay thêm skip mới (không giảm an toàn). (3) Repoint 29 file bằng 1 phép thay chuỗi đồng nhất
  (ROOT=_system ở mọi file) → cơ học, rủi ro thấp; checkpoint suite 381→384 xanh chứng minh fixture tương đương.
  (4) .gitkeep vì vault rỗng phải tồn tại thư mục topics/ (selfcheck + validator quét) — dir rỗng dễ rớt khi nén.
observations:
  - "status trên vault rỗng: 'topic=None | gợi ý: /learn' — UX đúng cho người mới (đã chạy CLI thật)."
  - "resume trên vault rỗng: committed=true nhưng no-op (không lesson → open_session giữ null); vault vẫn SẠCH byte-level (không .tx, không transaction_log). Không phải bug ảnh hưởng cleanliness; ghi nhận."
alternatives:
  - "Giữ docker + dán nhãn 'DEMO' (Phương án B) → người dùng vẫn thấy bài lạ trong vault mình. Loại (không sạch)."
  - "Thêm learning_vault vào _SYSTEM... không liên quan; hoặc nới INV-18 cho fixture → giảm an toàn. Loại (skip-dir validator đã đủ)."
  - "Xoá demo hẳn (không giữ fixture) → mất fixture của 29 test → phải viết lại fixture. Loại (lãng phí + mất coverage lịch sử)."
evidence:
  - "fixture: _system/validator/tests/fixtures/demo_vault/ (docker/lesson-001 nguyên vẹn) + README_FIXTURE.md"
  - "repoint: 29 file test (ROOT.parent/learning_vault → ROOT/validator/tests/fixtures/demo_vault) — grep xác nhận không còn tham chiếu cũ"
  - "ship sạch: learning_vault/{vault_state.md (current_topic/current_lesson=null), topics/.gitkeep}; docker đã xoá"
  - "ran-test RED-first: test_shipped_vault_clean.py 2 fail (docker còn) → dọn → 3 pass"
  - "ran-test: full suite 381→384 passed (repoint checkpoint 381 + 3 test mới); KHÔNG hồi quy"
  - "ran-command: validate.py --scope full trên vault ship SẠCH → pass:true, errors:[]; selfcheck → NGUYÊN VẸN"
  - "read-source: INV-18 _SYSTEM_SKIP_DIRS chứa 'validator' → fixture dưới validator/ không bị quét E-MIX-DATA"
verified: true
method: ran-test
status: active
note: "venv đã phải DỰNG LẠI giữa chừng (biến mất khỏi disk — môi trường reset/di chuyển); rebuild theo START_HERE bước 4, pytest xanh lại → xác nhận quy trình bootstrap của START_HERE/selfcheck hoạt động thật."
reversible: "Copy fixture ngược về learning_vault + revert 29 repoint + đặt lại con trỏ; nhưng sẽ tái nhầm lẫn UX."
```

## DEC-055 — Tính năng "curriculum-driven-learning": làm SPEC-first (requirements+design+tasks), CHƯA code

```yaml
id: DEC-055
type: decision
date: 2026-07-05
title: "Dựng đặc tả đầy đủ (requirements→design→tasks) cho tính năng giáo trình nhiều bài + reference + exam TRƯỚC khi code; chốt các quyết định thiết kế mấu chốt"
spec_ref: "none (yêu cầu người dùng: học nhiều bài theo giáo trình từ reference + exam chấm bài); §12 (change-request); phương pháp design-first của owner"
summary: >
  Người dùng muốn một topic có GIÁO TRÌNH nhiều bài (khắc phục giới hạn /learn chỉ tạo lesson-001), dựng
  từ tài liệu trong reference/ (hoặc nguồn ngoài), kiểm chặt, tự nhảy bài khi qua cổng, và có exam/ để nộp
  bài thực hành. Vì đụng schema+registry+spec, theo §12 + phương pháp design-first, AI dựng ĐẶC TẢ đầy đủ
  tại .kiro/specs/curriculum-driven-learning/ (requirements.md 11 nhóm EARS; design.md; tasks.md 11 task/9 wave)
  thay vì code nóng. Owner đã DUYỆT design (2026-07-05). Triển khai CHỜ theo tasks (RED-first).
key_design_decisions:
  - "Reference ON-DEMAND, KHÔNG clone bulk 5 repo (xem TRD-006): đăng ký nguồn vào sources.md + kéo lát cắt markdown liên quan vào learning_vault/topics/<topic>/reference/ (chỉ .md)."
  - "exam/ đặt NGOÀI learning_vault (ở gốc ai-learning-system): bài nộp có thể là CODE → trong vault sẽ phá INV-17. Bản ghi chấm exam_results.md (KHÔNG chứa code) ở TRONG vault, trỏ bài nộp bằng đường dẫn tương đối (INV-16)."
  - "Schema mới curriculum + exam_results: file schemas/*.schema.md + model pydantic + drift-guard (đồng nhất DEC-008)."
  - "topic_state.lessons[] VẪN là nguồn sự thật index bài (INV-25); curriculum.points[].lesson_id chỉ là tham chiếu được validate khớp (E-CURR-LESSON-LINK) — tránh nguồn-thứ-2."
  - "9 mã lỗi mới (E-CURR-* + E-EXAM-REF-BROKEN), mỗi mã RED-first. 'Đủ sâu/rộng/chính xác nội dung' KHÔNG có mã (Class D, cố ý)."
  - "Auto-advance móc vào cmd_done (khi qua learned_gate) trong CÙNG transaction; KHÔNG tạo cổng mới."
  - "Kế hoạch CR: CR-0007 (schema) → CR-0008 (5 lệnh) → CR-0009 (spec §3/§11A/§14). Mỗi CR chờ owner Duyệt."
rationale (vì sao spec-first, không code ngay): >
  Tính năng lớn, đa-chạm (schema+lệnh+spec+validator+lesson lifecycle). Code nóng sẽ (1) vi phạm §12,
  (2) rủi ro thiết kế sai phải làm lại. Design-first + owner duyệt = đúng phương pháp owner yêu cầu, giảm
  rework, giữ kỷ luật. Mọi quyết định thiết kế đều neo vào bất biến hiện có (INV-16/17/18/25/03/07) —
  kiểm-chứng-được, không bịa.
evidence:
  - ".kiro/specs/curriculum-driven-learning/{requirements.md, design.md, tasks.md} — diagnostics sạch (Kiro Spec Format)"
  - "design.md: mục Architecture (vị trí file INV), Data Models (2 schema), Error Handling (9 mã), Correctness Properties (7), Testing Strategy, Kế hoạch CR"
  - "read-source: verify giới hạn cmd_learn chỉ tạo lesson-001 (DEC-014); INV-18 skip 'validator'; sources.md status raw sẵn có"
verified: true
method: read-source
status: active
todo: "Triển khai theo tasks.md: T1 soạn CR pending → owner Duyệt → T2..T11 RED-first + validator PASS. Ghi DEC-056.. khi code."
reversible: "Xoá thư mục spec; chưa đụng code sản phẩm nên không ảnh hưởng hệ."
```

---

## DEC-056 — `/ask` GIỮ ghi vào `lesson.md ## Hỏi phụ` (KHÔNG tách file riêng); đề xuất tách file HOÃN

```yaml
id: DEC-056
type: decision
date: 2026-07-05
title: "Giữ nguyên hành vi /ask (ghi ## Hỏi phụ trong lesson.md) theo quyết định người dùng; hoãn phương án tách file riêng"
spec_ref: "spec dòng 163 ('lesson.md ... có section ## Hỏi phụ ... không tách file riêng'), dòng 1102; DEC-024"
summary: >
  Người dùng ban đầu muốn câu hỏi phụ ra FILE RIÊNG (thấy '## Hỏi phụ - (chưa có)' in sẵn là 'rác'). AI
  truy spec: dòng 163 CỐ Ý quy định 'không tách file riêng' + dòng 1102 'không làm rác bài giảng' — đổi =
  đổi spec, phải qua CR §12. AI nêu 2 phương án (tách file lười / bỏ placeholder rỗng). Người dùng chốt
  'gõ /ask là được' → GIỮ cơ chế hiện tại, KHÔNG đổi. Nguyên nhân 'rác' chủ yếu là dòng '- (chưa có)' in sẵn.
rationale: >
  Tôn trọng quyết định owner + tránh đổi spec không cần thiết. Đổi hành vi /ask khi chưa cấp thiết = rủi ro
  + tốn CR. Ghi lại để nếu sau muốn tách file (hoặc bỏ placeholder) thì đi trọn §12, không sửa nóng.
evidence:
  - "read-source: session.py cmd_ask + _append_hoiphu (ghi ## Hỏi phụ); spec dòng 163/1102"
  - "transcript phiên: người dùng 'ok vậy gõ /ask là được'"
verified: true
method: read-source
status: active
reversible: "Nếu owner muốn tách file: mở CR đổi §14A + cmd_ask + template + tests (đã phác trong phiên)."
```

## DEC-057 — CR-0007 approved+áp: schema `curriculum` + `exam_results` (Task 2, RED-first)

```yaml
id: DEC-057
type: decision
date: 2026-07-05
title: "Implement Task 2 (curriculum-driven-learning): model + schemas/ + drift-guard cho curriculum & exam_results; +2 tên vào INV-18"
spec_ref: "CR-0007 (approved); spec curriculum-driven-learning R3/R9/R11; DEC-055 (design), DEC-008 (drift-guard schema)"
summary: >
  Owner duyệt CR-0007 (theo khuyến nghị từng-bước). Áp Task 2 RED-first: (1) tạo schemas/curriculum.schema.md
  + schemas/exam_results.schema.md (khối schema_fields máy-đọc) + mở rộng test_schemas_consistency
  (MODEL_BY_SCHEMA += 2) → chạy ĐỎ (M.Curriculum/ExamResults chưa có); (2) thêm model pydantic Curriculum,
  CurriculumPoint, ExamResults, ExamResult vào models.py → XANH; (3) thêm curriculum.md/exam_results.md vào
  INV-18 _SYSTEM_DATA_NAMES (chống dữ liệu học lạc vào _system). 386 passed; validator full PASS.
key_decisions:
  - "Model chỉ giữ ràng buộc CẤU TRÚC (id pattern ^cp-*/^ex-*, order>=1, status Literal, schema literal, updated>=created, submission_id duy nhất). CỐ Ý KHÔNG nhét kiểm NGỮ NGHĨA (dup id/order-hoán-vị/objective-rỗng/pointer/ref-broken/lesson-link) vào model → để Curriculum_Validator (validate.py, Task 3) phát mã E-CURR-* PHÂN BIỆT (khác TopicState nhét dup-id vào model→E-SCHEMA). Lý do: design R10.1 đòi mỗi loại vi phạm một mã xác định."
  - "current_point: str REQUIRED (giáo trình luôn có con trỏ); tính hợp lệ (trỏ point tồn tại) để E-CURR-POINTER lo."
  - "verdict: str required (bản ghi chấm phải có nhận xét — Class D)."
evidence:
  - "ran-test RED: test_schemas_consistency ERROR (AttributeError M.Curriculum) trước khi thêm model"
  - "ran-test GREEN: test_schemas_consistency 8 passed (7 parametrize + present)"
  - "ran-test: full suite 386 passed (384 + 2 schema mới); ran-command: validate --scope full pass:true"
  - "read-source: models.py _Strict (strict+extra=forbid+populate_by_name); alias 'schema'; date/Literal/Optional theo mẫu hiện có"
  - "CR-0007 pending→approved + changelog (2026-07-05)"
verified: true
method: ran-test
status: active
todo: "Task 3: _check_curriculum trong validate.py — 9 mã E-CURR-*/E-EXAM-* RED-first (cần quyết CR: mở rộng scope CR-0007 hay CR riêng cho enforcement — nêu khi làm)."
reversible: "Gỡ 2 model + 2 schema doc + revert MODEL_BY_SCHEMA + bỏ 2 tên INV-18; validator lõi không phụ thuộc."
```

## DEC-058 — Task 3.1 Curriculum_Validator: 3 mã ngữ nghĩa đầu (RED-first) + tinh chỉnh bỏ 2 mã thừa

```yaml
id: DEC-058
type: decision
date: 2026-07-05
title: "Hiện thực _check_curriculum (E-CURR-DUP-ID/ORDER/EMPTY-OBJECTIVE) + wire vào _validate_topic + dispatch _SCHEMA_MODELS; RED-first. Tinh chỉnh design: bỏ E-CURR-SCHEMA/E-CURR-BADSTATUS (thừa)"
spec_ref: "spec curriculum-driven-learning R3/R5/R10; design.md Error Handling; DEC-055/057; tiền lệ DEC-034 (mã lỗi validator = enforcement, RED-first + sync validation_rules, không cần CR riêng)"
summary: >
  Task 3 (Curriculum_Validator). Áp increment 3.1: (1) thêm 'curriculum'/'exam_results' vào _SCHEMA_MODELS
  (trước đó THIẾU → curriculum.md bị validator BỎ QUA hoàn toàn — under-enforce); (2) _check_curriculum phát
  3 mã NGỮ NGHĨA model không bắt: E-CURR-DUP-ID (id trùng), E-CURR-ORDER (order không hoán vị 1..N),
  E-CURR-EMPTY-OBJECTIVE (objective rỗng sau strip); (3) wire cuối _validate_topic (curriculum.md TÙY CHỌN);
  (4) sync validation_rules.md (bảng + khối error_codes) để test_doc_codes_equal_emitted khớp 2 chiều.
design_refinement (bỏ 2 mã thừa so với design 9-mã): >
  Đọc models.py thật: M.Curriculum strict + Literal đã bắt sai-schema (→ E-SCHEMA) và status-ngoài-tập
  (→ E-SCHEMA). Nên E-CURR-SCHEMA và E-CURR-BADSTATUS TRÙNG E-SCHEMA → tạo chúng vi phạm chính R10.1
  ('mỗi loại vi phạm MỘT mã phân biệt') + ceremony. Chốt: 9 mã design → 7 mã ngữ nghĩa THẬT
  (DUP-ID, ORDER, EMPTY-OBJECTIVE, POINTER, LESSON-LINK, REF-BROKEN, EXAM-REF-BROKEN). Cấu trúc → E-SCHEMA.
scope_gating (vì sao Task 3 không cần CR mới): >
  CR-0007 phủ schema. Enforcement (thêm mã E-CURR-* vào validate.py) theo tiền lệ DEC-034 (E-IO-ENCODING):
  mã lỗi validator là enforcement của đảm bảo Class-A ĐÃ có trong design duyệt, RED-first + sync
  validation_rules drift-guard, KHÔNG cần CR registry/schema. Spec-file formalize ở CR-0009 (Task 11).
evidence:
  - "ran-test RED: test_curriculum_validator.py 5 failed (AttributeError _check_curriculum) trước khi hiện thực"
  - "ran-test GREEN: test_curriculum_validator 5 passed + test_validation_rules_codes 2 passed (coverage 2 chiều khớp)"
  - "ran-test: full suite 391 passed (386 + 5 mới); ran-command: validate --scope full pass:true, errors:[]"
  - "read-source: _validate_topic (wire sau _check_views), _parse_state_model (dispatch _SCHEMA_MODELS), _emitted scanner (validate/transaction/session)"
verified: true
method: ran-test
status: active
todo: "Task 3.2/3.3: E-CURR-POINTER (current_point dangling, INV-03) + E-CURR-LESSON-LINK (INV-25) + E-CURR-REF-BROKEN (source_refs); Task 8: E-EXAM-REF-BROKEN. Mỗi mã RED-first + sync validation_rules."
reversible: "Gỡ _check_curriculum + call + 2 dòng _SCHEMA_MODELS + 3 mã validation_rules + test; validator lõi không phụ thuộc."
```

## DEC-059 — Task 3.2 Curriculum_Validator: E-CURR-POINTER (INV-03) + E-CURR-LESSON-LINK (INV-25)

```yaml
id: DEC-059
type: decision
date: 2026-07-05
title: "Thêm 2 mã ngữ nghĩa curriculum: current_point dangling (E-CURR-POINTER) + lesson_id trỏ lesson thật (E-CURR-LESSON-LINK); RED-first"
spec_ref: "spec curriculum-driven-learning R7.5/R6.4/R6.5/R10.3; design Property 2 & 3; DEC-058 (increment trước); INV-03/INV-25"
summary: >
  Tiếp Task 3 (increment 3.2). E-CURR-POINTER: current_point PHẢI trỏ một point tồn tại (cùng diễn giải
  INV-03 'mọi tham chiếu' như DEC-031/037 cho open_session/current_topic). E-CURR-LESSON-LINK: mỗi
  point.lesson_id (nếu != null) phải nằm trong all_lesson_ids (lesson THẬT trên đĩa) — giữ INV-25, và
  KHẲNG ĐỊNH lại nguồn sự thật index = topic_state.lessons[], curriculum.lesson_id chỉ là tham chiếu.
  RED-first: 2 test đỏ (POINTER dangling + LESSON-LINK broken) + 2 test ca-hợp-lệ; implement → xanh.
evidence:
  - "ran-test RED: test_pointer_dangling + test_lesson_link_broken FAIL trước khi thêm check (2 failed, 7 passed)"
  - "ran-test GREEN: test_curriculum_validator 9 passed + test_validation_rules_codes 2 passed"
  - "ran-test: full suite 395 passed (391 + 4 test 3.2); ran-command: validate --scope full pass:true"
  - "read-source: _check_curriculum dùng all_lesson_ids (đã truyền từ _validate_topic); ids từ points"
  - "sync validation_rules.md: +E-CURR-POINTER +E-CURR-LESSON-LINK (bảng + error_codes, coverage 2 chiều)"
verified: true
method: ran-test
status: active
todo: "Task 3.3: E-CURR-REF-BROKEN (source_refs trỏ file reference/ tồn tại) — cần dựng reference/ (Task 4). Task 8: E-EXAM-REF-BROKEN. Còn 5/7 → nay 5 mã xong (DUP-ID/ORDER/EMPTY-OBJECTIVE/POINTER/LESSON-LINK), còn 2 (REF-BROKEN, EXAM-REF-BROKEN)."
reversible: "Gỡ 2 check trong _check_curriculum + 2 mã validation_rules + 4 test; validator lõi không phụ thuộc."
```

## DEC-060 — Task 3.3 Curriculum_Validator: E-CURR-REF-BROKEN → hoàn tất 6/6 mã curriculum

```yaml
id: DEC-060
type: decision
date: 2026-07-05
title: "Thêm E-CURR-REF-BROKEN (source_refs trỏ file reference/ tồn tại); RED-first. Task 3 (Curriculum_Validator) hoàn tất 6/6 mã curriculum"
spec_ref: "spec curriculum-driven-learning R1.4/R5.6; design Property (REF); DEC-058/059; INV-16 (abspath đã do E-PORT-ABSPATH)"
summary: >
  Increment 3.3: E-CURR-REF-BROKEN — mỗi point.source_refs[i] phải trỏ file TỒN TẠI (resolve tương đối
  topic_dir, ví dụ 'reference/<slug>.md'). Đường dẫn tuyệt đối KHÔNG cần xử lý ở đây vì đã bị E-PORT-ABSPATH
  chặn ở _parse_state_model (không trùng lặp enforcement). RED-first: test_ref_broken đỏ + test_ref_ok (tạo
  file thật) xanh; implement → xanh.
scope_note: >
  Vị trí reference/: chốt theo design Architecture = topics/<topic>/reference/ → source_ref resolve tương đối
  TOPIC_DIR (không phải vault). Ví dụ schema cũ ('reference/docker/...') là loose; chuẩn hoá: tương đối topic_dir.
milestone: "Task 3 (Curriculum_Validator) XONG 6/6 mã curriculum: DUP-ID, ORDER, EMPTY-OBJECTIVE, POINTER, LESSON-LINK, REF-BROKEN. Còn E-EXAM-REF-BROKEN thuộc Task 8 (exam)."
evidence:
  - "ran-test RED: test_ref_broken FAIL (1 failed, 10 passed) trước khi thêm check"
  - "ran-test GREEN: test_curriculum_validator 11 passed + test_validation_rules_codes 2 passed (coverage 2 chiều)"
  - "ran-test: full suite 397 passed (395 + 2); ran-command: validate --scope full pass:true"
  - "sync validation_rules.md: +E-CURR-REF-BROKEN (bảng + error_codes)"
verified: true
method: ran-test
status: active
todo: "Task 4 (backend collect → reference/ + kiểm reference/ chỉ .md); Task 5/6 (dựng giáo trình + next-lesson); Task 7 (auto-advance); Task 8 (E-EXAM-REF-BROKEN + grade); Task 9 (đăng ký lệnh CR-0008). Các bước ghi vault cần CR-0008 approved."
reversible: "Gỡ check REF-BROKEN + 1 mã validation_rules + 2 test."
```

## DEC-061 — Task 8.1 Exam ref-integrity: E-EXAM-REF-BROKEN (mã thứ 7/7 — tầng validator HOÀN TẤT)

```yaml
id: DEC-061
type: decision
date: 2026-07-05
title: "_check_exam_results (E-EXAM-REF-BROKEN): ref bài nộp tồn tại trong exam/ NGOÀI vault + target là topic/Curriculum_Point tồn tại; RED-first"
spec_ref: "spec curriculum-driven-learning R9.4/R9.6; design Data Models (exam_results); CR-0007 (schema exam_results approved); tiền lệ DEC-034/058 (validator enforcement không cần CR lệnh)"
summary: >
  Hiện thực enforcement Class A cho exam_results.md: (1) mỗi result.ref phải resolve VÀO exam_root
  (vault_root.parent/exam) VÀ tồn tại — bài nộp (có thể là CODE) nằm NGOÀI vault, ref buộc dùng '..'
  (hợp lệ theo thiết kế, không cấm '..'); (2) target ∈ {tên topic} ∪ {Curriculum_Point ids} (đọc
  curriculum.md nếu có, lỗi curriculum để _check_curriculum lo — dùng Report() nháp tránh double-report).
  verdict là Class D (không kiểm nội dung). Wire cuối _validate_topic (exam_results.md TÙY CHỌN).
design_refinement (tách gating sai của tasks.md): >
  tasks.md gộp Task 8.1 (validator E-EXAM-REF-BROKEN) + 8.2 (cmd_grade) dưới 'sau CR-0007/0008'. Nhưng 8.1
  là ENFORCEMENT của schema exam_results ĐÃ duyệt (CR-0007), giống Task 3 (đọc-kiểm) → KHÔNG cần CR-0008
  (CR-0008 chỉ cho LỆNH GHI cmd_grade). Tách: 8.1 làm ngay (không CR), 8.2 chờ CR-0008. Tiền lệ DEC-034.
milestone: >
  HOÀN TẤT 7/7 mã ngữ nghĩa tính năng: 6 curriculum (DUP-ID/ORDER/EMPTY-OBJECTIVE/POINTER/LESSON-LINK/
  REF-BROKEN) + 1 exam (EXAM-REF-BROKEN). TẦNG VALIDATOR (đọc-kiểm, Class A) của curriculum-driven-learning
  ĐÃ XONG. Phần còn lại (Task 4-9) đều là LỆNH GHI → cần CR-0008 approved.
evidence:
  - "ran-test RED: test_exam_results_validator.py 4 failed (AttributeError _check_exam_results) trước khi hiện thực"
  - "ran-test GREEN: test_exam_results_validator 4 passed + test_validation_rules_codes 2 passed (coverage 2 chiều)"
  - "ran-test: full suite 401 passed (397 + 4 test 8.1); ran-command: validate --scope full pass:true, errors:[]"
  - "read-source: _parse_state_model (exam_results đã trong _SCHEMA_MODELS từ DEC-058); scan_abspath chặn abspath ref (INV-16); _validate_topic wire sau _check_curriculum"
  - "sync validation_rules.md: +E-EXAM-REF-BROKEN (bảng + error_codes, coverage 2 chiều)"
verified: true
method: ran-test
status: active
todo: "CÒN LẠI đều cần CR-0008 approved (lệnh GHI): Task 4.2 collect, Task 5 curriculum, Task 6 next-lesson, Task 7 auto-advance (móc cmd_done), Task 8.2 grade, Task 9 đăng ký registry+router. Rồi CR-0009 (spec) + E2E (Task 10)."
reversible: "Gỡ _check_exam_results + call + 1 mã validation_rules + test; validator lõi không phụ thuộc."
```

## DEC-062 — CR-0008 approved (owner) + Task 4.2 `cmd_collect` (RED-first) + Task 4.1 gộp vào INV-17

```yaml
id: DEC-062
type: decision
date: 2026-07-05
title: "Duyệt CR-0008 (move pending→approved, chốt tên 5 lệnh) + hiện thực lệnh GHI đầu tiên cmd_collect (reference/); Task 4.1 'reference chỉ .md' KHÔNG thêm check (đã có INV-17)"
spec_ref: "CR-0008 (approved); spec curriculum-driven-learning R1/R2/R4; tasks Task 4; DEC-055 (design); §12"
summary: >
  Owner duyệt CR-0008 qua tín hiệu 'duyệt theo khuyến nghị từng bước'. Áp governance: move
  change_requests/pending/cr-0008 → approved (status approved, date_decided, CHỐT tên lệnh:
  collect/curriculum(+--check)/next-lesson/grade; quy ước display '/next-lesson' ↔ backend identifier
  'next_lesson'). Changelog CR-0008 HOÃN tới khi đủ 5 lệnh áp (theo rule 'approved AND applied').
  Triển khai INCREMENTAL. Increment đầu: cmd_collect (Task 4.2) — ghi lát cắt tài liệu vào
  topics/<topic>/reference/<slug>.md, transaction-LIGHT, backend ghi tất định (AI-chat lấy nội dung như
  cmd_source/cmd_learn). Đăng ký ĐỒNG BỘ: CLI_COMMANDS+parser+dispatch (session.py) + backends+bảng
  (commands.md) + router.commands (router_prompt.md) — 3 drift-guard giữ khớp.
task_4_1_refinement (không thêm check 'reference chỉ .md'): >
  Phân tích: INV-17 (_check_no_code_in_vault) đã quét TOÀN vault, chặn code/đuôi-code/manifest/dir ở MỌI
  nơi kể cả reference/ → E-MIX-CODE. Thêm check 'reference chỉ .md' = trùng phần NGUY HIỂM (code); phần
  còn lại (.txt/.json trong reference) vô hại → ceremony. CỐ Ý KHÔNG thêm (phân biệt under-enforce vs trùng).
evidence:
  - "governance: approved/cr-0008-curriculum-commands.md (status approved); pending/cr-0008 đã xóa; test_change_requests_scaffold 2 passed"
  - "ran-test RED: test_session_collect.py 6 failed (cmd_collect chưa có) trước khi hiện thực"
  - "ran-test GREEN: test_session_collect 6 passed + test_commands_registry 5 + test_router_prompt_consistency 3 = 14 passed (registry↔CLI↔router khớp)"
  - "ran-test: full suite 407 passed (401 + 6 collect); ran-command: validate --scope full pass:true, errors:[]"
  - "read-source: cmd_source (khuôn), _build_parser (elif chain), main() dispatch write chain"
verified: true
method: ran-test
status: active
todo: "CÒN lệnh CR-0008: cmd_curriculum (+--check, Task 5) → cmd_next_lesson (Task 6, INV-25) → auto-advance cmd_done (Task 7) → cmd_grade (Task 8.2). Rồi changelog CR-0008 + HUONG_DAN (Task 9) + CR-0009 spec + E2E (Task 10)."
reversible: "Gỡ cmd_collect + 'collect' khỏi CLI_COMMANDS/parser/dispatch + backends/bảng commands.md + router + test; move cr-0008 về pending."
```

## DEC-063 — Task 5 `cmd_curriculum`: dựng giáo trình (RED-first) + `--check` gộp vào `/validate`

```yaml
id: DEC-063
type: decision
date: 2026-07-05
title: "cmd_curriculum dựng curriculum.md từ điểm học (JSON), transaction-FULL cổng E-CURR-*; teachable=true; create-new-only. curriculum --check GỘP vào /validate (không thêm cờ)"
spec_ref: "CR-0008 (approved); spec curriculum-driven-learning R3/R4/R5/R6; DEC-055/058-062; §12"
summary: >
  Lệnh CR-0008 thứ 2. cmd_curriculum(topic, points_json): AI (chat) soạn NỘI DUNG điểm (Class D) truyền
  qua JSON list [{objective, source_refs?}]; backend gán cp-NNN + order 1..N TẤT ĐỊNH + status=not_started +
  lesson_id=null + current_point=cp-001 + teachable=true, ghi curriculum.md qua _dump_state (safe_dump →
  free-text objective an toàn, KHÔNG lặp bug DEC-046). transaction-FULL → _check_curriculum kiểm E-CURR-*
  (dup-id/order/objective/pointer/lesson-link/ref-broken) → cấu trúc sai thì ABORT (không commit curriculum lỗi).
  Chỉ DỰNG MỚI (đã có curriculum.md → SessionError; sửa/bổ sung R8 là luồng riêng sau). Đăng ký đồng bộ
  CLI_COMMANDS+parser+dispatch+commands.md+router (3 drift-guard xanh).
design_refinements:
  - "curriculum --check (CR-0008 liệt kê) KHÔNG thêm cờ riêng: /validate (validate.py) ĐÃ chạy _check_curriculum toàn vault → báo mọi E-CURR-* của curriculum. --check trên 1 file = trùng → ceremony (như Task 4.1 gộp INV-17). Người dùng /validate để kiểm."
  - "teachable=true khi commit: vì transaction-FULL abort nếu cấu trúc sai → curriculum committed LUÔN hợp lệ cấu trúc (Class A). 'Đủ sâu/rộng nội dung' vẫn là Class D (AI/người), validator không gate."
  - "points qua JSON (không nhiều --arg): input có cấu trúc N phần tử, JSON là cách sạch + backend json.loads tất định; free-text vào YAML qua safe_dump."
evidence:
  - "ran-test RED: test_session_curriculum.py 7 failed (cmd_curriculum chưa có)"
  - "ran-test GREEN: test_session_curriculum 7 + test_commands_registry 5 + test_router_prompt_consistency 3 = 15 passed"
  - "ran-test: full suite 414 passed (407 + 7); ran-command: validate --scope full pass:true, errors:[]"
  - "read-source: _run_tx (default FULL → _check_curriculum), _dump_state (safe_dump), cmd_source/cmd_collect (khuôn), json đã import"
verified: true
method: ran-test
status: active
todo: "Task 6 cmd_next_lesson (sinh lesson-NNN cho current_point, INV-25) → Task 7 auto-advance (cmd_done) → Task 8.2 cmd_grade → Task 9 changelog CR-0008 + HUONG_DAN → CR-0009 spec + E2E (Task 10)."
reversible: "Gỡ cmd_curriculum + 'curriculum' khỏi CLI_COMMANDS/parser/dispatch + commands.md/router + test."
```

## DEC-064 — Task 6 `cmd_next_lesson`: "nhảy bài" (sinh lesson kế cho current_point) — RED-first

```yaml
id: DEC-064
type: decision
date: 2026-07-05
title: "cmd_next_lesson: sinh lessons/lesson-NNN cho current_point (objective bám point), set point.lesson_id, append topic_state.lessons[] + regen view từ TẤT CẢ lesson, trỏ vault_state; transaction-FULL"
spec_ref: "CR-0008 (approved); spec curriculum-driven-learning R6 (sinh nhiều lesson); INV-25/09/08/03; DEC-055/063"
summary: >
  Lệnh CR-0008 thứ 3 — mắt xích 'một topic nhiều bài'. cmd_next_lesson(topic): điều kiện teachable=true
  (R6.8) + current_point CHƯA có lesson_id (chưa /done nhảy điểm). Tạo lesson-NNN (số kế tiếp, quét
  lessons/) từ template với objective = objective của current_point; set curriculum current_point.lesson_id;
  append topic_state.lessons[] {id, status}; REGEN view review_schedule+assessment từ TẤT CẢ lesson (cũ
  đọc-đĩa + mới in-memory) qua VW.regen_all(stage='full') → INV-09/25; trỏ vault_state.current_lesson + mở
  phiên. Tất cả trong 1 transaction-FULL: validator kiểm INV-25 (index↔đĩa) + INV-09 (view) + INV-08 (replay)
  + E-CURR-LESSON-LINK (point.lesson_id trỏ lesson thật) → sai bất kỳ → ABORT (lưới an toàn, không ship sai).
key_decisions:
  - "Regen từ TẤT CẢ lesson (không chỉ lesson mới như cmd_learn): lesson mới in-memory chưa trên đĩa lúc regen → ghép model thủ công [đọc-đĩa các lesson cũ] + [model lesson mới]; đúng cái validator regen sau commit (đĩa có cả hai) → khớp INV-09. stage='full' + claim_texts (đồng bộ has_draft_knowledge INV-26, như _regen_topic_views)."
  - "current_point KHÔNG dời khi next-lesson (chỉ gắn lesson_id); dời điểm là việc /done auto-advance (Task 7). Guard 'point đã có lesson' chống tạo trùng lesson cho một điểm."
  - "objective của point làm cả LESSON_TITLE + OBJECTIVE (point chỉ có objective, không title riêng) — free-text qua _dump_state safe_dump (an toàn)."
evidence:
  - "ran-test RED: test_session_next_lesson.py 5 failed (cmd_next_lesson chưa có)"
  - "ran-test GREEN: test_session_next_lesson 5 + test_commands_registry 5 + test_router_prompt_consistency 3 = 13 passed"
  - "ran-test: full suite 419 passed (414 + 5); ran-command: validate --scope full pass:true, errors:[] (INV-25/09/08 khớp sau khi thêm lesson-002 vào demo)"
  - "read-source: cmd_learn (khuôn tạo lesson + apply_views), _regen_topic_views/_apply_views_to_topic_raw (regen đa-lesson), _lesson_model_from_raw(raw, path)"
verified: true
method: ran-test
status: active
todo: "Task 7 auto-advance (móc cmd_done: qua learned_gate → dời current_point sang điểm kế chưa done, set point.status=done) → Task 8.2 cmd_grade → Task 9 changelog CR-0008 + HUONG_DAN → CR-0009 spec + E2E (Task 10)."
reversible: "Gỡ cmd_next_lesson + 'next_lesson' khỏi CLI_COMMANDS/parser/dispatch + commands.md/router + test."
```

## DEC-065 — Task 7 auto-advance giáo trình: móc `cmd_done` (learned_gate → dời `current_point`) — RED-first

```yaml
id: DEC-065
type: decision
date: 2026-07-06
title: "_advance_curriculum (helper thuần, tất định) + wire vào cmd_done: khi lesson đạt learned_gate và map một curriculum_point CHƯA done → set point.status=done, dời current_point sang point chưa-done đầu tiên theo order; hết → giữ point tồn tại (hoàn tất ngầm, KHÔNG field mới); ghi curriculum.md trong CÙNG transaction-FULL của /done"
spec_ref: "CR-0008 (approved); spec curriculum-driven-learning R7 (auto-advance); INV-03/25; DEC-055/064; LessonStatus 'learned' = gate-passed"
summary: >
  Mắt xích R7 — 'học xong bài, giáo trình tự tiến điểm'. Tách BẢN CHẤT thành helper THUẦN
  _advance_curriculum(cur_raw, lesson_id, learned, today)->bool (không I/O, tất định, dễ kiểm mọi nhánh)
  + WIRE mỏng vào cmd_done: sau regen, learned = regen['lesson_status'].get(lesson_id)=='learned' (status
  lesson_state đọc-đĩa, chính là gate-passed literal); nếu topic có curriculum.md → _load_raw + gọi helper;
  True → append TX.Write(curriculum.md, expected_read_hash=hash-hiện-tại) vào writes của CÙNG transaction-FULL.
  Validator gate E-CURR-* (POINTER/LESSON-LINK/ORDER...) trước commit → advance sai cấu trúc → ABORT (rollback
  cả /done). KHÔNG curriculum / chưa learned / point đã done / lesson không map → writes GIỮ NGUYÊN
  (backward-compat tuyệt đối: mọi test /done cũ xanh).
key_decisions:
  - "current_point khi hết point chưa-done: GIỮ NGUYÊN (trỏ point vừa-done, tồn tại) thay vì thêm field 'completed'/set null. Lý do: null → E-CURR-POINTER dangling (INV-03); field mới → cần CR schema (ceremony). 'Hoàn tất' là trạng thái NGẦM suy ra được (mọi point status=done) — không cần lưu trùng."
  - "Idempotent chống nhảy-2-lần: point đã status=done → helper trả False (không re-advance, không ghi thừa) → /done gọi lại trên lesson learned cũ không dời con trỏ oan."
  - "Điều kiện learned == (lesson_state.status=='learned'): dùng regen['lesson_status'] có sẵn (không tính lại gate) — status này CHÍNH là kết quả gate (INV-07); nếu lesson_state.status=learned mà lesson.md thiếu evidence → FULL validation của /done tự chặn E-GATE-FAIL trước khi advance kịp commit."
  - "TÁCH helper thuần vs wire: helper phủ trọn logic (5 unit thuần, kể cả learned=True + all-done + idempotent + unmapped); wire chỉ cần integration nhánh KHÔNG-advance (regression). Đường learned→advance end-to-end (cần lesson qua-gate thật) để E2E Task 10 — tránh dựng fixture gate nặng trùng lặp ở tầng unit."
evidence:
  - "ran-test RED: test_advance_curriculum.py 5 failed (module 'session' has no attribute '_advance_curriculum') + 1 passed (integration no-op vốn đúng = regression guard)"
  - "ran-test GREEN: test_advance_curriculum.py + test_session_done.py = 11 passed"
  - "ran-test: full suite 425 passed (419 + 6 test Task 7); ran-command: validate --system . --vault ..\\learning_vault --level full --scope full pass:true, errors:[], warnings:[]"
  - "read-source: cmd_done (nơi móc, sau _apply_views_to_topic_raw), _regen_topic_views (regen['lesson_status']={m.lesson_id:m.status}), CurriculumPoint/Curriculum model (status Literal not_started/in_progress/done), LessonStatus Literal ('learned'=gate-passed)"
verified: true
method: ran-test
status: active
todo: "Task 8.2 cmd_grade (ghi exam_results.md, transaction-LIGHT, ref exam/ ngoài vault) → Task 9 changelog CR-0008 + HUONG_DAN 5 lệnh mới → CR-0009 spec §3/§11A/§14 bump v2.7 → Task 10 E2E (gồm đường learned→auto-advance thật)."
reversible: "Gỡ _advance_curriculum + khối wire trong cmd_done (5 dòng) + test_advance_curriculum.py — /done trở về hành vi trước, không dữ liệu tồn dư (chỉ ghi curriculum.md khi advance)."
```

## DEC-066 — Task 8.2 `cmd_grade`: ghi bản ghi chấm exam (backend tự tính ref tương đối) — RED-first

```yaml
id: DEC-066
type: decision
date: 2026-07-06
title: "cmd_grade(topic, submission_id, file, target, verdict): append entry vào topics/<topic>/exam_results.md, transaction-LIGHT; verify NGAY trong lệnh (bài nộp tồn tại trong exam/ NGOÀI vault + target ∈ {topic,cp} + submission_id pattern + không trùng INV-04); backend TỰ TÍNH ref TƯƠNG ĐỐI portable từ topic_dir"
spec_ref: "CR-0008 (approved) /grade; spec curriculum-driven-learning R9 (Exam_Store); INV-04/16/17; DEC-061 (_check_exam_results Task 8.1); model ExamResults/ExamResult"
summary: >
  Lệnh CR-0008 thứ 5 (cuối) — khép vòng exam. Bài nộp (có thể CODE) ở exam/ sibling learning_vault →
  KHÔNG phá INV-17 trên vault (R9.5); chỉ METADATA chấm (không code) ở exam_results.md TRONG vault.
  cmd_grade guard NGAY trong lệnh (KHÔNG dựa post-validate vì LIGHT không chạy _check_exam_results):
  (1) submission_id pattern ^ex-\S+; (2) file bài nộp resolve dưới exam_root=(vault.parent/exam) + is_file
  → thiếu/ngoài exam → SessionError, KHÔNG tạo bản ghi bộ phận (R9.6); (3) target ∈ {topic}∪{cp id nếu có
  curriculum.md}; (4) submission_id chưa có trong results (INV-04). Đạt hết → append entry {submission_id,
  ref, target, graded_at, verdict} qua transaction-LIGHT (tạo file nếu chưa có, else append + expected_read_hash).
key_decisions:
  - "Backend TỰ TÍNH ref tương đối (os.path.relpath(file_resolved, topic_dir) → as_posix) thay vì bắt người dùng gõ '../../../exam/...'. Fix BẢN CHẤT: chống lỗi tay + đảm bảo ref LUÔN resolve đúng cái validator kỳ vọng ((topic_dir/ref).resolve() == bài nộp) + portable (tương đối, không drive-letter → INV-16). Input --file là đường dẫn thật (resolve tại lệnh), KHÔNG lưu."
  - "Dùng os.path.relpath (thêm import os) thay Path.relative_to(walk_up=True): walk_up chỉ có từ 3.12, nhưng selfcheck yêu cầu Python>=3.10 → os.path.relpath tương thích rộng hơn (commercial robustness)."
  - "Guard trong-lệnh (không dựa validator post-commit): grade là LIGHT (in-session, spec 10.8) nên _check_exam_results (chạy ở _validate_topic full-scope) KHÔNG chắc chạy → R9.6 phải do chính cmd_grade enforce. Song validator full vẫn là lưới thứ 2 (E-EXAM-REF-BROKEN) khi audit toàn vault."
  - "verdict free-text Class D (R9.3) — chỉ kiểm không-rỗng; KHÔNG kiểm nội dung/không tự tuyên bố đảm bảo."
evidence:
  - "ran-test RED: test_session_grade.py 8 failed (cmd_grade chưa có / 'grade' chưa vào CLI_COMMANDS)"
  - "ran-test GREEN: test_session_grade 8 + test_commands_registry 5 + test_router_prompt_consistency 3 = 16 passed"
  - "ran-test: full suite 433 passed (425 + 8); ran-command: validate --scope full pass:true, errors:[], warnings:[]"
  - "read-source: _check_exam_results (exam_root=vault.parent/exam, valid_targets={topic}∪{cp.id}, (topic_dir/ref).resolve()); ExamResult model (submission_id ^ex-, verdict str, INV-04 uniqueness); cmd_collect (khuôn LIGHT + guard slug); parser/dispatch/CLI_COMMANDS/commands.md/router (đăng ký đồng bộ)"
verified: true
method: ran-test
status: active
todo: "Task 9: move CR-0007/0008/0009 pending→approved + changelog.md (khi ĐỦ — CR-0009 spec chưa soạn xong) + cập nhật HUONG_DAN.md 5 lệnh mới + drift-guard test_huong_dan. Rồi CR-0009 spec §3/§11A/§14 bump v2.7 + Task 10 E2E (gồm learned→auto-advance thật)."
reversible: "Gỡ cmd_grade + 'grade' khỏi CLI_COMMANDS/parser/dispatch + dòng commands.md(bảng+backends)/router + test_session_grade.py. exam_results.md chỉ sinh khi grade → không tồn dư ở vault ship (rỗng)."
```

## DEC-067 — Task 9: khép registry/tài liệu — changelog CR-0008 + HUONG_DAN 5 lệnh mới

```yaml
id: DEC-067
type: decision
date: 2026-07-06
title: "Ghi changelog CR-0008 (5 lệnh giáo trình đã áp xong) + thêm 5 lệnh vào HUONG_DAN.md (khối máy-đọc + mục 'Học theo giáo trình' cho người học); drift-guard test_huong_dan/test_commands_registry/test_router xanh"
spec_ref: "tasks.md Task 9; §12 bước 7 (changelog chỉ ghi khi CR áp XONG); CR-0007/0008 approved; DEC-052 (HUONG_DAN drift-guard)"
summary: >
  Sau khi ĐỦ 5/5 lệnh CR-0008 áp xong + validator-layer + auto-advance (DEC-058..066), khép tài liệu:
  (1) thêm dòng changelog cr-0008 (ngày 2026-07-06, liệt kê file đụng tới, VERSION —); (2) HUONG_DAN.md:
  thêm mục người-học 'Học theo giáo trình — chủ đề dài, nhiều bài' (bảng 5 lệnh + ghi chú exam/ ngoài vault)
  + thêm /collect /curriculum /next-lesson /grade vào khối 'commands (máy đọc)'. Drift-guard test_huong_dan
  ép mọi lệnh trong khối máy-đọc phải TỒN TẠI trong commands.md → xanh (đã đăng ký ở DEC-062/063/064/066).
key_decisions:
  - "Changelog CR-0008 VERSION cột '—' (không bump): lệnh + validator mã lỗi là MỞ RỘNG tương thích ngược, KHÔNG đổi schema-version file (khác CR-0001 bump v2.6). Đúng nguyên tắc bump chỉ khi đổi cấu trúc dữ liệu on-disk."
  - "CR-0009 (spec bump v2.7) CHƯA ghi changelog: spec §3/§11A/§14 chưa soạn/duyệt → theo §12 chỉ ghi khi áp xong. Task 9 chỉ khép CR-0008 (đã xong), tách CR-0009 sang bước sau — không ghi trước 'nợ'."
  - "HUONG_DAN mô tả /grade + exam/ bằng ngôn ngữ người-học ('bài nộp kể cả code đặt NGOÀI kho để kho luôn sạch') — truyền đạt ĐÚNG ranh giới INV-17 mà không dùng thuật ngữ kỹ thuật; lệnh giữ English (DEC-052)."
evidence:
  - "read-source: changelog.md (đã có cr-0001..0007; thêm cr-0008), HUONG_DAN.md (khối commands máy-đọc + bảng người dùng), test_huong_dan.py (drift-guard: guide commands ⊆ commands.md)"
  - "ran-test: test_huong_dan 3 + test_commands_registry 5 + test_router_prompt_consistency 3 = 11 passed; full suite 433 passed (không đổi — thay đổi tài liệu, drift-guard phủ)"
  - "ran-command: validate --scope full pass:true, errors:[], warnings:[]"
verified: true
method: ran-test
status: active
todo: "CR-0009: soạn spec §3 (thêm reference/exam/curriculum), §11A (lệnh mới), §14 (multi-lesson), bump v2.7 → move pending→approved + changelog → Task 10 E2E (collect→curriculum→check→next-lesson→done-gate→auto-advance→next-lesson-002 + đường learned→advance thật) + test bảo toàn bất biến (10.2)."
reversible: "Gỡ dòng changelog cr-0008 + mục/lệnh giáo trình trong HUONG_DAN — drift-guard vẫn xanh (lệnh vẫn trong commands.md); thuần tài liệu."
```

## DEC-068 — Task 10: nghiệm thu E2E vòng giáo trình + đường learned→auto-advance THẬT + bảo toàn bất biến

```yaml
id: DEC-068
type: decision
date: 2026-07-06
title: "E2E tất định trên vault tmp: collect→curriculum→check(PASS)→next-lesson→(mô phỏng học qua learned_gate)→done→AUTO-ADVANCE(cp-001 done, current_point→cp-002)→next-lesson-2; + test bảo toàn bất biến (vault có curriculum+exam_results PASS INV-16/17/18/25). Khép tính năng curriculum-driven-learning"
spec_ref: "tasks.md Task 10.1/10.2; spec v2.7 §3.5/§14 bước 4b (DEV-006); DEC-065 (auto-advance unit, hoãn đường learned→advance sang E2E)"
summary: >
  Hợp đồng nghiệm thu cuối. test_e2e_curriculum_full_cycle chạy CHUỖI THẬT qua các cmd_* (không mock lõi):
  collect ghi reference/ → curriculum dựng 2 điểm teachable → validate PASS (không E-CURR/E-EXAM) → next-lesson
  sinh lesson-002 cho cp-001 (map lesson_id, current_point CHƯA dời) → mô phỏng AI dạy tới learned_gate
  (_make_lesson_learned: ghi lesson_state status=learned + mastery đạt ngưỡng _GATE + lesson.md có Sessions +
  transcript + 1 evidence/trục quote⊆transcript) → done: AUTO-ADVANCE đường learned=True THẬT (cp-001→done,
  current_point→cp-002) → next-lesson-2 sinh lesson-003 cho cp-002. FULL PASS cuối chuỗi. Bổ sung đường
  learned→advance mà DEC-065 cố ý hoãn (unit đã phủ logic; E2E nay phủ tích hợp thật qua validator gate).
  test_e2e_invariants_preserved: vault có curriculum + exam_results (grade ex-001 target cp-001) → PASS toàn bộ.
key_decisions:
  - "E2E là test NGHIỆM THU code đã hiện thực (T2-T9) → xanh-ngay là ĐÚNG, không vi phạm RED-first (RED-first áp cho HÀNH VI MỚI, đã làm ở T3/T7/T8). E2E chứng minh các mảnh ghép rời hoạt động như MỘT VÒNG qua đường chạy thật + validator FULL mỗi bước ghi."
  - "Mô phỏng 'học qua gate' bằng ghi lesson_state learned + evidence trực tiếp (đúng cái AI làm trong phiên qua LIGHT-write; snapshot validator không có transition-check khi /done đọc đĩa nên không kích E-STATE-ILLEGAL) — trung thực với kiến trúc, không hack. Khớp test_gate_evidence + pilot."
  - "Dùng demo vault (docker/lesson-001 sẵn) → next-lesson ra lesson-002/003, phản ánh topic thực có bài cũ + giáo trình chèn sau; chứng minh curriculum sống chung lesson không-map (INV-25 index vẫn nguồn sự thật)."
evidence:
  - "ran-test: test_e2e_curriculum.py 2 passed (full_cycle + invariants_preserved) ngay lần đầu — code T2-T9 khớp"
  - "ran-test: full suite 435 passed (433 + 2 E2E); ran-command: validate --scope full pass:true, errors:[], warnings:[]"
  - "read-source: _check_gate_and_evidence (_GATE ngưỡng + evidence theo axis từ lesson.md AST), lesson_state.template (status not_started khởi tạo), check_status_transition ('chỉ gọi khi CÓ baseline' → /done snapshot không kích)"
verified: true
method: ran-test
status: active
todo: "Tính năng curriculum-driven-learning HOÀN TẤT (T1-T10). Không còn task mở. Tương lai (ngoài scope hiện tại): R8 chèn điểm giữa chừng (Task 5.3 chưa làm — chưa có nhu cầu thực); alias lệnh tiếng Việt; MCP tool wrap."
reversible: "Gỡ test_e2e_curriculum.py (thuần test nghiệm thu, không đụng code sản phẩm)."
```

## DEC-069 — Task 5.3 / CR-0010: chèn điểm học giữa chừng giáo trình (R8) — RED-first

```yaml
id: DEC-069
type: decision
date: 2026-07-06
title: "cmd_curriculum_insert: chèn Curriculum_Point tại vị trí insert_at (1..N+1) qua cờ /curriculum --insert-at <pos> --point <json>; point mới order=pos + id cp-{max_suffix+1} duy nhất; order>=pos dịch +1 (giữ hoán vị); id/status point cũ + current_point GIỮ NGUYÊN; transaction-FULL"
spec_ref: "CR-0010 approved; spec curriculum-driven-learning R8; spec v2.7 §3.5; DEC-063 (--check là cờ trên /curriculum, tiền lệ không thêm tên lệnh); E-CURR-ORDER (hoán vị 1..N)"
summary: >
  Khép task mở cuối cùng (T5.3, R8) — 'sửa giáo trình đang học mà không dựng lại'. Là năng lực user-facing
  mới → đi qua CR-0010 (§12). Hiện thực bằng CỜ trên backend /curriculum (--insert-at + --point), KHÔNG
  thêm tên lệnh mới → drift-guard (CLI_COMMANDS↔commands.md↔router) BẤT BIẾN (tiền lệ --check DEC-063).
  Dispatch route: có --insert-at → cmd_curriculum_insert; không → cmd_curriculum (build). Backend riêng giữ
  single-responsibility. Ngữ nghĩa R8: chèn tại pos (1..N+1) → point mới order=pos, các point order>=pos
  dịch +1 (giữ hoán vị 1..N+1 cho E-CURR-ORDER); id mới cp-{max_suffix+1}; current_point (tham chiếu ID,
  KHÔNG phụ thuộc order) + status point cũ giữ nguyên (R8.3); transaction-FULL re-validate E-CURR-* → sai
  rollback (R8.5). Vị trí ngoài [1..N+1] / curriculum thiếu / objective rỗng → SessionError không đổi (R8.7).
key_decisions:
  - "id mới = cp-{max_suffix+1} (KHÔNG = cp-{order}): id là ĐỊNH DANH ổn định, order là THỨ TỰ — tách bạch. Dùng order làm id sẽ đụng khi dịch order hoặc khi xoá-rồi-chèn. max_suffix+1 đảm bảo duy nhất + ổn định (R8.4). Parse suffix qua regex cp-(\\d+); phòng vệ thêm check trùng."
  - "CỜ trên /curriculum thay vì lệnh mới /curriculum-add: tránh phình registry + drift-guard, đúng tiền lệ DEC-063 (--check). CR-0010 vẫn mở (năng lực mới phải qua §12) nhưng KHÔNG chạm tên lệnh → thay đổi tối thiểu."
  - "R8.6 (re-check FAIL → not teachable): cấu trúc-FAIL → transaction-FULL ABORT (mạnh hơn: không chèn). 'Đủ sâu/rộng' là Class D (không mã máy) — nhất quán ranh giới hệ thống; teachable giữ nguyên (curriculum vẫn structurally valid sau chèn well-formed)."
  - "current_point giữ nguyên khi chèn (kể cả chèn TRƯỚC current_point): R8.3 yêu cầu giữ con trỏ tiến độ; người học đang ở điểm cũ, chèn điểm mới không kéo họ lùi. Điểm mới status=not_started sẽ được tới theo order khi auto-advance chạm."
evidence:
  - "ran-test RED: test_session_curriculum_insert.py 9 failed (no attribute cmd_curriculum_insert)"
  - "ran-test GREEN: test_session_curriculum_insert 9 + test_session_curriculum (build cũ) + test_commands_registry 5 = 21 passed (drift-guard xanh, không hồi quy build)"
  - "ran-test: full suite 444 passed (435 + 9); ran-command: validate --scope full pass:true, errors:[], warnings:[]"
  - "read-source: _check_curriculum (E-CURR-ORDER = sorted(orders)==[1..N]; DUP-ID; POINTER dùng current_point∈ids; REF-BROKEN), cmd_curriculum (khuôn build + _dump_state), parser/dispatch curriculum"
verified: true
method: ran-test
status: active
todo: "Tính năng curriculum-driven-learning HOÀN TẤT 100% (T1-T11 + T5.3). cr-0001..0010 approved+changelog. Không còn task mở. Tương lai ngoài scope: alias lệnh tiếng Việt; MCP tool wrap; cross-AI handoff re-test (NOTE-031)."
reversible: "Gỡ cmd_curriculum_insert + 2 cờ parser + nhánh dispatch (trả --points về required) + dòng commands.md/HUONG_DAN/spec §3.5 + test. /curriculum trở về chỉ-dựng."
```

## DEC-070 — Hardening HANDOFF_TEST (đóng NOTE-031): Phần A SOLO trọn vẹn + vòng v2.7 + drift-guard

```yaml
id: DEC-070
type: decision
date: 2026-07-06
title: "Sửa gốc HANDOFF_TEST.md để AI nhận handoff KHÔNG dừng sớm: tách A (SOLO, không cần người, làm ĐẾN HẾT) vs B (cần người học, bỏ được nếu solo); thêm A2 vòng giáo trình v2.7 (collect/curriculum/--insert-at/next-lesson/grade); + drift-guard test_handoff_commands; sửa START_HERE v2.6→v2.7"
spec_ref: "NOTE-031 (bản handoff cũ thất bại: AI kia chỉ /learn rồi dừng); DEC-053 (HANDOFF_TEST gốc); DEC-052 (drift-guard HUONG_DAN khuôn mẫu); spec v2.7"
summary: >
  Chẩn đoán gốc vì sao AI nhận handoff 'chỉ /learn rồi dừng': (1) Phần A (máy) và B (dạy thật cần NGƯỜI)
  lẫn điều kiện → AI test SOLO tưởng bị chặn, dừng; (2) Phần A cũ không phải chuỗi tự-chạy-trọn (bước review
  'nếu có item' bị bỏ với vault rỗng → A cụt); (3) handoff KHÔNG nhắc tính năng v2.7 (collect/curriculum/
  next-lesson/grade) + START_HERE ghi spec v2.6 cũ; (4) không drift-guard → dễ tham chiếu lệnh lệch.
  Fix BẢN CHẤT: Phần A = chuỗi SOLO hoàn chỉnh chia A1 (learn/validate/status/schedule/audit) + A2 (vòng
  giáo trình v2.7, gồm --insert-at R8 + grade exam ngoài vault) — làm ĐẾN HẾT, KHÔNG cần người; Phần B tách
  rõ 'cần người học thật, solo → ghi bỏ, KHÔNG tính trượt'. Rubric +R4b (curriculum.md/exam_results sau A2).
  Thêm khối 'commands (máy đọc)' + test_handoff_commands (3 test) khoá lệnh handoff ⊆ commands.md + phủ
  vòng v2.7. START_HERE spec_ref v2.7.
key_decisions:
  - "Phần A SOLO-completable là gốc rễ: bảo đảm Class A đến từ CHẠY LỆNH, không cần người → tách khỏi Class D (dạy thật cần người). Làm rõ 'đừng dừng ở /learn, chạy hết A' trực tiếp chặn lỗi NOTE-031."
  - "A2 dùng đúng chuỗi đã kiểm chứng LIVE (collect→curriculum→insert→next-lesson→grade→validate PASS) → handoff nghiệm thu hệ HIỆN TẠI (v2.7) chứ không chỉ vòng lõi cũ."
  - "Drift-guard test_handoff_commands (khuôn test_huong_dan qua md_ast.extract_yaml_under_heading, khớp tiêu đề CHÍNH XÁC 'commands (máy đọc)' → heading KHÔNG đánh số) — chống handoff drift lệnh, đóng lỗ hổng cũ tận gốc thay vì chỉ sửa văn bản một lần."
  - "KHÔNG tự chạy được cross-AI test (cần AI+người khác) — chỉ chuẩn bị turnkey; đánh giá thật vẫn do owner + AI khác (ranh giới trung thực, như DEC-053)."
evidence:
  - "read-source: HANDOFF_TEST.md (§3 A1/A2 + B, §5 self-report, §6 rubric R4b, §commands máy đọc), START_HERE.md (step 6 v2.7), md_ast.extract_yaml_under_heading (khớp h.text == heading_text exact)"
  - "ran-test RED: test_handoff_commands 2 failed (TypeError None — heading '8. commands' không khớp) → sửa heading → GREEN 3 passed"
  - "ran-test: full suite 447 passed (444 + 3 handoff drift-guard); ran-command: validate --scope full pass:true, errors:[], warnings:[]"
  - "ran-command (live, phiên trước): chuỗi A2 collect→curriculum→--insert-at→next-lesson→grade→validate PASS trên vault tạm — cơ sở để viết A2"
verified: true
method: ran-test
status: active
todo: "Cross-AI handoff THẬT vẫn chờ owner chạy AI khác + đánh giá theo rubric R1-R7 (NOTE-031 sẽ đóng khi có bản đạt). Tương lai ngoài scope: MCP wrap (design-first riêng); alias tiếng Việt đã từ chối (DEC-052)."
reversible: "Revert HANDOFF_TEST §3/§5/§6/§commands + START_HERE v2.7→v2.6 + xóa test_handoff_commands.py. Thuần tài liệu + 1 test guard."
```

## DEC-071 — Audit đối kháng lệnh curriculum: fix GỐC crash traceback trên file sửa-tay-hỏng — RED-first

```yaml
id: DEC-071
type: decision
date: 2026-07-06
title: "_load_model_validated (generic, validate raw qua pydantic model TRƯỚC khi iterate) — vá crash AttributeError của cmd_curriculum_insert/cmd_next_lesson (curriculum points sai kiểu) + cmd_grade (curriculum points reference + exam_results.results sai kiểu); driver suy biến về E-SCHEMA sạch"
spec_ref: "NOTE-018 (nguyên tắc: driver KHÔNG BAO GIỜ crash traceback, luôn về mã E-* chẩn đoán được); DEC-041/042/043 (khuôn validate-qua-model ở biên đọc); pilot self-simulate (NOTE-015..020)"
summary: >
  Trước khi giao cross-AI test, chạy AUDIT ĐỐI KHÁNG (adversarial probe qua CLI thật, phương pháp pilot) các
  lệnh curriculum MỚI trên curriculum.md/exam_results.md SỬA-TAY-HỎNG. Phát hiện 3 lệnh cùng lớp lỗi: đọc RAW
  collection (points/results) rồi gọi phần_tử.get('id') — nếu YAML HỢP LỆ nhưng collection sai kiểu (list
  non-dict / không phải list) → AttributeError THÔ (crash traceback, vi phạm NOTE-018). PROBE 2: insert →
  crash; PROBE 3: grade append exam_results → crash; next_lesson cùng đường. Fix GỐC (không vá ngọn): helper
  chung _load_model_validated(path, model) validate raw qua pydantic model TRƯỚC khi iterate (khuôn
  _load_vault_state DEC-042); SchemaError ⊂ SessionError → main() báo E-SCHEMA sạch. Áp: insert/next_lesson
  dùng _load_curriculum_validated (=_load_model_validated(., M.Curriculum)); grade append dùng
  _load_model_validated(., M.ExamResults). grade ĐỌC curriculum (tham chiếu PHỤ để mở valid_targets) dùng
  guard MỀM isinstance (không ép E-SCHEMA — target=topic vẫn chấm được dù curriculum hỏng).
key_decisions:
  - "Phân biệt curriculum-là-ĐỐI-TƯỢNG (insert/next_lesson → validate cứng qua model, E-SCHEMA nếu hỏng) vs curriculum-là-THAM-CHIẾU-PHỤ (grade valid_targets → guard mềm isinstance, bỏ qua points hỏng, KHÔNG chặn chấm target=topic). Cùng triết lý bất-đối-xứng-có-chủ-đích DEC-043."
  - "Generic _load_model_validated thay 2 helper riêng: DRY + nhất quán khuôn DEC-042; nhận model làm tham số (M.Curriculum/M.ExamResults). Bắt SchemaError re-raise để giữ mã E-SCHEMA-YAML/E-SCHEMA từ _load_raw."
  - "exam_results append validate cứng qua M.ExamResults: grade là LIGHT (không chạy _check_exam_results post-commit) → nếu không validate lúc đọc, có thể append vào file rác rồi commit. Validate lúc đọc chặn append-lên-rác (an toàn thương mại)."
evidence:
  - "ran-command (adversarial CLI): PROBE 2 (points=list chuỗi → insert) TRƯỚC fix = Traceback AttributeError 'str' object has no attribute 'get' (session.py:795); SAU fix = JSON E-SCHEMA committed:false exit 1 (đã chạy lại xác nhận). PROBE 3 (exam_results.results=list chuỗi → grade) TRƯỚC = crash session.py:983"
  - "ran-test RED: test_curriculum_robustness.py 4→5 fail (AttributeError); SAU fix GREEN 5 passed"
  - "ran-test: full suite 452 passed (447 + 5 robustness); ran-command: validate --scope full pass:true, errors:[], warnings:[]"
  - "read-source: SchemaError(SessionError) [session.py:50]; dispatch write bắt SessionError→getattr error_code; _load_vault_state/_load_topic_state (khuôn validate-qua-model)"
verified: true
method: ran-test
status: active
todo: "Hệ sẵn sàng cross-AI test (452 passed, driver không-crash trên input hỏng cả lệnh cũ lẫn mới). Tương lai ngoài scope: MCP design-first; đóng NOTE-031 khi có bản handoff đạt."
reversible: "Gỡ _load_model_validated + _load_curriculum_validated (trả về _load_raw) + guard isinstance trong grade + test_curriculum_robustness.py. Nhưng KHÔNG nên revert — mất bảo đảm không-crash."
```

## DEC-072 — Fix test-defect drift-guard bootstrap: spec_ground_truth là pointer NGOÀI đơn vị, KHÔNG bắt-buộc-tồn-tại — RED-first

```yaml
id: DEC-072
type: decision
date: 2026-07-06
title: "test_bootstrap_pointers_all_exist ép MỌI pointer (gồm spec_ground_truth=../PROMPT_LEARNING_SYSTEM.md) tồn tại → fail oan trên MỌI bản copy portable sạch (cha không mang spec). Tách _required_in_unit_pointers (chỉ pointer TRONG đơn vị) khỏi spec ngoài-đơn-vị (DEC-047)"
spec_ref: "DEC-047 (START_HERE nói THẬT: spec gốc ở thư mục CHA, ngoài đơn vị portable); INV-16 (portability); phát hiện qua cross-AI HANDOFF_RESULT (Claude Opus 4.6) báo pytest 451/1"
summary: >
  Cross-AI handoff test (AI khác chạy bản copy Desktop) báo pytest 451 passed / 1 FAILED:
  test_bootstrap_pointers_all_exist vì '../PROMPT_LEARNING_SYSTEM.md' không có ở thư mục cha bản copy.
  AI kia chẩn đoán ĐÚNG là 'theo thiết kế, không phải bug hệ'. Nhưng đó là TEST-DEFECT thật: test assert
  MỌI pointer trong khối bootstrap của START_HERE phải tồn tại, GỘP NHẦM pointer TRONG-đơn-vị (read_order/
  first_run_check/setup_lock/runbook — phải luôn có) với spec_ground_truth (= ../PROMPT_LEARNING_SYSTEM.md,
  cố ý NGOÀI đơn vị theo DEC-047, không đi theo bản copy). Trên máy dev cha tình cờ CÓ spec → pass (452);
  trên MỌI bản copy portable sạch cha KHÔNG có spec → fail (451/1) → tín hiệu ĐỎ OAN cho mọi handoff hợp lệ,
  đúng ngay kịch bản portability hệ này cam kết hỗ trợ. Fix GỐC: tách _required_in_unit_pointers(b) (loại
  spec_ground_truth) làm tập bắt-buộc-tồn-tại; spec ngoài-đơn-vị kiểm riêng (phải khai báo '..' + KHÔNG nằm
  trong tập bắt-buộc). Đây là code(test)-lệch-design → KHÔNG cần CR (tiền lệ DEC-029).
key_decisions:
  - "Phân biệt pointer TRONG-đơn-vị (must-exist, khoá cứng chống dangling) vs pointer NGOÀI-đơn-vị (spec_ground_truth, optional, cố ý không đi theo copy). Test cũ vi phạm phân biệt này → false-negative trên chính ca portability."
  - "RED-first bằng test mô phỏng bản copy portable trong tmp (test_portable_copy_no_parent_spec): tạo mọi pointer trong-đơn-vị vào tmp, KHÔNG tạo spec cha, assert guard vẫn pass. Trước fix 2 test đỏ (NameError _required_in_unit_pointers), sau fix xanh."
  - "KHÔNG hạ chuẩn drift-guard: pointer trong-đơn-vị vẫn khoá cứng (test_bootstrap_pointers_all_exist giữ, chỉ đổi nguồn path sang _required_in_unit_pointers). Chỉ gỡ đúng phần over-assert."
  - "KHÔNG cần sửa START_HERE.md: nó đã nói THẬT (comment 'thư mục CHA — ngoài đơn vị học'). Lỗi nằm ở test, không ở tài liệu."
evidence:
  - "HANDOFF_RESULT.md (Desktop copy, Claude Opus 4.6): 'pytest 451 passed, 1 failed — test_bootstrap_pointers_all_exist — ../PROMPT_LEARNING_SYSTEM.md không tồn tại'."
  - "ran-command: Test-Path (workspace chính, cha) = True → pass; Test-Path (Desktop copy, cha) = False → fail. START_HERE spec_ground_truth: ../PROMPT_LEARNING_SYSTEM.md '# thư mục CHA (ngoài đơn vị học)'."
  - "ran-test RED: test_start_here_bootstrap.py 2 failed (NameError _required_in_unit_pointers) / 3 passed."
  - "ran-test GREEN: test_start_here_bootstrap.py 5 passed; full suite 454 passed (452 + 2 test mới); validate --scope full pass:true, errors:[], warnings:[]."
verified: true
method: ran-test
status: active
reversible: "Gộp lại spec_ground_truth vào tập must-exist (khôi phục over-assert) — KHÔNG nên: sẽ tái lập false-negative trên mọi handoff portable."
```

## DEC-073 — Fix GỐC E-EXAM-REF-BROKEN GIẢ trong transaction-overlay: thread vault root THẬT vào validate — RED-first

```yaml
id: DEC-073
type: decision
date: 2026-07-06
title: "_check_exam_results resolve ref bài nộp + exam/ SAI khi validate chạy trên overlay TEMP của transaction (exam/ là sibling NGOÀI vault → không copy vào overlay). Fix: thread real_vault_root (transaction.self.root) qua validate_full_semantic→core→_validate_topic→_check_exam_results; standalone giữ nguyên. KHÔNG hack theo tên tempdir/__file__ như bản copy Gemini (phá portability INV-16)"
spec_ref: "DEC-061/066 (E-EXAM-REF-BROKEN + exam/ NGOÀI vault, ref tương đối portable INV-16); spec §10.3 (transaction overlay validate); NOTE-036 (cross-AI handoff #2 Gemini phát hiện bug tích hợp THẬT); DEC-068 (E2E cũ bỏ sót vì chỉ validate STANDALONE)"
summary: >
  Bug tích hợp THẬT do cross-AI handoff #2 (Gemini) phát hiện, E2E của ta (DEC-068) BỎ SÓT vì chỉ validate
  STANDALONE, chưa từng chạy validator qua transaction-overlay SAU khi 1 topic có exam_results.md.
  Cơ chế bug (đã đọc code + reproduce): transaction._build_overlay() copy NỘI DUNG VAULT (self.root.rglob)
  sang thư mục TEMP; exam/ là SIBLING NGOÀI vault nên KHÔNG có trong overlay. validate_staged chạy
  validate_full_semantic (FULL) trên overlay → _check_exam_results: (a) exam_root=(vault_root.parent/exam)
  = TEMP-parent/exam (không tồn tại); (b) rp=(topic_dir/ref).resolve() với topic_dir=overlay temp, ref
  '../../../exam/..' resolve vào TEMP → không tồn tại → E-EXAM-REF-BROKEN GIẢ → BẤT KỲ lệnh FULL-transaction
  (/learn topic-mới, /done, /review, /next-lesson, /curriculum) SAU khi có exam_results.md đều ABORT OAN.
  Fix GỐC (phương án A, principled): thread vault root THẬT trên đĩa vào validate. transaction.validate_staged
  truyền real_vault_root=self.root xuống validate_full_semantic→validate_full_core→_validate_topic→
  _check_exam_results. Trong _check_exam_results: base_vault = real_vault_root or vault_root; real_topic =
  base_vault / topic_dir.relative_to(vault_root) (dựng lại topic dir THẬT — ref là tương đối topic_dir nên
  PHẢI resolve từ topic thật, không phải overlay temp); exam_root = base_vault.parent/exam. Standalone
  (real_vault_root=None) → base_vault=vault_root, real_topic=topic_dir → HÀNH VI CŨ Y NGUYÊN.
key_decisions:
  - "Phương án A (thread vault THẬT) thắng phương án B (coi exam-existence ngoài-scope trong overlay, hoãn tới standalone) vì B YẾU hơn: mất kiểm existence ngay tại điểm-ghi. A giữ full-validate tại điểm ghi + portable."
  - "TỪ CHỐI fix của Gemini (bản copy: if 'tx_overlay_' in str(vault_root): exam_root=Path(__file__).resolve().parent.parent.parent/exam). Hai lý do: (a) couple validator với tên tempdir NỘI BỘ của transaction (mong manh, vỡ nếu đổi prefix); (b) hardcode layout repo qua __file__, BỎ QUA vault_root truyền vào → phá INV-16 (validate vault ở vị trí khác sẽ resolve exam/ về chỗ validator, SAI) + có thể vỡ test demo_vault fixture. Gemini phát hiện bug ĐÚNG nhưng fix KHÔNG phù hợp portability."
  - "Phải dựng lại real_topic (không chỉ sửa exam_root) vì ref là TƯƠNG ĐỐI topic_dir (os.path.relpath, DEC-066): chỉ sửa exam_root mà giữ rp=(overlay_topic/ref) thì rp vẫn trỏ vào TEMP → under_exam vẫn False → chưa hết bug. real_vault_root là 'vault root thật' (không phải 'exam base') để tái dựng CẢ hai."
  - "KHÔNG mã lỗi mới, KHÔNG đổi ngữ nghĩa E-EXAM-REF-BROKEN → validation_rules.md không cần sync (drift-guard xanh). code-lệch-hành-vi-đúng → KHÔNG cần CR (tiền lệ DEC-029/072)."
evidence:
  - "read-source: transaction._build_overlay (rglob self.root, exam/ sibling không copy) + validate_staged (validate_full_semantic trên overlay); validate._check_exam_results (exam_root=vault_root.parent/exam, rp=topic_dir/ref)."
  - "ran-command RED (_probe.py): curriculum+grade tạo exam_results.md → cmd_next_lesson (FULL) → 'next_lesson committed: False [E-EXAM-REF-BROKEN]' (false-positive abort)."
  - "ran-command GREEN (sau fix, cùng probe): 'next_lesson committed: True []'."
  - "ran-test RED-first→GREEN: test_tx_exam_overlay.py 4 test (no-false-positive CLI + overlay-with-real-root + TEETH still-detects-broken-ref + standalone-unchanged) PASSED."
  - "ran-test: full suite 458 passed (454 + 4); ran-command: validate --scope full --at pass:true, errors:[], warnings:[]; selfcheck NGUYÊN VẸN."
verified: true
method: ran-test
status: active
credit: "Gemini 3.5 Flash (via Antigravity, cross-AI handoff #2) phát hiện bug tích hợp THẬT mà pilot/E2E của ta bỏ sót — điểm cộng lớn. Fix của nó (bản copy) không dùng (portability); workspace chính áp fix gốc đúng."
reversible: "Gỡ tham số real_vault_root khỏi 5 hàm validate + dòng transaction.validate_staged (trả về resolve theo vault_root) + xoá test_tx_exam_overlay.py. KHÔNG nên: tái lập false-positive abort mọi full-tx sau khi có exam_results."
```


## DEC-074 — Tính năng mandatory-curriculum-framework (Topic_Blueprint) — SPEC-first + RED-first, CR-0011..0014

```yaml
id: DEC-074
type: decision
date: 2026-07-07
title: "Thêm tầng khung giáo trình BẮT BUỘC (Topic_Blueprint) trên curriculum-driven-learning: schema blueprint + Blueprint_Validator 7 mã E-BP-* + lệnh /blueprint (build/edit/approve/amend) + Coverage_Map qua CurriculumPoint.area_refs. SPEC-first (requirements→design→tasks) rồi RED-first từng wave; git baseline trước khi làm sâu"
spec_ref: "spec mandatory-curriculum-framework R1..R7; CR-0011 (schema blueprint) / CR-0012 (area_refs) / CR-0013 (lệnh) / CR-0014 (spec §3.6 v2.7→v2.8); tiền lệ DEC-055..069 (curriculum-driven-learning), DEC-008 (drift-guard schema), DEC-034/058 (enforcement không cần CR mã lỗi)"
summary: >
  Owner yêu cầu 'khung sườn cố định' để mọi AI (giỏi/dở) bám khi dạy, không bỏ sót mảng. Đã tạo spec đầy đủ
  (requirements owner-viết + design + tasks do phiên này soạn), rồi triển khai 8 wave RED-first, verify sau
  mỗi wave (full suite + validate --scope full PASS), commit git mỗi mốc. Baseline 458→499 passed (+41).
  QĐ-1 Coverage_Map đặt ở CurriculumPoint.area_refs (phía curriculum EDITABLE) chứ không blueprint (phía KHÓA
  khi approved) — tránh xung đột R4.3. QĐ-2/3 phủ là CỔNG teachable (xem DEC-075). Blueprint là artifact
  TÙY CHỌN wire theo mẫu _check_curriculum/_check_exam_results (chỉ kiểm khi file tồn tại) → topic không
  blueprint / blueprint draft giữ hành vi cũ (P9 backward-compat).
key_decisions:
  - "Wave 2 schema: model Blueprint+MandatoryArea (strict, id ^ma-\\S+$, status Literal draft|approved) + CurriculumPoint.area_refs:list[str]=[] (additive, default [] → curriculum cũ parse nguyên vẹn). Đăng ký blueprint vào _SCHEMA_MODELS + _SYSTEM_DATA_NAMES (INV-18) + schemas/blueprint.schema.md + drift-guard MODEL_BY_SCHEMA. area_refs là field NESTED → drift-guard schema (top-level) KHÔNG kiểm → nói thẳng ở prose + teeth thật đến từ Blueprint_Validator (không giả vờ RED)."
  - "Wave 3/4 Blueprint_Validator (_check_blueprint, wire cuối _validate_topic): E-BP-DUP-ID/ORDER/EMPTY-TITLE/REF-BROKEN (cấu trúc, áp cả draft) + E-BP-AREA-REF-BROKEN (ánh xạ point→area tồn tại INV-03, áp cả draft) + E-BP-AREA-UNCOVERED/POINT-OUTSIDE (phủ, teachable-gated — DEC-075). Sai schema/status → E-SCHEMA sẵn có (bỏ mã trùng, tiền lệ DEC-058). 7 mã, drift-guard validation_rules 2 chiều."
  - "Wave 5 lệnh /blueprint đa-chế-độ qua cờ (--edit/--approve/--amend --confirm) — MỘT tên lệnh, drift-guard bất biến (tiền lệ DEC-063/069). Build gán ma-NNN order 1..N; edit/amend GIỮ id ổn định (R1.2) qua _parse_areas_json(existing_ids): item có 'id' phải trỏ area cũ, item không id → ma-{max+1} duy nhất. approve draft→approved transaction-FULL gate; amend approved BẮT BUỘC --confirm (R4.3/4.4). Đăng ký CLI_COMMANDS/parser/dispatch/commands.md/router đồng bộ (3 drift-guard xanh)."
  - "Wave 6 curriculum mang area_refs (cmd_curriculum + cmd_curriculum_insert đọc area_refs JSON, default []). Xác minh GỐC: cmd_next_lesson set cp['lesson_id'] IN-PLACE trên cur_raw → area_refs bảo toàn (không rebuild point làm mất field)."
  - "Wave 7 E2E: blueprint(draft)→edit→approve→curriculum(phủ đủ)→validate PASS→next-lesson; ca âm thiếu phủ→ABORT E-BP-AREA-UNCOVERED; amend-thêm-mandatory-mới khi teachable→ABORT (guarantee giữ vững); backward-compat topic không blueprint."
  - "Wave 8 áp CR-0011..0014 pending→approved + changelog + HUONG_DAN (/blueprint) + spec §3.6 v2.7→v2.8 + START_HERE v2.8. _system/VERSION GIỮ =1 (schema dữ liệu additive, không migration — tách semver tài liệu vs schema, DEV-004/006)."
  - "An toàn dài hạn: khởi tạo git ở thư mục CHA (bao spec + đơn vị) + .gitignore (venv/cache) + commit baseline xanh TRƯỚC khi sửa sâu → mọi thay đổi diff/revert được (thư mục trước đó KHÔNG phải git repo)."
evidence:
  - "ran-test: full suite 499 passed (458 baseline + 41: 1 schema + 9 bp-structural + 6 bp-coverage + 15 lệnh + 5 area_refs + 4 E2E - 1 gộp/đổi tên); ran-command: validate --scope full pass:true errors:[] warnings:[] sau mỗi wave; selfcheck NGUYÊN VẸN."
  - "read-source: _check_curriculum/_check_exam_results (mẫu artifact tùy chọn), cmd_curriculum/insert (mẫu transaction-FULL), cmd_next_lesson (in-place lesson_id), test_schemas_consistency/commands_registry/router/huong_dan (drift-guard)."
  - "ran-command teeth-probe: vô hiệu block coverage → 2-3 test coverage chuyển RED, phần còn lại xanh → chứng minh check có răng thật."
verified: true
method: ran-test
```

## DEC-075 — Root-fix: coverage (phủ blueprint) là CỔNG của teachable, KHÔNG phải bất biến vault độc lập

```yaml
id: DEC-075
type: decision
date: 2026-07-07
title: "E-BP-AREA-UNCOVERED / E-BP-POINT-OUTSIDE chỉ fire khi blueprint approved VÀ curriculum tồn tại VÀ curriculum.teachable==true — KHÔNG phải mọi lúc approved. Phát hiện khi truy vết luồng approve TRƯỚC khi viết lệnh"
spec_ref: "spec mandatory-curriculum-framework R3.3 (còn mảng chưa phủ → GIỮ curriculum chưa-teachable), R3.4, R4.2 (approve), R5.4 (backward-compat); tiền lệ DEC-073 (check optional-artifact làm brick vault qua transaction-abort cascade)"
summary: >
  Trong lúc chuẩn bị viết cmd_blueprint_approve, truy vết luồng: approve ghi status=approved rồi
  transaction-FULL validate. Nếu coverage gate CHỈ theo status=='approved' thì: (a) approved-blueprint-CHƯA-
  có-curriculum → E-BP-AREA-UNCOVERED → validate FULL FAIL → BRICK VAULT (mọi transaction sau abort — đúng
  lớp bug DEC-073); (b) chặn OAN luồng tự nhiên blueprint→approve→dựng-curriculum (chicken-egg, không bao
  giờ approve được). Đọc gộp R3.3 'còn mảng bắt buộc chưa phủ → GIỮ curriculum chưa-teachable' cho
  contrapositive: teachable ⟹ phủ đủ. Vậy phủ là CỔNG của teachable, không phải bất biến vault standalone.
key_decisions:
  - "Gate đúng: if bp.status=='approved' and cur is not None and cur.teachable → mới ép E-BP-AREA-UNCOVERED/POINT-OUTSIDE. Ma trận: (no curriculum)→PASS; (teachable=false draft-curriculum)→PASS; (teachable=true thiếu phủ)→FAIL; (teachable=true phủ đủ)→PASS. Draft blueprint: không bao giờ ép (R5.4)."
  - "E-BP-AREA-REF-BROKEN (toàn vẹn tham chiếu INV-03) VẪN ungated (fire bất kể draft/approved/teachable) — ref gãy luôn là lỗi, khác với 'chưa phủ đủ' (điều kiện chưa-sẵn-sàng-dạy)."
  - "cmd_curriculum đặt teachable=True lúc dựng → nếu thiếu phủ dưới approved-blueprint, transaction-FULL abort → teachable=true KHÔNG tồn tại bền → R3.3/R3.4 thỏa tự nhiên qua cơ chế transaction (không cần cổng riêng)."
  - "Guarantee kiểm-được: amend approved thêm mandatory-area mới khi đang có curriculum teachable phủ-đủ-cũ → coverage vỡ → transaction abort/rollback → không thể có curriculum teachable dưới approved-blueprint mà thiếu phủ (test_e2e_amend_add_mandatory_breaks_coverage)."
  - "code(test sửa)-lệch-thiết-kế-đúng → KHÔNG cần CR (tiền lệ DEC-029/072). Sửa cùng wave trước khi commit code sai ra ngoài."
evidence:
  - "read-source: truy vết cmd_blueprint_approve → _run_tx → validate_staged (FULL) → _check_blueprint; xác nhận cmd_curriculum đặt teachable=True (session.py)."
  - "ran-command teeth-probe: gate=False → test_approved_uncovered_area_fails + test_approved_point_outside_fails RED (2 fail), 5 test còn lại PASS → teeth xác nhận đúng 2 mã coverage."
  - "ran-test: test_blueprint_coverage 7 test (gồm test_approved_not_teachable_no_coverage_error + test_approved_no_curriculum_passes mã hoá ma trận) PASSED; full suite 499 passed; validate --scope full PASS."
verified: true
method: ran-test
```


## DEC-076 — CR-0015 approved+áp: /curriculum --set-area-refs (retrofit area_refs) — giải ngõ cụt NOTE-039

```yaml
id: DEC-076
type: decision
date: 2026-07-08
title: "Thêm chế độ cờ /curriculum --set-area-refs <cp-id> --area-refs <json>: gắn/sửa area_refs cho Curriculum_Point ĐÃ CÓ (retrofit) — mở luồng curriculum-first→áp-khung, giải ngõ cụt NOTE-039. Phương án B của TRD-008 (owner duyệt). SPEC-first (CR-0015 design→valid→approve) rồi RED-first"
spec_ref: "CR-0015 approved; NOTE-039 (ngõ cụt); TRD-008 (owner chọn B); DEC-069 (tiền lệ chế độ cờ --insert-at), DEC-075 (phủ là cổng teachable), DEC-071 (_load_curriculum_validated→E-SCHEMA sạch), CR-0012 (area_refs schema)"
summary: >
  Owner duyệt phương án B (TRD-008): bổ sung năng lực gắn/sửa area_refs cho điểm học ĐÃ CÓ (trước KHÔNG có —
  cmd_curriculum từ chối nếu tồn tại; insert chỉ thêm point mới). Backend cmd_curriculum_set_area_refs: tìm
  point theo id → REPLACE area_refs → transaction-FULL (gate E-CURR-* + E-BP-*). Chế độ CỜ
  /curriculum --set-area-refs <cp-id> --area-refs <json> — KHÔNG thêm tên lệnh (drift-guard bất biến, tiền lệ
  DEC-069). GIẢI ngõ cụt NOTE-039: retrofit chạy DƯỚI blueprint draft (cổng phủ TẮT — DEC-075) từng điểm một,
  rồi /blueprint --approve → phủ đủ → approved. Luồng curriculum-first→áp-khung nay thông suốt.
key_decisions:
  - "Bề mặt: chế độ CỜ, KHÔNG tên lệnh mới → drift-guard registry/router/huong_dan bất biến (DEC-069)."
  - "Ngữ nghĩa REPLACE (đặt lại cả list; [] = xoá ánh xạ) KHÔNG append — tất định, idempotent, cho phép sửa/xoá."
  - "transaction-FULL (không LIGHT): area_refs tác động E-BP-AREA-REF-BROKEN + coverage → phải qua _check_blueprint (full-validate). LIGHT sẽ không gate được."
  - "KHÔNG đổi schema (area_refs có sẵn CR-0012), KHÔNG mã lỗi mới, KHÔNG bump _system/VERSION (=1)."
  - "point không tồn tại / curriculum thiếu / JSON sai (không list / phần tử non-str) → SessionError, KHÔNG ghi bộ phận; curriculum.md sửa-tay-hỏng → E-SCHEMA sạch (DEC-071)."
edge_declared: >
  Nếu blueprint ĐÃ approved + curriculum teachable + chưa phủ (CHỈ tới được bằng sửa-tay file, vì approve qua
  lệnh đã đòi phủ đủ) → validate FULL đang FAIL → mọi transaction (kể cả set-area-refs) ABORT tới khi phủ đủ.
  Cách đúng: retrofit dưới blueprint DRAFT (luồng chuẩn); trạng thái sửa-tay-hỏng thì đưa blueprint về draft
  trước rồi retrofit. KHÔNG phải bug (validator giữ đúng bất biến).
verified: true
method: ran-test
tests: >
  RED-first 7 unit (validator/tests/phase10/test_session_curriculum_setarearefs.py: updates_point /
  replace_not_append / empty_clears / unknown_point / bad_json / no_curriculum / corrupt→E-SCHEMA) —
  xác nhận RED (AttributeError) trước, GREEN sau hiện thực. + 1 E2E
  (validator/tests/phase12/test_e2e_retrofit_blueprint.py): curriculum-first teachable KHÔNG area_refs →
  blueprint draft → approve FAIL (E-BP-POINT-OUTSIDE/AREA-UNCOVERED) → 2× set-area-refs → approve PASS →
  validate --scope full PASS → next-lesson PASS. CHỨNG MINH ngõ cụt NOTE-039 được giải.
  505→513 passed (+8); validate --scope full pass:true; selfcheck NGUYÊN VẸN.
status: active
reversible: >
  Gỡ backend cmd_curriculum_set_area_refs + 2 cờ parser (--set-area-refs/--area-refs) + nhánh dispatch + 2 file
  test + revert doc (commands.md/HUONG_DAN.md/spec §3.6+§11A/changelog) + move cr-0015 approved→rejected. Field
  area_refs GIỮ (CR-0012 độc lập). Backward-compat tuyệt đối: mọi luồng /curriculum cũ không đổi.
```


## DEC-077 — Hardening HANDOFF_TEST cho vòng khung bắt buộc v2.8 (A3 blueprint + retrofit) — để AI KHÁC xác minh đầy đủ

```yaml
id: DEC-077
type: decision
date: 2026-07-08
title: "Mở rộng HANDOFF_TEST.md: thêm Phần A3 (blueprint draft → /curriculum --set-area-refs retrofit → --approve, CHỨNG MINH ngõ cụt NOTE-039 giải) + rubric R4c + /blueprint vào khối commands máy-đọc + drift-guard test_handoff_covers_blueprint_cycle. Để một AI KHÁC (cross-AI) xác minh ĐẦY ĐỦ hệ hiện tại (v2.8), không chỉ v2.7 (A2)"
spec_ref: "DEC-070 (tiền lệ hardening HANDOFF thêm A2 v2.7); DEC-074/075/076 (blueprint + retrofit); NOTE-035/036 (cross-AI handoff đã đạt); yêu cầu owner 'cần 1 AI khác xác định'"
summary: >
  HANDOFF_TEST.md (prompt tự-chứa cho AI KHÁC tiếp quản + chấm rubric) trước chỉ phủ A1 (lõi) + A2 (giáo
  trình v2.7). Blueprint (v2.8) + retrofit (CR-0015/DEC-076) KHÔNG có trong bài → AI khác chạy sẽ 'ĐẠT
  handoff' mà KHÔNG kiểm phần mới (đúng lớp lỗ hổng DEC-073: nghiệm thu bỏ sót tầng chưa phủ). Mở rộng:
  thêm A3 (dựng blueprint draft → retrofit area_refs cho các điểm curriculum đã có → approve; nếu chưa phủ
  đủ → E-BP-AREA-UNCOVERED/POINT-OUTSIDE, đúng cổng phủ) — CHÍNH kịch bản curriculum-first→áp-khung giải
  NOTE-039. Cập nhật đồng bộ: R4c (rubric), khối commands máy-đọc (+/blueprint), self-report (+dòng A3),
  tiêu chí/kết luận Phần A (validate PASS bước 10 VÀ 14; R1–R4c).
key_decisions:
  - "Thuần TÀI LIỆU + 1 drift-guard (test_handoff_covers_blueprint_cycle: /blueprint ∈ khối handoff) — KHÔNG cần CR (tiền lệ DEC-070; HANDOFF_TEST là artifact test, không phải registry/schema/spec)."
  - "A3 dùng đúng luồng blueprint-first-KHÔNG-được (curriculum có trước) → retrofit → approve, để cross-AI kiểm CHÍNH năng lực mới DEC-076 (không phải happy-path blueprint-first)."
  - "drift-guard đảm bảo: /blueprint (dùng trong A3) phải TỒN TẠI trong commands.md → chống handoff nhắc lệnh bịa (NOTE-031)."
verified: true
method: ran-test
tests: "RED-first: test_handoff_covers_blueprint_cycle FAIL (khối handoff thiếu /blueprint) → thêm /blueprint + A3 → GREEN. Full suite 513→514 passed (+1 drift-guard); validate --scope full PASS. Cross-AI test THẬT vẫn chờ owner chạy AI khác (ranh giới trung thực — tôi KHÔNG tự chấm thay AI độc lập)."
status: active
reversible: "Revert A3/R4c/self-report/commands trong HANDOFF_TEST.md + gỡ test_handoff_covers_blueprint_cycle. Không đụng code hệ."
```


## DEC-078 — Anti-drift GỐC: drift-guard cho CHÍNH nhật ký decisions/ (canh người-gác)

```yaml
id: DEC-078
type: decision
date: 2026-07-08
title: "Thêm test_decision_journal_consistency.py: ép song ánh index.yaml ↔ các file .md (id trong index ⇔ heading '## <id>' trong .md), id duy nhất, đặt đúng file theo tiền tố (DEC/DEV/TRD/NOTE), type khớp tiền tố + đủ field. Bịt lỗ hổng chống-drift GỐC: nhật ký decisions/ là artifact máy-đọc DUY NHẤT trước đây KHÔNG có drift-guard"
spec_ref: "yêu cầu owner 'cần 1 cách CỰC MẠNH tránh drift'; DEC-005 (tiền lệ drift-guard docs↔code); spec §17 anti-drift; phát hiện thực nghiệm NOTE-038 (drift thật của nhật ký)"
summary: >
  Điều tra: MỌI artifact máy-đọc khác đã có drift-guard (schemas↔models test_schemas_consistency; rules↔code
  test_rules_consistency; router↔registry test_router_prompt_consistency; claims↔code test_claim_rules_consistency;
  anti_drift↔error_codes test_anti_drift_memory_consistency; registry/huong_dan/handoff/pilot_runbook). DUY NHẤT
  nhật ký decisions/ (index.yaml ↔ .md) KHÔNG được canh. Mà nhật ký là XƯƠNG SỐNG chống-drift (START_HERE bước
  3 bắt mọi AI phiên sau đọc để không lặp lỗi / không quyết lại điều đã chốt). Nếu nó tự trôi → cả chiến lược
  chống-drift mất tin cậy. Phiên này gặp drift THẬT: NOTE-038 có dòng index nhưng THIẾU khối notes.md, không
  test nào bắt (phải sửa tay). ⇒ "Canh chính người-gác" là bước chống-drift MẠNH GỐC nhất còn thiếu.
why_strongest (lý do chọn — chính xác): >
  KHÔNG fix ngọn (không đi vá từng entry lệch tay). Fix GỐC: cơ chế tất định bắt MỌI lệch index↔.md tương lai,
  hai chiều (orphan ở index HOẶC ở .md đều đỏ). Vì nhật ký là nơi mọi phiên sau tin để tránh drift, guard nó =
  bảo vệ nền tảng của toàn bộ anti-drift. Mọi thứ khác đã có guard → đây đúng là mảnh còn thiếu duy nhất.
key_decisions:
  - "Là TEST drift-guard (như DEC-005/077) → KHÔNG cần CR (validate-the-validator §10.6, không đổi registry/schema/spec)."
  - "Song ánh 2 chiều (bắt cả 'index thừa' lẫn '.md thừa') — đúng lớp NOTE-038."
  - "Kiểm thêm: id duy nhất (README: id vĩnh viễn không tái dùng), đặt đúng file theo tiền tố, type khớp tiền tố, entry đủ field bắt buộc."
verified: true
method: ran-test
tests: "5 test (index_valid_fields / no_duplicate_ids / index_md_bijection / prefix_placed_right_file / type_matches_prefix). Teeth-probe: chèn tạm DEC-999 (index, không .md) → test_index_md_bijection ĐỎ đúng ('id CÓ trong index nhưng THIẾU khối .md: DEC-999') → gỡ → xanh lại. Full suite 514→519 passed (+5); validate --scope full PASS."
status: active
reversible: "Gỡ file test. Không đụng dữ liệu/nhật ký (chỉ thêm kiểm)."
```

---

## DEC-079 — Lưu tài liệu chiến lược NGOÀI cây governed `_system` (PRODUCT_THESIS + landscape)

```yaml
id: DEC-079
type: decision
date: 2026-07-09
title: "Đặt PRODUCT_THESIS.md ở gốc dự án + similar_systems_landscape.md trong repo_evaluations/ (role prior_art_comparison); KHÔNG guard prose bằng test"
spec_ref: "none (spec silent — không nói về tài liệu chiến lược/đối-thủ)"
summary: >
  Phiên này (theo yêu cầu owner 'xem repo tương tự + có nên đập đi xây lại') tạo 2 tài liệu:
  (a) PRODUCT_THESIS.md ở GỐC dự án (cạnh PROMPT_LEARNING_SYSTEM.md + end.md); (b)
  _system/repo_lab/repo_evaluations/similar_systems_landscape.md — role mới 'prior_art_comparison'
  (khác fsrs.md role 'install_dependency'). KHÔNG thêm test drift-guard cho 2 file này.
rationale: >
  (1) Tài liệu prose/chiến lược KHÔNG phải artifact máy-đọc mà code phụ thuộc → guard bằng test =
  ceremony, trái R10.1 + tiền lệ DEC-058/NOTE-014/NOTE-024 (không thêm test vặt). (2) PRODUCT_THESIS đặt
  ở gốc để dễ thấy + KHÔNG nằm trong _system → không rủi ro INV-18/drift-guard. (3) repo_evaluations/ vốn
  là nơi chứa phiếu đánh giá (fsrs.md) → landscape đặt cùng chỗ đúng vai. Đã VERIFY không test nào canh
  repo_lab (grep) nên thêm file an toàn, không đổi số test.
alternatives:
  - "Đặt trong _system/decisions/ — BỎ: lẫn tài liệu chiến lược với nhật ký máy-đọc; rủi ro coupling."
  - "Tạo thư mục governed mới + drift-guard — BỎ: ceremony, chưa có nhu cầu máy-đọc (R10.1)."
evidence:
  - "PRODUCT_THESIS.md (gốc dự án) — tồn tại (tạo phiên này)"
  - "_system/repo_lab/repo_evaluations/similar_systems_landscape.md — tồn tại (tạo phiên này)"
  - "grep 'repo_eval|repo_lab' trong **/tests/**/*.py → No matches (repo_lab KHÔNG được guard)"
verified: true
method: read-source
status: active
reversible: "Xoá 2 file; không ảnh hưởng kernel/validator/test."
```

---

## DEC-080 — Chống-drift GỐC (sound): referential-integrity cho nhật ký; TỪ CHỐI liveness token evidence (đo ~19% false-positive)

```yaml
id: DEC-080
type: decision
date: 2026-07-09
title: "Thêm test_supersede_pointers_resolve (supersede pointers phải trỏ id thật) vào guard nhật ký; từ chối kiểm liveness token evidence vì đo được ~19% false-positive"
spec_ref: "none (drift-guard test — tiền lệ DEC-005/DEC-078, additive, KHÔNG cần CR)"
summary: >
  Owner yêu cầu 'cách CỰC MẠNH chống drift'. Design-first + valid-thiết-kế-bằng-đo-thực-nghiệm rồi mới
  triển khai. Điều tra 2 hướng cho hở evidence-liveness của nhật ký (NOTE-042/TRD-010):
  (B) kiểm mọi token path/test trong 'evidence' còn tồn tại — ĐO trên dữ liệu thật: 28/149 token
  ASSERT-FAIL (~19%) trên entry HỢP LỆ, do (a) path một phần ('phase10/test_x.py'), (b) ví dụ minh hoạ
  ('alpha/a.py','zeta/z.py'), (c) ellipsis ('cr-0009-...md'). ⇒ B UNSOUND (đỏ oan / buộc viết lại lịch
  sử, trái append-only). TỪ CHỐI B. Thay bằng deepening SOUND: mở rộng test_decision_journal_consistency.py
  thêm test_supersede_pointers_resolve — mọi superseded_by/superseded_part_by/supersedes_part_of trong
  khối yaml .md phải trỏ id THẬT (tập id đóng, cấu trúc cố định ⇒ 0 false-positive by construction).
rationale: >
  Fix BẢN CHẤT không fix ngọn: liveness-token là fix-ngọn unsound (đo được false-positive cao trên free-
  text); referential-integrity là root sound (id có cấu trúc + tập đóng → tất định, không đỏ oan). Bổ sung
  tự nhiên cho bijection DEC-078 (khép nốt toàn-vẹn tham chiếu NỘI BỘ nhật ký). Thêm test = additive theo
  tiền lệ DEC-005/DEC-078 → không cần CR. Không over-reach: KHÔNG ép rewrite 133 entry cũ, KHÔNG guard prose.
alternatives:
  - "B (TRD-010): kiểm liveness mọi token file/test trong evidence — TỪ CHỐI (đo 28/149 ~19% false-positive; xem _scan_evidence)."
  - "evidence_refs structured opt-in (tách ref máy-kiểm khỏi prose) — HOÃN: hữu ích, zero-FP, nhưng thêm gánh field; để owner cân nhắc khi cần liveness thật."
  - "A: guard chéo tài liệu chiến lược (PRODUCT_THESIS↔landscape) — loại (prose, ceremony)."
evidence:
  - "read-source: validator/tests/phase10/test_decision_journal_consistency.py — thêm _supersede_pointers() + test_supersede_pointers_resolve() + docstring KIỂM #5"
  - "ran-command (py -3 harness nạp module trực tiếp — máy này KHÔNG có .venv/pytest): 6/6 check GREEN + teeth-probe inject 'DEC-99999' → AssertionError (bắt dangling)"
  - "ran-command (scan evidence, đã xoá script): 297 token; ASSERT-OK 121; ASSERT-FAIL 28 (~19% trên 149 checkable); SKIP-ambiguous 148 → chứng minh liveness-token UNSOUND"
  - "ran-command (scan xref, đã xoá script): 2 supersede pointer (DEC-003→DEC-001; DEV-005→DEC-016) đều resolve → guard mới xanh + sound"
verified: true
method: ran-command
status: active
resolves: "NOTE-042 (open-question → resolved); TRD-010 (chọn giải pháp sound, từ chối B)"
reversible: "Gỡ _supersede_pointers + test_supersede_pointers_resolve + docstring #5 → guard quay về DEC-078 structure-only. Không đụng dữ liệu/kernel."
```


## DEC-081 — R1 giải: orchestrator author nội-dung-dạy + kernel `cmd_done` gác; SỬA GỐC R-ORCH-2 (trust model)

```yaml
id: DEC-081
type: decision
date: 2026-07-09
title: "Phase 1 R1 (spec-review gate): xác minh qua ĐỌC CODE THẬT — orchestrator author lesson.md (transcript+evidence) + lesson_state trực tiếp rồi gọi kernel cmd_done (FULL-validate) làm CỔNG; KHÔNG cần đổi kernel. Đồng thời SỬA GỐC R-ORCH-2 của SPEC_PHASE1 (viết sai: 'không bao giờ ghi vault trực tiếp' — mâu thuẫn thiết kế thật)"
spec_ref: "SPEC_PHASE1_ORCHESTRATOR §2/§6; test_e2e_curriculum._make_lesson_learned; validate._check_gate_and_evidence (INV-07/22/22b); session.cmd_done docstring 'Driver KHÔNG sửa nội dung lesson — việc AI trong phiên'"
finding_R1 (đọc code, không đoán): >
  KHÔNG có lệnh kernel nào ghi NỘI DUNG DẠY (## Sessions transcript + #### Evidence). Thiết kế hệ CHỦ ĐÍCH
  để AI (nay = orchestrator) tự author lesson.md, còn cmd_done FULL-validate là CỔNG: gate learned (INV-07
  _GATE) + evidence tồn tại (E-ASSESS-NOEVIDENCE) + quote verbatim⊆transcript (E-ASSESS-FAKEQUOTE, validate.py
  _check_gate_and_evidence dùng normalize_for_match + substring). Bằng chứng: test _make_lesson_learned author
  lesson_state(status=learned+mastery) + lesson.md(Sessions+transcript+1 evidence/trục) TRỰC TIẾP → cmd_done
  commit + validate PASS, KHÔNG đổi kernel. ⇒ R1 = orchestrator làm y vậy được, KHÔNG đổi kernel (không CR).
root_fix_R-ORCH-2 (bản chất, không ngọn): >
  R-ORCH-2 ban đầu ('orchestrator SHALL KHÔNG mở/ghi bất kỳ file nào trong learning_vault trực tiếp') MÂU
  THUẪN thiết kế: không thể dạy mà không author nội dung lesson. Reformulate ĐÚNG trust-model:
  (a) orchestrator ĐƯỢC author NỘI DUNG DẠY (transcript+evidence trong lesson.md) — đó là vai AI hợp lệ;
  (b) MỌI CHUYỂN-TRẠNG-THÁI (learned/done/advance) CHỈ qua lệnh kernel (cmd_done...), KHÔNG tự set
      lesson_state.status=learned rồi bỏ qua cmd_done;
  (c) phán quyết 'learned' CHỈ hợp lệ khi cmd_done COMMIT (FULL-validate PASS) — evidence bịa/ungated bị
      kernel chặn (E-ASSESS-FAKEQUOTE/E-GATE-FAIL). Kernel là cổng chân-lý, không phải thiện chí orchestrator.
  R-ORCH-3 (verbatim) = defense-in-depth: orchestrator kiểm verbatim để FAIL SỚM, kernel kiểm lại (chốt).
implication: >
  Phase 1 KHÔNG đổi kernel (đúng moat). Điểm yếu cố hữu (author nội dung KHÔNG transactional — write rồi mới
  validate; nếu validate fail thì lesson.md 'bẩn' nằm lại tới khi sửa) là HÀNH VI HỆ HIỆN TẠI, ghi nhận; cải
  tiến 'ghi nội dung dạy transactional' là kernel-change tương lai qua CR §12, NGOÀI scope Phase 1.
verified: true
method: read-source
status: active
reversible: "Chỉ sửa prose SPEC + ghi nhận; chưa code."
```
