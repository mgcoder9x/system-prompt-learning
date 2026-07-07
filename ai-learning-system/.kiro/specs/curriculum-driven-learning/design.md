# Design Document

## Overview

Tính năng **Học theo giáo trình** mở rộng hệ hiện có từ "một topic ≈ một lesson-001" sang "một topic có **Curriculum** (giáo trình) nhiều điểm/nhiều bài, dạy-hỏi bám giáo trình, tự tiến qua từng bài khi qua cổng `learned_gate`", với ba năng lực mới: **nạp tài liệu tham chiếu on-demand**, **dựng + kiểm giáo trình**, và **chấm bài thực hành (exam)**.

Thiết kế bám **kiến trúc sẵn có** (không phát minh lại):
- **Validator là chân lý** (INV-01..26); mọi thuộc tính máy-đảm-bảo của Curriculum sẽ có mã lỗi + test (Class A).
- **Write Transaction** cho mọi ghi vault (backup → validate → commit/rollback).
- **`sources.md`** đã có (status raw/confirmed) — tái dùng cho danh bạ nguồn, KHÔNG tạo cơ chế nguồn thứ 2.
- **`topic_state.lessons[]`** đã là index bài (INV-25) — Curriculum ánh xạ vào đây, không thay thế.
- **`learned_gate`** + rubric 5 trục đã có — auto-advance móc vào đường `/done`, không đổi cổng.
- Mọi lệnh mới/schema mới/đổi spec đi qua **change-request §12** (không sửa nóng).

**Nguyên tắc tận dụng 5 repo (theo thoả thuận on-demand):** KHÔNG clone bulk. Đăng ký repo làm nguồn trong `sources.md`; khi dựng giáo trình, chỉ **kéo lát cắt markdown liên quan** vào `reference/<topic>/` (chỉ text, không `.git`/code) → giữ INV-16/17 + tránh bản quyền bulk.

## Ranh giới bảo đảm (nhắc lại, quyết định kiến trúc)

- **Class A (máy đảm bảo):** cấu trúc Curriculum đúng schema, định danh điểm duy nhất, thứ tự không trùng/không hở, mục tiêu không rỗng, trạng thái hợp lệ, liên kết truy vết trỏ file tồn tại, index bài khớp đĩa (INV-25), con trỏ tiến độ không dangling (INV-03), auto-advance chỉ sau `learned_gate`, không path tuyệt đối (INV-16).
- **Class D (người/AI đánh giá — validator KHÔNG tự nhận đảm bảo):** giáo trình có "đủ sâu/đủ rộng/chính xác về nội dung" không; chấm chất lượng bài `exam/`.

## Architecture

### Vị trí file (quyết định INV-16/17/18)

```
ai-learning-system/
  learning_vault/                         # dữ liệu học (validator quét INV-17: không code)
    topics/<topic>/
      curriculum.md                       # MỚI — artifact giáo trình (front-matter máy-đọc)
      reference/                           # MỚI — lát cắt markdown đã lọc (CHỈ .md, KHÔNG code)
        <slug>.md
      sources.md                          # SẴN CÓ — thêm entry repo nguồn (status: raw)
      topic_state.md                      # SẴN CÓ — lessons[] index (INV-25), + con trỏ curriculum
      lessons/lesson-001..NNN/            # SẴN CÓ — nhiều bài (khắc phục giới hạn lesson-001)
  exam/                                    # MỚI — Ở GỐC, NGOÀI vault (vì bài nộp có thể là CODE)
    <topic>/<submission-id>/...            # code người học nộp — validator KHÔNG quét (không phá INV-17)
  _system/
    validator/... exam_records/            # KHÔNG — bản ghi chấm là dữ liệu học → thuộc vault
```

**Quyết định quan trọng (căn cứ INV-17):**
- `reference/` đặt **trong** `learning_vault/topics/<topic>/` và **chỉ chứa `.md`** (text đã lọc). Markdown không phải đuôi code/manifest → INV-17 không kích. Truy vết được từ Curriculum_Point.
- `exam/` (bài nộp, có thể là `.py/.js/...`) đặt **ở gốc `ai-learning-system/`, NGOÀI vault** → validator không quét vault trúng nó → INV-17 vault vẫn PASS. **Bản ghi kết quả chấm** (metadata, markdown/yaml, KHÔNG chứa code) lưu **trong vault** (`topics/<topic>/exam_results.md`) và trỏ tới bài nộp bằng **đường dẫn tương đối** (INV-16).
- Đây là cách thỏa R2 và R9.5 kiểm-chứng-được: sau khi thêm tính năng, `validate --scope full` trên vault vẫn PASS INV-16/17/18.

## Components and Interfaces

### Danh bạ nguồn — tận dụng tối đa 5 repo (on-demand)

Đăng ký một lần trong `sources.md` của topic (status: raw), gán vai trò rõ ràng. Khi `/tạo-giáo-trình`, AI chỉ kéo **lát cắt liên quan topic** (ví dụ học Docker → chỉ mục Docker của roadmap), lưu markdown đã lọc vào `reference/<topic>/`, ghi `source_ref` truy vết.

| Repo (ref) | Vai trò trong pipeline | Kéo cái gì (on-demand) |
|---|---|---|
| `kamranahmedse/developer-roadmap` | Xương sống **thứ tự** Curriculum_Point | Lát roadmap của topic → danh sách điểm + thứ tự |
| `EbookFoundation/free-programming-books` | Danh bạ tài liệu chiều sâu | Link tài liệu cho từng điểm |
| `practical-tutorials/project-based-learning` | Ngân hàng **bài exam** thực hành | Project liên quan topic → đề bài `exam/` |
| `donnemartin/system-design-primer` | Nội dung sâu (topic system-design) | Mục liên quan làm reference chính |
| `freeCodeCamp/freeCodeCamp` | Tham chiếu ý tưởng bài/thử thách | Ý tưởng chia bài — KHÔNG vendor |

Bổ sung: mỗi topic nên có **nguồn chính chủ** (vd `docker.com/learning-paths`) đặt trust cao hơn — dùng để đối chiếu độ chính xác (Class D).

### Lệnh mới (đăng ký qua change-request §12 — CHƯA đặt tên cứng)

Năng lực (R4). Tên lệnh sẽ chốt trong CR:
1. **Thu thập dữ liệu** (đề xuất `collect`): kéo lát cắt nguồn → `reference/<topic>/*.md` + ghi `sources.md` (transaction-LIGHT).
2. **Dựng giáo trình** (đề xuất `curriculum`): sinh `curriculum.md` từ `reference/` (hoặc nguồn ngoài) — transaction-FULL, chạy Curriculum_Validator.
3. **Kiểm giáo trình** (đề xuất `curriculum --check`): read-only, in báo cáo PASS/FAIL.
4. **Sinh bài kế** (đề xuất `next-lesson`): tạo `lesson-NNN` cho `current_point`, cập nhật `topic_state.lessons[]` (INV-25) — transaction-FULL.
5. **Chấm bài** (đề xuất `grade`): tạo entry `exam_results.md` (transaction-LIGHT).

## Data Models

### 1) `curriculum.md` (front-matter máy-đọc + body người-đọc)

```yaml
schema: curriculum
schema_version: 1
topic_id: <topic>
teachable: false            # false tới khi Curriculum_Validator PASS (R5.2)
current_point: cp-001       # con trỏ tiến độ (INV-03: phải trỏ point tồn tại)
points:
  - id: cp-001              # định danh ổn định, duy nhất trong curriculum
    order: 1                # thứ tự học: 1..N, không trùng, không hở
    objective: "..."        # không rỗng (>=1 ký tự non-space)
    status: not_started     # {not_started | in_progress | done}
    lesson_id: null         # ánh xạ tới lesson khi đã sinh (INV-03)
    source_refs:            # truy vết reference (R1.4); rỗng nếu dựng từ nguồn ngoài
      - "reference/docker/roadmap-containers.md"
created: <date>
updated: <date>
```

### 2) `exam_results.md` (bản ghi chấm — trong vault, KHÔNG chứa code)

```yaml
schema: exam_results
schema_version: 1
topic_id: <topic>
results:
  - submission_id: ex-001
    ref: "../../../exam/<topic>/ex-001"   # tương đối tới bài nộp NGOÀI vault (INV-16)
    target: cp-003                          # topic hoặc curriculum_point tồn tại
    graded_at: <date>
    verdict: "..."                          # nhận xét Class D (không phải chân lý máy)
```

Cả hai schema thêm: file `schemas/*.schema.md` (khối `schema_fields` máy-đọc) + model pydantic trong `models.py` + drift-guard test — **đồng nhất** cơ chế hiện có (R11.5, DEC-008).

## Error Handling

### Bộ kiểm giáo trình (Curriculum_Validator) — mã lỗi mới (RED-first)

Mở rộng `validate.py`. Mỗi mã có ≥1 test FAIL trước khi hiện thực (R10.2):

| Mã lỗi | Vi phạm | Requirement |
|---|---|---|
| `E-CURR-SCHEMA` | curriculum.md sai schema/kiểu | R3, R11 |
| `E-CURR-DUP-ID` | hai Curriculum_Point trùng `id` | R3.7, R10.1 |
| `E-CURR-ORDER` | `order` trùng hoặc hở (không 1..N liên tục) | R3.1 |
| `E-CURR-EMPTY-OBJECTIVE` | `objective` rỗng | R3.3, R5.3 |
| `E-CURR-BADSTATUS` | `status` ngoài tập hợp lệ | R3.6, R5.3 |
| `E-CURR-REF-BROKEN` | `source_refs` trỏ file không tồn tại trong `reference/` | R1.4, R5.6 |
| `E-CURR-POINTER` | `current_point` trỏ point không tồn tại (dangling) | R7.5 (INV-03) |
| `E-CURR-LESSON-LINK` | `lesson_id` trỏ lesson không tồn tại trên đĩa | R6, INV-25 |
| `E-EXAM-REF-BROKEN` | bản ghi chấm trỏ submission/target không tồn tại | R9.4/9.6 |

`teachable` chỉ được set `true` khi 0 vi phạm (R5.1/5.2). "Đủ sâu/rộng/chính xác" KHÔNG có mã — cố ý (Class D, R5.5).

## Correctness Properties

Các bất biến máy-kiểm-được (Class A) mà tính năng phải giữ. Mỗi property kiểm được bằng test tất định.

### Property 1: Auto-advance chỉ sau cổng
Con trỏ `current_point` chỉ tiến khi lesson tương ứng đạt `learned_gate`.
**Validates: Requirements 7.1, 7.2, 7.3, 10.4**

### Property 2: Toàn vẹn con trỏ
`current_point` luôn trỏ một point tồn tại (INV-03); vi phạm → `E-CURR-POINTER`.
**Validates: Requirements 7.5**

### Property 3: Index khớp đĩa
Mỗi `lesson_id` trong curriculum + `topic_state.lessons[]` khớp lesson thật trên đĩa (INV-25); vi phạm → `E-CURR-LESSON-LINK`.
**Validates: Requirements 6.4, 6.5, 10.3**

### Property 4: Định danh và thứ tự
`id` các point duy nhất; `order` là hoán vị liên tục 1..N (không trùng, không hở); vi phạm → `E-CURR-DUP-ID` / `E-CURR-ORDER`.
**Validates: Requirements 3.1, 3.2, 3.7, 10.1**

### Property 5: Cổng dạy
Không sinh lesson khi `teachable=false`.
**Validates: Requirements 5.2, 6.1, 6.8**

### Property 6: Tất định
Cùng đầu vào luôn cho cùng tập mã lỗi + cùng phán quyết, không phụ thuộc đồng hồ thật hay thứ tự duyệt file.
**Validates: Requirements 10.6**

### Property 7: Bảo toàn bất biến nền
Sau khi thêm tính năng, vault vẫn PASS INV-16/17/18/25.
**Validates: Requirements 11.3, 11.4**

### Auto-advance (R7) — móc vào `/done`, không cổng mới

Khi `cmd_done` set `lesson.status = learned` (đã qua `learned_gate`):
- Trong **cùng transaction**: tìm `point` có `lesson_id == <lesson>` → set `status=done`; nếu còn point `status!=done` theo `order` nhỏ nhất → set `current_point` = point đó; nếu hết → `curriculum` đánh dấu hoàn tất.
- Nếu chưa qua gate → không đụng con trỏ (R7.3). Nếu transaction validate fail → rollback (R7.6). Tất cả kiểm-được bằng test tất định (R10.4).

## Testing Strategy

### Kỷ luật test (hiện hành)

1. **RED-first** mỗi mã lỗi mới (test đỏ trước khi code kiểm).
2. Sau mỗi thay đổi: **full suite** + `validate --scope full` PASS trên vault.
3. **Tất định**: bơm `--at` cố định; không lệ đồng hồ/thứ tự file (R10.6).
4. E2E: `collect → curriculum → validate(PASS) → next-lesson → dạy → /done → auto-advance → next-lesson-002` trên vault tmp, FULL PASS mỗi bước.
5. Bảo toàn bất biến: test khẳng định vault ship vẫn PASS INV-16/17/18/25 sau tính năng (R11.4).

## Kế hoạch change-request (thứ tự áp)

- **CR-0007** — schema mới `curriculum` + `exam_results` (models + schemas/ + drift-guard). Bump VERSION? Không (schema_version per-file = 1; không đổi file cũ). 
- **CR-0008** — 5 lệnh mới vào registry `commands.md` + router.
- **CR-0009** — sửa spec: mở rộng §3/§11A cho multi-lesson + reference/exam (spec hiện nói 1 topic nhiều lesson nhưng chưa mô tả curriculum/reference/exam).
Mỗi CR: pending → bạn "Duyệt" → áp + changelog + ghi DEC.

## Rủi ro & giảm thiểu

- **INV-17 với reference/**: chỉ cho `.md`; thêm kiểm "reference/ chỉ chứa .md" (nếu lọt file code → cảnh báo). 
- **exam/ ngoài vault không được validator bảo vệ**: chấp nhận (bài nộp là code, bản chất Class D); chỉ **bản ghi chấm** trong vault được máy kiểm ref-integrity.
- **Kéo nguồn online cần mạng**: `collect` phải suy biến sạch khi offline (báo lỗi, không tạo curriculum rỗng — R1.5).
- **Bản quyền**: chỉ lưu trích đoạn + ghi nguồn; không vendor nguyên repo.
