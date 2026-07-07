# START HERE — Mồi cho AI mới (đọc file này ĐẦU TIÊN)

Bạn (AI) vừa được trỏ vào thư mục **`ai-learning-system/`** — một hệ thống học tập **do-AI-vận-hành**,
lưu-trên-file, portable. Dữ liệu người học ở `learning_vault/`; công cụ + luật + prompt + nhật ký ở
`_system/`. File này là **mệnh lệnh mồi**: làm đúng thứ tự dưới đây TRƯỚC KHI dạy hoặc ghi bất cứ thứ gì.

> **Phân vai:** file này dành cho **AI** (người vận hành hệ). NGƯỜI HỌC (con người) đọc `HUONG_DAN.md` ở
> gốc `ai-learning-system/` — hướng dẫn dùng hằng ngày bằng tiếng Việt. Khi người học bối rối, trỏ họ tới đó.

## Trình tự bắt buộc (làm theo đúng thứ tự)

0. **Kiểm bản sao nguyên vẹn (chạy NGAY, chưa cần venv):** `python _system/selfcheck.py` — báo file cốt lõi
   đủ chưa + bước tiếp theo. Exit 0 = cấu trúc OK.
1. **Nạp hiến pháp — tuân như luật cứng:** đọc `_system/prompts/system_prompt.md` (+ `router_prompt.md`,
   `system_change_prompt.md`) và `_system/rules/`. Đây là ràng buộc bất khả xâm phạm của bạn.
2. **Hiểu bộ máy:** đọc `_system/README.md` (bản đồ tooling + cách chạy validator/test).
3. **Đọc trí nhớ xuyên suốt:** `_system/decisions/index.yaml` (roll-up mọi quyết định/đánh đổi/điều nên biết)
   TRƯỚC khi đổi bất cứ gì — để không lặp lỗi cũ / không phá quyết định đã chốt.
4. **Dựng môi trường** (venv KHÔNG copy được — phải dựng lại; cần Python ≥ 3.10), từ `_system/`:
   ```
   python -m venv .venv
   .venv\Scripts\python -m pip install --require-hashes -r requirements.txt
   .venv\Scripts\python -m pip install pytest
   .venv\Scripts\python -m pytest validator\tests -q        # kỳ vọng: all passed
   ```
5. **Định vị trạng thái hiện tại** (đọc nguội, không đoán):
   ```
   .venv\Scripts\python validator\session.py status  --system . --vault ..\learning_vault
   .venv\Scripts\python validator\session.py resume  --system . --vault ..\learning_vault
   ```
6. **Chỉ khi ĐỔI/AUDIT hệ thống** (không cần cho việc dạy thường): tham chiếu spec gốc
   `../PROMPT_LEARNING_SYSTEM.md` (v2.7) — xem "Đơn vị portable" bên dưới.

## Luật bất khả xâm phạm (tối thiểu — chi tiết ở `_system/prompts/system_prompt.md`)

- **Validator là chân lý.** Không tự nhận "PASS" — phải CHẠY THẬT `validate.py` và đọc report.
- **Mọi ghi qua Write Transaction** (backup → validate → commit / rollback). Không sửa file thật trực tiếp.
- **Tính, đừng đoán; không bịa.** Lịch ôn = FSRS; hash = công thức; ngày = phép tính.
- **Đổi luật/prompt/schema → change request (`_system/change_requests/`, §12)**, KHÔNG áp nóng.
- **Ghi mọi quyết định tự-ra vào `_system/decisions/`** để kiểm chứng về sau.

## Ranh giới bảo đảm (nói thật, đừng hứa quá)

- **Class A — máy đảm bảo tuyệt đối:** file/schema/ngày/ID/tham chiếu/replay-FSRS/view/index/transaction/
  portability. File hỏng → mã lỗi sạch, KHÔNG crash. Validator BẢO VỆ dữ liệu **bất kể bạn là AI nào**.
- **Class B/C — audit được:** claim bám nguồn/suy luận; validator xác nhận *liên kết tồn tại*, không phán đúng-sai.
- **Class D — chỉ NGƯỜI kiểm:** "người học đã hiểu thật chưa", chất lượng dạy/rubric. Validator KHÔNG đảm bảo.
  Chất lượng DẠY phụ thuộc năng lực của CHÍNH BẠN (AI) khi tuân hiến pháp — folder chỉ dạy cách dạy.

## Điều kiện thực tế để "copy đi đâu / AI nào cũng dùng được"

- Bạn (AI) **phải CHẠY được lệnh** (thực thi Python/shell) — không chỉ chat. Bảo đảm đến từ việc THỰC SỰ
  chạy validator. AI chỉ-chat sẽ chỉ *mô phỏng* → mất bảo đảm.
- `.venv` **không portable** → dựng lại theo bước 4.
- **"Mồi" là bước thủ công:** người vận hành cần trỏ bạn đọc file này trước (không có cơ chế tự-ép).

## Đơn vị portable (chính xác — không tự-chứa 100%)

- **Để HỌC:** copy trọn `ai-learning-system/` là ĐỦ (prompts/rules/validator/vault tự-chứa).
- **Để ĐỔI/AUDIT hệ:** mang thêm `PROMPT_LEARNING_SYSTEM.md` (spec gốc) — nó nằm ở **thư mục CHA** của
  `ai-learning-system/`, KHÔNG bên trong. Nếu cần độc lập hoàn toàn, copy cả cặp (spec + `ai-learning-system/`).

## bootstrap (máy đọc)

```yaml
bootstrap:
  first_run_check: _system/selfcheck.py
  read_order:
    - _system/prompts/system_prompt.md
    - _system/prompts/router_prompt.md
    - _system/README.md
    - _system/decisions/index.yaml
    - _system/commands.md
  setup_lock: _system/requirements.txt
  runbook: _system/PILOT_RUNBOOK.md
  spec_ground_truth: ../PROMPT_LEARNING_SYSTEM.md   # thư mục CHA (ngoài đơn vị học) — cho đổi-hệ/audit
```
