# Validation Rules — Mã lỗi & mức kiểm (spec 10.1–10.8)

Nguồn tham chiếu mã lỗi. Bảng máy-đọc `error_codes` được test giữ **khớp CHÍNH XÁC** tập mã mà code thật
phát ra (`validate.py` + `transaction.py` + `session.py`) — thêm/bớt mã ở code mà quên cập nhật đây → test đỏ.

Hai mức (spec 10.8): **LIGHT** (trong phiên: schema/ngày/ref/cú pháp file vừa đụng) — **FULL** (`/review` `/done`
`/forget`: toàn bộ INV-01..26 + replay + view + diff-invariant INV-06/11). AI **cấm** tự tuyên bố PASS nếu chưa
có output validator thật.

## Cấu trúc / schema (LIGHT + FULL)
| Mã | Ý nghĩa |
|----|---------|
| `E-SCHEMA` | Front-matter sai schema/field/kiểu (pydantic) hoặc thiếu |
| `E-SCHEMA-YAML` | YAML front-matter hỏng |
| `E-SCHEMA-UNKNOWN` | `schema:` không nhận diện |
| `E-SCHEMA-CONFIG` | Thiếu/hỏng `fsrs_config.yaml` hoặc `_system/VERSION` |
| `E-SCHEMA-OUTDATED` | version vault/config cũ hơn hệ thống (INV-19/24) — cần migration |
| `E-SCHEMA-AHEAD` | `vault.schema_version` mới hơn `_system/VERSION` (INV-19) |
| `E-LESSON-HEADING` | `lesson.md` thiếu heading bắt buộc |
| `E-QUESTION` | Lỗi `#### Question <qid>` (trùng/sai) |
| `E-EVIDENCE` | Lỗi cú pháp evidence block (LIGHT) |

## Tham chiếu / ID / index (FULL)
| Mã | Ý nghĩa |
|----|---------|
| `E-REF-BROKEN` | Tham chiếu (prompt_ref/prerequisites/current_lesson) trỏ thứ không tồn tại (INV-03) |
| `E-ID-DUP` | Trùng `rv-*`/`gap-*` trong lesson/topic (INV-04) |
| `E-ID-PATH` | `lesson_id` != đường dẫn (INV-02) |
| `E-INDEX-MISMATCH` | Index/status/current_lesson lệch nguồn (INV-25) |
| `E-REVIEW-DUP` | Trùng `prompt_ref` (INV-10) |

## FSRS / năng lực (FULL)
| Mã | Ý nghĩa |
|----|---------|
| `E-REVIEW-MISCALC` | Replay log không khớp card (INV-08) |
| `E-STATE-DERIVED` | `mastery_state` != `derive_mastery` (INV-21) |
| `E-GATE-FAIL` | `learned` khi chưa qua cổng (INV-07) |
| `E-ASSESS-NOEVIDENCE` | Trục đạt ngưỡng nhưng thiếu evidence (INV-22) |
| `E-ASSESS-FAKEQUOTE` | `quote` không phải chuỗi con transcript (INV-22b) |
| `E-REVIEW-BADGRADE` | grade ngoài 0..3 (driver) |

## Claim / nguồn (FULL)
| Mã | Ý nghĩa |
|----|---------|
| `E-CLAIM-UNCLASSED` | Claim thiếu/không hợp lệ id/class/status/text (INV-15) |
| `E-CLAIM-DRAFTREASON` | Claim draft thiếu `draft_reason` (INV-15) |
| `E-CLAIM-WEAKBASE` | C confirmed thiếu/tiền đề không A/B confirmed (INV-14) |
| `E-CLAIM-NOSRC` | B confirmed thiếu anchor nguồn confirmed (INV-12) |
| `E-CLAIM-LOC` | Claim ngoài `## Claims` (INV-23) |
| `E-SRC-RAWUSED` | Dùng nguồn raw/rejected làm anchor (INV-13) |
| `E-DRAFT-IN-MAP` | Draft trong Knowledge Map hoặc `has_draft_knowledge` sai (INV-26) |

## View (FULL)
| Mã | Ý nghĩa |
|----|---------|
| `E-VIEW-MISMATCH` | Nội dung view khác object sinh lại (INV-09) |
| `E-VIEW-STALE` | `generated_from_hash` lệch nguồn (INV-09) |

## Portability / tách gốc (FULL)
| Mã | Ý nghĩa |
|----|---------|
| `E-PORT-ABSPATH` | Đường dẫn tuyệt đối trong vault (INV-16) |
| `E-MIX-CODE` | Code/dependency/repo trong `learning_vault/` (INV-17) |
| `E-MIX-DATA` | Dữ liệu học trong `_system/` (INV-18) |
| `E-IO-ENCODING` | File text không đọc được bằng UTF-8 rõ ràng (§19; báo sạch, không crash validator) |

## Curriculum / giáo trình (FULL — tính năng curriculum-driven-learning, Task 3)
| Mã | Ý nghĩa |
|----|---------|
| `E-CURR-DUP-ID` | Hai `Curriculum_Point` trùng `id` trong `curriculum.md` (ngữ nghĩa, model không bắt) |
| `E-CURR-ORDER` | `order` các point không phải hoán vị liên tục 1..N (trùng/hở) |
| `E-CURR-EMPTY-OBJECTIVE` | `Curriculum_Point.objective` rỗng (chỉ khoảng trắng) |
| `E-CURR-POINTER` | `current_point` trỏ `Curriculum_Point` không tồn tại (dangling, INV-03) |
| `E-CURR-LESSON-LINK` | `Curriculum_Point.lesson_id` trỏ lesson không có thật trên đĩa (INV-25) |
| `E-CURR-REF-BROKEN` | `Curriculum_Point.source_refs` trỏ file `reference/` không tồn tại |
| `E-EXAM-REF-BROKEN` | Bản ghi chấm `exam_results.md` trỏ bài nộp (`ref`) hoặc `target` (topic/Curriculum_Point) không tồn tại |

## Transaction (ghi an toàn, spec 10.3/10.3a)
| Mã | Ý nghĩa |
|----|---------|
| `E-STALE-CONTEXT` | File đổi sau khi đọc context, trước BEGIN (OCC mốc 1) |
| `E-CONCURRENT-EDIT` | File đích bị sửa trong lúc tx chạy (OCC mốc 2) |
| `E-TX-PARTIAL` | Transaction dở/không recovery được — chặn ghi mới |
| `E-REVIEW-LOST` | Review item in_review/need_redo biến mất không tombstone (INV-11) |
| `E-STATE-ILLEGAL` | Chuyển status lesson không hợp lệ (INV-06) |

## Driver / CLI (session.py)
| Mã | Ý nghĩa |
|----|---------|
| `E-ARG` | Tham số CLI sai (vd `--at` naive) |
| `E-DRIVER` | Lỗi tầng driver (vd item lạ, `/forget` chưa xác nhận) |

### error_codes (máy đọc)

```yaml
error_codes:
  - E-SCHEMA
  - E-SCHEMA-YAML
  - E-SCHEMA-UNKNOWN
  - E-SCHEMA-CONFIG
  - E-SCHEMA-OUTDATED
  - E-SCHEMA-AHEAD
  - E-LESSON-HEADING
  - E-QUESTION
  - E-EVIDENCE
  - E-REF-BROKEN
  - E-ID-DUP
  - E-ID-PATH
  - E-INDEX-MISMATCH
  - E-REVIEW-DUP
  - E-REVIEW-MISCALC
  - E-STATE-DERIVED
  - E-GATE-FAIL
  - E-ASSESS-NOEVIDENCE
  - E-ASSESS-FAKEQUOTE
  - E-REVIEW-BADGRADE
  - E-CLAIM-UNCLASSED
  - E-CLAIM-DRAFTREASON
  - E-CLAIM-WEAKBASE
  - E-CLAIM-NOSRC
  - E-CLAIM-LOC
  - E-SRC-RAWUSED
  - E-DRAFT-IN-MAP
  - E-VIEW-MISMATCH
  - E-VIEW-STALE
  - E-PORT-ABSPATH
  - E-MIX-CODE
  - E-MIX-DATA
  - E-IO-ENCODING
  - E-CURR-DUP-ID
  - E-CURR-ORDER
  - E-CURR-EMPTY-OBJECTIVE
  - E-CURR-POINTER
  - E-CURR-LESSON-LINK
  - E-CURR-REF-BROKEN
  - E-EXAM-REF-BROKEN
  - E-STALE-CONTEXT
  - E-CONCURRENT-EDIT
  - E-TX-PARTIAL
  - E-REVIEW-LOST
  - E-STATE-ILLEGAL
  - E-ARG
  - E-DRIVER
```
