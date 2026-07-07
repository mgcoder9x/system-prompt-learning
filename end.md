# CONTEXT TRANSFER — ai-learning-system (phiên 2026-07-06, bản 2)

> Nguồn sự thật ĐẦY ĐỦ và bền vững: `_system/decisions/index.yaml` + `decisions.md` + `notes.md`.
> **Phiên sau ĐỌC 3 file đó TRƯỚC TIÊN.** File này chỉ là mồi chuyển-máy.

---

## 0. BỐI CẢNH MÁY (đọc kỹ — vừa chuyển máy)

- **Workspace hiện tại:** `C:\Users\k.nguyen.manh.toan\Desktop\TOANM\PERSONAL\system-prompt\ai-learning-system\`
- **Spec gốc** `PROMPT_LEARNING_SYSTEM.md` (v2.7) nằm ở **thư mục CHA** `...\system-prompt\` (NGOÀI đơn vị portable — đúng thiết kế DEC-047).
- **Shell thực tế = PowerShell (pwsh)**, KHÔNG phải cmd (dù system-info nói cmd). Hệ quả:
  - `tail`/`&&` không có. Dùng `; ` phân tách, `Get-Content <file> -Tail N`.
  - Console hay QUẤN DÒNG lệnh/đầu ra dài → **ghi output ra file rồi `Get-Content`**.
  - Script tiếng Việt: chạy `-X utf8`.
- **Python:** `python` là Store-alias KHÔNG dùng được. Dùng **`py` = Python 3.11.9**.
- **`.venv` KHÔNG relocatable:** khi chuyển máy, `.venv\Scripts\python.exe` trỏ Python máy cũ → hỏng. **Phải dựng lại** (xem §1).
- **Concurrency:** có trình-thực-thi-task tự chạy giữa lượt (văn phong giống hệt). **LUÔN đọc/grep trạng thái THẬT trước khi sửa.**

### Lệnh chuẩn (chạy từ `ai-learning-system\_system\`)
```powershell
# Rebuild venv (bắt buộc sau khi chuyển máy):
Remove-Item -Recurse -Force .venv
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install fsrs==6.3.1 "pydantic>=2.13,<3" "PyYAML>=6,<7" "markdown-it-py>=4,<5" pytest

# Test toàn bộ:
.\.venv\Scripts\python.exe -m pytest validator\tests -q

# Validator full scope (tất định qua --at):
.\.venv\Scripts\python.exe validator\validate.py --system . --vault ..\learning_vault --level full --scope full --at 2026-07-06T12:00:00+07:00 --json

# Self-check bootstrap:
.\.venv\Scripts\python.exe selfcheck.py
```

---

## 1. BASELINE HIỆN TẠI (đã verify phiên này, ran-test/ran-command)

- **454 passed** (trước phiên = 452; +2 do DEC-072).
- **validator full scope: `{pass:true, errors:[], warnings:[]}`**.
- **selfcheck: NGUYÊN VẸN**.
- `learning_vault` ship RỖNG (topics chỉ `.gitkeep`, con trỏ null). Demo docker là fixture dưới `validator/tests/fixtures/demo_vault`.
- Decision journal: **119 entry** md↔index khớp, không trùng ID (DEC-001..072, DEV-001..006, TRD-001..006, NOTE-001..035).

---

## 2. ĐÃ LÀM PHIÊN NÀY (hoàn tất, đã ghi journal)

1. **Chuyển máy THẬT lần 2** (toann → k.nguyen.manh.toan) → **NOTE-034**: `.venv` cũ trỏ Python máy toann → dựng lại bằng `py 3.11.9`; re-verify TOÀN BỘ trên máy mới (452 passed, validator PASS, selfcheck NGUYÊN VẸN). Nâng portability transcript→ran-command trên máy thứ hai (3.13-cũ vs 3.11-mới đều pass). Chỉ `.venv` phải dựng lại (đúng thiết kế INV-16).

2. **Cross-AI handoff #1 (Claude Opus 4.6 via Antigravity)** → **NOTE-035**, đóng **NOTE-031**: chạy trọn HANDOFF_TEST Phần A trên bản copy Desktop, để lại HANDOFF_RESULT.md. Chấm rubric R1–R7 = **ĐẠT** (R1 selfcheck, R3 validate PASS, R4 tx khớp, R4b insert hoán vị + exam ref tương đối, R7 trung thực; R5 N/A SOLO). Hệ GIỮ TOÀN VẸN sang AI khác.

3. **Fix test-defect DEC-072 (RED-first)**: cross-AI báo pytest 451/1 — `test_bootstrap_pointers_all_exist` ép `spec_ground_truth = ../PROMPT_LEARNING_SYSTEM.md` (cố ý NGOÀI đơn vị portable, DEC-047) tồn tại → fail OAN trên MỌI bản copy portable sạch. Fix: tách `_required_in_unit_pointers(b)` (loại spec ngoài-đơn-vị) làm tập must-exist; spec kiểm riêng. Thêm 2 test (`test_portable_copy_no_parent_spec` mô phỏng copy trong tmp + `test_spec_ground_truth_is_external_not_required`). `START_HERE.md` KHÔNG đổi (đã nói thật). code(test)-lệch-design → KHÔNG cần CR (tiền lệ DEC-029). **454 passed**.
   - File sửa: `_system/validator/tests/phase10/test_start_here_bootstrap.py`.

4. Journal: baseline NOTE-003 452→454, note_latest cập nhật, consistency check OK (119 entries).

5. **Tạo bản copy SẠCH** `...\ai-learning-system - Copy` (bỏ `.venv/__pycache__/.pytest_cache`; ship vault rỗng; có fix DEC-072; baseline journal 454) — đã verify OK để handoff.

---

## 3. ĐANG LÀM DỞ — ⚠️ BUG THẬT chưa fix trong workspace chính (ƯU TIÊN CAO)

**Cross-AI handoff #2 (Gemini 3.5 Flash via Antigravity)** chạy bản copy `ai-learning-system - Copy`:
- pytest ban đầu: **454/0** (fix DEC-072 hiệu quả — hết đỏ oan) ✓. Phần A committed, validate PASS.
- **Gemini tuyên bố phát hiện + TỰ SỬA `validate.py`** trong bản copy. Ghi `NOTE-036` trong journal của COPY (KHÔNG phải workspace chính).

### Bug (ĐÃ xác nhận qua đọc code thật — LÀ BUG THẬT):
- `transaction._build_overlay()` (transaction.py:305) tạo overlay bằng `tempfile.mkdtemp(prefix="tx_overlay_")` và **chỉ copy nội dung vault** (`self.root.rglob`). `exam/` là **SIBLING NGOÀI vault** → KHÔNG được copy vào overlay. Overlay's parent = thư mục TEMP (không có `exam/`).
- `Transaction.validate_staged` (transaction.py:247) chạy `validate_full_semantic` trên overlay (FULL scope → chạy `_check_exam_results` trên MỌI topic).
- `_check_exam_results` (validate.py:~502, workspace CHÍNH — CHƯA sửa): `exam_root = (vault_root.parent / "exam").resolve()`; `rp = (topic_dir / r.ref).resolve()`. Trong overlay: `vault_root`=overlay temp, `.parent`=TEMP (không exam/); ref `../../../exam/...` resolve vào TEMP → không tồn tại → **E-EXAM-REF-BROKEN GIẢ**.
- **Trigger:** sau khi 1 topic có `exam_results.md` (từ `/grade`), BẤT KỲ lệnh FULL-transaction sau đó (`/learn topic-mới`, `/done`, `/review`) → overlay full-validate → fail giả. E2E của ta (DEC-068) BỎ SÓT vì validate STANDALONE, không qua transaction sau khi có exam_results.

### Fix của Gemini (trong COPY) — ⚠️ KHÔNG DÙNG (phá portability):
```python
if "tx_overlay_" in str(vault_root):
    workspace_root = Path(__file__).resolve().parent.parent.parent
    exam_root = (workspace_root / "exam").resolve()
    resolve_base = workspace_root / "learning_vault" / "topics" / topic_dir.name
else: ...
```
Vấn đề: (a) couple validator với tên temp-dir của transaction (mong manh); (b) hardcode layout repo qua `Path(__file__)`, **BỎ QUA vault_root truyền vào** → phá INV-16 (validate vault ở vị trí khác sẽ resolve exam/ về chỗ validator, sai) + nhiều khả năng vỡ test demo_vault fixture. **Workspace chính CHƯA áp gì — validate.py còn nguyên bản gốc.**

### CẦN LÀM (theo thứ tự):
1. **REPRODUCE RED-first trong workspace chính** (temp vault copy): `/learn t1` → `/collect` → `/curriculum` → `/grade` (tạo exam_results.md) → `/learn t2` (full-tx) → quan sát E-EXAM-REF-BROKEN giả. Xác nhận bug.
2. **Fix GỐC ĐÚNG (KHÔNG hack như Gemini).** Phương án ưu tiên **(A)**: thread base exam THẬT vào validate lúc transaction — `validate_staged` truyền `self.root.parent` (parent vault THẬT, có exam/ thật) xuống `validate_full_semantic` → `_check_exam_results(exam_base=...)`, default = `vault_root.parent` cho standalone. Giữ validate.py layout-agnostic + portable (dùng vị trí vault thật, KHÔNG `__file__`). Đánh giá thêm phương án (B): trong overlay coi exam/-existence là ngoài-scope (chỉ kiểm format ref + target), hoãn existence sang standalone full validate — nhưng (B) YẾU hơn. **CHỌN (A).**
3. RED-first test bắt đúng ca transaction-overlay. Sync `rules/validation_rules.md` nếu cần (không mã lỗi mới). 
4. Full suite + validator full scope + probe CLI thật (trước=fail giả, sau=PASS).
5. **DEC-073**: ghi quyết định fix gốc + ghi công Gemini phát hiện bug THẬT nhưng fix của nó không phù hợp (portability) → workspace chính áp fix đúng.
6. Cập nhật baseline (454 + số test mới).

### Chấm handoff #2 (Gemini) — làm sau khi fix:
- R1 selfcheck ✓, R2 pytest 454/0 ban đầu ✓, R3/R4/R4b ✓ (Phần A committed, tx log khớp), R5 N/A SOLO, R7 trung thực (khai thẳng đã sửa code + friction `py`/PowerShell quoting). **Điểm cộng lớn: phát hiện bug tích hợp THẬT mà pilot/E2E của ta bỏ sót.**
- Lưu ý: sau khi Gemini chạy writes, `test_shipped_vault_clean.py` fail 2 test (`test_shipped_vault_topics_empty`, `test_shipped_vault_pointers_null`) trong COPY — **đúng thiết kế** (vault ship bị bẩn do ghi topic git-basics/docker), KHÔNG phải bug.
- **KHÔNG merge ngược code/journal từ COPY** vào workspace chính (copy là artifact test; NOTE-036 của copy ≠ journal nguồn-sự-thật).

---

## 4. RÀNG BUỘC XUYÊN SUỐT (giữ nguyên)

- **Không bịa; fix tận GỐC không fix ngọn; RED-first; validate nhiều lần** (targeted + full suite + validator full scope sau MỖI thay đổi); design-first; phân biệt under-enforce (đáng fix) vs ceremony (không thêm).
- **Đổi lệnh/schema/spec → qua `change_requests/` (§12):** AI ghi pending → owner "duyệt" (tín hiệu proceed) → move approved + changelog (chỉ khi áp xong) + ghi DEC. (Fix code-lệch-design/spec KHÔNG cần CR — tiền lệ DEC-029/072.)
- **Mỗi thay đổi journal:** tạo `_check_tmp.py` (parse ```yaml blocks + index.yaml, check trùng ID + md↔index symmetric-diff), chạy `-X utf8`, rồi **XÓA** (+ `_out.txt`). Sửa `note_latest` trong index.yaml dễ vỡ YAML → sau sửa PHẢI chạy consistency check (nó `yaml.safe_load` index.yaml).
- Lệnh giữ English (alias tiếng Việt đã từ chối — DEC-052).
- Drift-guard registry đồng bộ mỗi lệnh mới (CLI_COMMANDS ↔ commands.md backends ↔ router ↔ test error_codes).
- Bản copy handoff: LUÔN bỏ `.venv/__pycache__/.pytest_cache`; dán trọn `HANDOFF_TEST.md`; AI kia để lại `HANDOFF_RESULT.md`.

---

## 5. FILE PHIÊN SAU NÊN ĐỌC TRƯỚC

1. `_system/decisions/index.yaml` (ĐẦU TIÊN — roll-up + note_latest).
2. `_system/decisions/notes.md` (NOTE-034/035; NOTE-036 chỉ có trong COPY) + `decisions.md` (DEC-072).
3. `_system/validator/validate.py` (`_check_exam_results` ~dòng 482–512 — chỗ cần fix) + `transaction.py` (`validate_staged` 247, `_build_overlay` 305).
4. `_system/validator/session.py` (cmd_grade ~941; cmd_learn/next_lesson — đường full-transaction).
5. Bản copy `...\ai-learning-system - Copy\HANDOFF_RESULT.md` (báo cáo Gemini) + `...\_system\validator\validate.py` (xem fix hack của Gemini để tránh lặp).

## 6. TÍNH NĂNG (trạng thái)
- Curriculum-driven-learning: **HOÀN TẤT 100%** (T1–T11 + 5.3), cr-0001..0010 approved. KHÔNG còn task feature mở.
- Việc DUY NHẤT đang mở: **fix bug E-EXAM-REF-BROKEN transaction-overlay** (§3) — do handoff #2 phát hiện.
- Ngoài scope tương lai: MCP wrap (design-first, chưa bắt đầu); alias tiếng Việt (đã từ chối).
