# Kế Hoạch Triển Khai Theo Phase (TDD)

> Nguồn spec: `../PROMPT_LEARNING_SYSTEM.md` (**v2.6**). Tài liệu này chia việc code thành các **phase độc lập kiểm thử được**.
> Tiến độ (2026-07-02): **P00–P06, P09 (+has_draft_knowledge regen), P07a-core, P07b (FULL semantic — INV-07/12/13/14/15/22/22b/23/26), P08 (+durability parity), P10-driver (session.py `/review` `/done` `/forget` + RECOVER-FIRST + CLI shell, transaction FULL=core+semantic+INV-11 + prune dir rỗng), P04b (AST semantic) xanh. Validator enforce **TRỌN VẸN INV-01..26**. P10-agent: `_system/rules/` (review/teaching/validation) + `commands.md` (registry) + test nhất quán docs↔code/CLI. 216/216 test PASS.**
> Vòng gần nhất thêm **P10-driver** (`session.py`): `cmd_review` (chấm 1 review item → replay đúng convention validator → derive_mastery → regen view topic → transaction-FULL validate-gated commit) + `cmd_done` (clear `open_session` + regen view + FULL-validate + commit trong cùng transaction) + **`_recover_first`** (spec 10.3 BẮT BUỘC: `TX.recover` trước mỗi lệnh, roll-forward tx dở hoặc chặn `E-TX-PARTIAL`). 15 test golden trên COPY vault demo thật (lần đầu-review PASS, tất định byte-identical, lưới-an-toàn ABORT khi card lệch, EReviewBadGrade, OCC `E-STALE-CONTEXT`, /review→/done end-to-end, RECOVER-FIRST roll-forward + chặn-ghi khi partial). Thêm **CLI shell** (`session.py review|done ...`, spec 10.5) in report `validate_staged` nguyên văn + exit-code (0 commit+PASS / 1 không-commit / 2 lỗi tham số); 6 test (in-process + subprocess thật). Kiểm chứng thực nghiệm `safe_dump` tự quote offset round-trip-safe.
> **P10-agent (đang làm):** `_system/rules/review_rules.md` + `teaching_rules.md` + `_system/commands.md` (registry 11A.3). **Test nhất quán docs↔code** (chống trôi single-source-of-truth): `grade_to_rating==FA.MAP_GRADE_TO_RATING`, `learned_gate==validate._GATE`, anchored_examples ≥3/trục (spec 9.5); `commands.md backends` khớp ĐÚNG CLI thật (`session._build_parser` introspect ↔ `CLI_COMMANDS`) + phủ đủ 15 lệnh spec. `validation_rules.md error_codes` == **tập mã E-* thật** quét từ validate/transaction/session (cả hai chiều — chống trôi doc↔code mã lỗi; 39 mã). Refactor `session._build_parser`. Các file `rules/`+`commands.md` không kích INV-18.
> **INV-17/18 (tách bạch hai gốc) — enforced:** INV-17 `E-MIX-CODE` (vault không chứa code/dependency/repo: thư mục cấm + đuôi code + manifest deps; bỏ `_scratch/.tx`); INV-18 `E-MIX-DATA` (`_system` không chứa dữ liệu học: `*_state.md`/lesson/topic md/thư mục `topics/`; loại trừ `validator/.venv/repo_lab/...`). Dùng `os.walk` prune (nhanh, không lội `.venv`). Kiểm chứng chống-bắt-oan: vault + `_system` THẬT sạch. 10 test `phase07a_core/test_inv17_18_mix.py`. **⇒ Toàn bộ INV-01..26 đã enforce.**
> **Fix gốc — INV-06 chưa enforce:** cạnh chuyển status lesson (spec 6.1) chưa kiểm. Là kiểm DIFF (backup→staged) nên cắm vào `Transaction.validate_staged` (như INV-11) qua `_check_status_transitions` + `validate.check_status_transition`/`extract_lesson_status`. Cạnh không hợp lệ (vd `not_started→learned`) → `E-STATE-ILLEGAL`. Item `mastery_state` là hàm thuần → thuộc INV-21, KHÔNG áp cạnh. 6 test `phase08_tx/test_inv06_transitions.py`.
> **Fix gốc — INV-03 bỏ lọt refs:** trước chỉ kiểm `prompt_ref` (+ current_lesson-match qua INV-25), KHÔNG kiểm TỒN TẠI của `prerequisites` và `current_lesson` (vault+topic). Thêm `_collect_all_lesson_ids` + check → `E-REF-BROKEN` khi trỏ lesson không tồn tại. 4 test `phase07a_core/test_inv03_refs.py`.
> **Fix gốc — INV-19 chưa enforce + thiếu `_system/VERSION`:** INV-19 (schema_version ↔ VERSION) là INV mồ côi (không call-site), và `_system/VERSION` không tồn tại. Đã tạo `VERSION=1` + `_check_schema_version` trong `validate_full_core` (vault<system→`E-SCHEMA-OUTDATED`; vault>system→`E-SCHEMA-AHEAD`; thiếu VERSION→`E-SCHEMA-CONFIG`). Dùng SỐ NGUYÊN (nhất quán model + migration vN→vN+1); **spec ghi 'semver major.minor' là dòng tự mâu thuẫn cần dọn** (đã ghi chú trong code). 6 test `phase07a_core/test_inv19_version.py`.
> **Fix gốc — INV-11 chưa cắm điện:** `check_review_not_lost`/`extract_review_states` (chống mất review item in_review/need_redo) trước chỉ là hàm test-unit-lẻ, KHÔNG có call-site ở luồng transaction → `/review` `/done` `/forget` KHÔNG enforce INV-11. Vì là kiểm DIFF (backup↔staged+tombstone) nên không thể nằm trong `validate_full_*`. Đã thêm `Transaction._check_review_preservation` gọi trong `validate_staged` (FULL): so review-state backup↔staged mỗi `lesson_state.md`, item bảo vệ biến mất không tombstone → `E-REVIEW-LOST`. 4 test wiring (`phase08_tx/test_inv11_wired.py`: drop không tombstone → LOST; có tombstone → sạch; item 'new' → sạch; xoá cả file → LOST).
> **Fix gốc — transaction FULL bỏ lọt semantic:** `Transaction.validate_staged(level="full")` trước gọi `validate_full_core` → `/review` `/done` commit mà KHÔNG kiểm INV semantic (07/12../26), trái spec 10.8 (FULL = INV-01..26). Đã chuyển sang `validate_full_semantic`. Test `phase10/test_staged_full_semantic.py`: stage lesson `status=learned` (mastery 0) → `validate_staged('full')` bắt `E-GATE-FAIL`. Demo overlay semantic-clean nên `/review` `/done` vẫn PASS.
> **Durability parity (P08 hardening):** `atomic_write_manifest` fsync manifest nhưng `stage()`/`_apply_commit` trước đây `write_bytes`/`os.replace` KHÔNG fsync data → lỗ 'rename chưa fsync data'. Fix gốc: `_write_bytes_durable` (write→flush→fsync) cho staged + `_fsync_dir` sau replace, đưa dữ liệu commit ngang độ bền manifest. 3 test contract (fsync đúng chỗ; trung thực: không mô phỏng mất-điện thật). Giới hạn Windows: fsync file chạy, fsync thư mục no-op an toàn (đúng như manifest).
> Trước đó: P03 mở rộng (TopicState/view/Sources), P09 (views), P07a-core (INV-02/03/04/08/09/10/21/24/25). Sửa gốc UTF-8 stdout Windows; ranh giới tầng model↔validator (E-ID-DUP/E-REVIEW-DUP).
> Còn lại: P10-agent (prompt/commands/rules — phần văn bản hệ thống), P11 (cache/migration), P12 (pilot). ĐÃ XONG: P07b trọn vẹn (validator semantic đủ INV-01..26), P10-driver, P04b, INV-26 hai chiều (regen sinh `has_draft_knowledge` + validator kiểm, cùng logic). Còn wiring GĐ2 driver `/done` gọi `regen_all(stage='full', claim_texts=...)` khi vault có claim — thuộc P10-agent/GĐ2.
> Mục tiêu: mỗi thứ dựng ra đều **validate chính xác được ngay**, không dồn rủi ro về cuối.

## Nguyên tắc vàng

1. **Test-gate giữa các phase.** Phase N chỉ bắt đầu khi toàn bộ test của phase < N xanh. Không "code trước, test sau".
2. **Rủi ro cao code trước.** FSRS determinism + transaction là hai chỗ dễ vỡ nhất → làm sớm (Phase 1, 8).
3. **Validator tự kiểm bằng golden fixtures** (spec mục 10.6): mỗi INV có ≥1 vault/đơn vị hợp lệ (PASS) và ≥1 hỏng có chủ đích kèm `expected_error_code`.
4. **Thuần hàm trước, I/O sau.** Logic (FSRS, hash, normalize, schema) test bằng unit/golden JSON, không đụng file; I/O và transaction test bằng fault-injection.
5. **Mỗi phase kết bằng lệnh chạy được:** `pytest _system/validator/tests/phaseNN -q` phải xanh.

## Bản đồ phase & phụ thuộc

```text
P00 Bootstrap ─┬─► P01 FSRS adapter ─┐
               ├─► P02 Hash/Normalize ┤
               └─► P03 Schema models ─┼─► P06 LIGHT ─► P07a FULL-core ─► P07b FULL-semantic ─┐
                   P04a AST-core ─────┤                          ▲                   │
                   P05 File IO ───────┘                          │                   │
                                            P09 Views ───────────┘                   │
                                            P08 Transaction ─────────────────────────┼─► P10 Agent layer ─► P12 Pilot E2E
                                                                 P11 Optimize/Migrate ┘
```

## Ánh xạ Giai đoạn MVP (spec A.1)

| Giai đoạn spec                          | Phase trong kế hoạch này            | Kết quả dùng được                                                                   |
| ----------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------- |
| **GĐ1 — Lõi vận hành**         | P00, P01, P02, P03, P04a, P05, P06, P07a, P08, P09 | Học hỏi-đáp + FSRS deterministic + transaction-safe; CHƯA có claim/evidence enforce |
| **GĐ2 — Cưỡng chế toàn vẹn** | P04b, P07b                              | Cổng "đã hiểu" + evidence verbatim + claim B/C/D + view deep-compare                  |
| **GĐ3 — Tối ưu & vỏ**          | P11                                    | Cache replay, validate vi sai, migrations                                                 |
| **Xuyên suốt**                    | P10 (prompt/commands), P12 (pilot)     | Agent chạy`/learn /review /done` thật                                                 |

## Danh sách file phase

| Phase | File                               | Lõi                                                          | INV/mục spec chính      |
| ----- | ---------------------------------- | ------------------------------------------------------------- | ------------------------- |
| P00   | `PHASE_00_BOOTSTRAP.md`          | uv lock + deps + fsrs_config + repo_evaluations               | 16.0A, 8.3, 20.1–2       |
| P01   | `PHASE_01_FSRS_ADAPTER.md`       | fsrs_adapter: replay, quantize, derive_mastery, grade→rating | 8.1–8.5, INV-08, INV-21  |
| P02   | `PHASE_02_HASH_NORMALIZE.md`     | canonical hash + normalize_yaml_object + normalize_for_match  | 4, 9.6, INV-09, INV-22b   |
| P03   | `PHASE_03_SCHEMA_MODELS.md`      | pydantic models strict, card theo-state                       | 5.1–5.5, INV-01/04/05    |
| P04a  | `PHASE_04A_MARKDOWN_AST_CORE.md` | AST core: heading/fence/question/evidence-syntax (GĐ1) | 5.5, 19 |
| P04b  | `PHASE_04B_CLAIMS_SEMANTIC.md`   | AST semantic: claims/evidence/answer-block (GĐ2) | 5.5, INV-22/23/26 |
| P05   | `PHASE_05_FILE_IO.md`            | UTF-8 + discovery + ignore policy                             | 19, INV-16, E-IO-ENCODING |
| P06   | `PHASE_06_VALIDATOR_LIGHT.md`    | validate.py --level light                                     | 10.8                      |
| P07a  | `PHASE_07A_VALIDATOR_FULL_CORE.md`     | FULL-core: cấu trúc + FSRS + view (GĐ1) | 10.2, 10.6, INV-08/09/10/25 |
| P07b  | `PHASE_07B_VALIDATOR_FULL_SEMANTIC.md` | FULL-semantic: claim/evidence/gate (GĐ2) | INV-07/12-15/22/23/26 |
| P08   | `PHASE_08_TRANSACTION.md`        | manifest + OCC + recovery + atomic                            | 10.3, 10.3a/b             |
| P09   | `PHASE_09_VIEWS.md`              | build view + regen wiring                                     | 4, 7, INV-09              |
| P10   | `PHASE_10_AGENT_LAYER.md`        | prompts + commands + rules                                    | 8.1, 9, 11, 11A, 18       |
| P11   | `PHASE_11_OPTIMIZE_MIGRATION.md` | cache + vi sai + migrations                                   | 10.7, 10.9                |
| P12   | `PHASE_12_PILOT_E2E.md`          | topic thật + cross-AI handoff                                | 20.12–13                 |

## Cấu trúc test dùng chung

```text
_system/validator/tests/
  phase01_fsrs/        # golden JSON: input log → expected card
  phase02_hash/        # input object → expected sha256 ; normalize cases
  phase03_schema/      # valid/*.md (PASS) ; invalid/*.md + expected_error.json
  phase04a_ast/        # AST core: heading/fence/question/evidence-syntax fixtures
  phase04b_semantic/   # claims/evidence/answer-block extraction fixtures
  phase06_light/       # vault-lite valid/invalid + expected_error
  phase07a_core/       # FULL-core: valid + 1 vault hỏng / 1 INV cấu trúc/FSRS/view
  phase07b_semantic/   # FULL-semantic: valid + 1 vault hỏng / 1 INV claim/evidence/gate
  phase08_tx/          # fault-injection scenarios
  conftest.py          # helper: run_validator(), load_fixture()
```

Mỗi fixture hỏng đặt tên theo mã lỗi kỳ vọng, ví dụ `invalid/E-REVIEW-MISCALC__drifted_stability.md`.