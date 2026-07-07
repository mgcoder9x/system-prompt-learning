# `_system/` — Bộ máy của AI Learning System

Đây là **tầng công cụ + luật + bộ nhớ** của hệ thống học tập. Dữ liệu người học nằm ở
`../learning_vault/` (markdown thuần, portable). `_system/` KHÔNG chứa dữ liệu học — nó chứa
validator, transaction engine, luật, prompt, và nhật ký quyết định.

> **Phiên AI mới bắt đầu từ đây.** Đọc file này → `decisions/index.yaml` (roll-up quyết định) →
> `PROMPT_LEARNING_SYSTEM.md` (spec gốc v2.6, ở thư mục cha) trước khi thay đổi gì.

## Chạy nhanh (từ thư mục `_system/`)

```text
PY = .venv\Scripts\python           # Windows; đã cài theo requirements.txt (--require-hashes)
PY -m pytest validator\tests -q     # toàn bộ test (kỳ vọng: all passed)
PY validator\validate.py --system . --vault ..\learning_vault --level full --scope full --json
#   Exit 0 = PASS. Thêm --at 2026-07-02T17:00:00+07:00 để audit TÁI LẬP (INV-05 không lệ đồng hồ).
```

## Bản đồ thư mục

| Đường dẫn | Vai trò |
|-----------|---------|
| `validator/` | Lõi: `validate.py` (INV-01..26), `models.py` (schema pydantic), `transaction.py` (ghi an toàn: manifest+OCC+recover-first), `session.py` (driver CLI 11 lệnh), `fsrs_adapter.py` (bọc py-fsrs), `views.py` (regen review_schedule/assessment), `schedule.py`, `canonical.py`, `md_ast.py`, `vault_io.py` + `tests/` |
| `rules/` | 6 file luật (review/teaching/validation/claim/memory/anti_drift) — có khối "máy đọc" drift-guard khớp hằng số code |
| `schemas/` | Mô tả ràng-buộc-test của từng file state (drift-guard vào `models.py`) |
| `prompts/` | 3 prompt vận hành (system/router/system_change) |
| `templates/` | Template topic/lesson (`*.template.md`) |
| `migrations/` | `planner.py` (tính đường di trú) + `executor.py` (chạy migration trong transaction-FULL, rollback) — spec §10.7 |
| `change_requests/` | Quy trình đổi spec/registry §12: `pending/` → `approved/` + `changelog.md` (KHÔNG sửa nóng) |
| `decisions/` | **Nhật ký quyết định xuyên suốt** (đọc `index.yaml` trước): decisions/deviations/tradeoffs/notes |
| `repo_lab/repo_evaluations/` | Phiếu đánh giá dependency (hiện: `fsrs.md`) |
| `commands.md` | Registry 15 lệnh (nguồn sự thật cho router) |
| `fsrs_config.yaml` | Cấu hình FSRS cố định (21 weights, `enable_fuzzing:false`) |
| `VERSION` | schema_version hệ thống (INV-19) |
| `requirements.txt` | Lock dependency + hash (`pip install --require-hashes`) |
| `PILOT_RUNBOOK.md` | Quy trình nghiệm thu bán-thủ-công P12 (người + AI + validator) |
| `selfcheck.py` | **First-run**: `python _system/selfcheck.py` (stdlib, chưa cần venv) — kiểm bản sao nguyên vẹn + bước tiếp theo |
| `audit.py` | **Đánh giá CHỈ-ĐỌC** 'folder đã làm gì': verdict toàn-vẹn + topics/lessons + tiến độ ôn + open_gaps + lịch sử (transaction_log) |
| `../HUONG_DAN.md` | **Hướng dẫn NGƯỜI HỌC** (tiếng Việt, ở gốc `ai-learning-system/`, ngoài `_system/`): dùng hằng ngày, lệnh giữ English, có drift-guard test `commands (máy đọc)`↔`commands.md` |

## Nguyên tắc cốt lõi (bất biến khi làm việc)

- **Validator là chân lý (Class A).** Không tự nhận PASS — chạy `validate.py` và đọc report thật.
- **Ghi qua transaction.** Mọi thay đổi vault đi qua `transaction.py` (backup → validate → commit / rollback).
  Crash giữa chừng → `recover()` roll-forward all-or-nothing (không corrupt).
- **Tất định.** `enable_fuzzing:false`; so lịch ôn theo `due_date` (ngày), KHÔNG `due_at_utc` (F-B, cross-platform).
- **Đổi spec/luật → change request (§12),** không sửa nóng. Anti-drift: khối "máy đọc" trong `rules/` phải khớp code.
- **Không bịa, không suy đoán.** Phân biệt "under-enforce so với spec" (đáng fix) vs "spec cố ý không yêu cầu"
  (không tự thêm — over-reach). Fix nhìn BẢN CHẤT, không fix ngọn.
- **Mọi quyết định tự-ra ghi vào `decisions/`** để kiểm chứng về sau.

## Ranh giới bảo đảm (đọc trước khi hứa)

- **Class A** (validator đảm bảo tuyệt đối): file/schema/ngày/ID/tham chiếu/replay-FSRS/view/index/transaction.
- **Class B/C** (audit được, không phải chân lý): claim bám nguồn/suy luận — validator chỉ xác nhận *liên kết tồn tại*.
- **Class D** (chỉ người kiểm): "người học đã thật sự hiểu chưa", chất lượng chấm rubric — validator KHÔNG đảm bảo.
