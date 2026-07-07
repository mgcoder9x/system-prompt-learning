# Bản Thiết Kế Hệ Thống Học Bằng AI (v2.7 — Thêm Học Theo Giáo Trình)

> Trạng thái: **đã chốt v2.1** ngày 2026-06-30, **vá thực thi v2.2**, **vá chính xác v2.3**,
> **vá dependency/IO v2.4**, **vá schema card/edge v2.5** ngày 2026-07-01,
> **vá theo SPIKE FSRS thật v2.6** ngày 2026-07-01 (F-A: bỏ State.New; F-B: due_date là trục chuẩn — xem A.7),
> **mở rộng học-theo-giáo-trình v2.7** ngày 2026-07-06 (CR-0009: thêm khái niệm Curriculum nhiều bài, vùng
> `reference/`, vùng `exam/` — THÊM tính năng, KHÔNG phá cấu trúc cũ; topic không có `curriculum.md` vẫn hợp lệ).
> Engine lịch ôn = FSRS; validation là lõi với mô hình **"toàn vẹn cấu trúc đúng tuyệt đối + tầng
> phán đoán audit được"** (Class A đúng tuyệt đối; B/C/D có dấu vết, KHÔNG tự nhận là chân lý — đọc
> mục 0.3 về giới hạn thực thi); một nguồn sự thật duy nhất; số file tối giản; rubric rời rạc +
> evidence; transaction-safe có recovery manifest; giao diện lệnh.
> Tài liệu này là spec định hướng triển khai (mục 20). Sửa nội dung phải qua change request (mục 12).

---

## 0. Tuyên Bố Về "Chính Xác Tuyệt Đối" (Đọc Trước Tiên)

Đây là phần quan trọng nhất của hệ thống. Mọi thiết kế sau đều phục vụ tuyên bố này.

Một LLM **không thể** đảm bảo đúng tuyệt đối với phán đoán chủ quan (ví dụ: "người học đã thật sự hiểu chưa"). Nếu bản thiết kế hứa điều đó, nó nói dối. Vì vậy hệ thống định nghĩa lại "chính xác tuyệt đối" thành hai cam kết tách biệt:

1. **Đúng tuyệt đối ở tầng cấu trúc và tính toán (Class A).**
   Mọi thứ có thể tính hoặc kiểm bằng máy — file tồn tại, schema hợp lệ, kiểu dữ liệu, phép tính ngày, chuyển trạng thái hợp lệ khi có baseline transaction, ID duy nhất, tham chiếu chéo không gãy, lịch ôn tính ra cùng kết quả — **bắt buộc đúng 100%**, vì chúng được *tính toán và kiểm bằng validator dạng code*, không phải do AI "cảm tính".

2. **Truy vết và tái lập được ở tầng phán đoán (Class B/C/D).**
   Với phần chủ quan, hệ thống không tuyên bố chân lý. Thay vào đó nó đảm bảo: mọi kết luận đều **gắn bằng chứng cụ thể**, **theo rubric rời rạc**, và **một AI khác đọc cùng bằng chứng sẽ ra cùng kết luận**. Đây là "chính xác" theo nghĩa nhất quán và kiểm toán được, không phải toàn tri.

### 0.1. Phân Lớp Mọi Khẳng Định (Claim Classes)

Mỗi claim được ghi vào mục `## Claims` (xem mục 5.5) phải có `id`, `class`, `status`, và `text`. Chỉ claim `status: confirmed` mới là **khẳng định kiến thức chính thức**. Claim `status: draft` là ghi chú làm việc chưa nguồn-hoá: được kiểm cấu trúc, bị cấm vào `## Knowledge Map`, và không được dùng làm tiền đề chắc chắn. Hội thoại/transcript trong `lesson.md` (câu hỏi, điều hướng, động viên) KHÔNG bắt buộc gắn lớp.

| Lớp | Loại khẳng định | Cách kiểm | Mức đảm bảo |
|-----|-----------------|-----------|-------------|
| **A** | Sự thật cấu trúc/tính toán | Validator dạng code | Đúng tuyệt đối |
| **B** | Kiến thức bám nguồn | Phải trỏ tới anchor trong `sources.md` | Đúng nếu trích dẫn tồn tại và đúng phạm vi |
| **C** | Suy luận của AI | Phải liệt kê tiền đề (đều là A hoặc B) | Hợp lệ nếu suy luận từ tiền đề hợp lệ |
| **D** | Phán đoán năng lực người học | Rubric rời rạc + bằng chứng trích nguyên văn | Tái lập được, không tuyên bố chân lý |

Quy tắc cứng:

- Không claim nào trong mục `## Claims` được "mồ côi lớp". Thiếu nhãn lớp = validator báo lỗi `E-CLAIM-UNCLASSED`. Hội thoại/transcript thường KHÔNG bị ràng.
- Một claim `status: confirmed` lớp B mà không có anchor nguồn confirmed = `E-CLAIM-NOSRC`. Claim `status: draft` được phép thiếu anchor, nhưng phải có `draft_reason` và không được xuất hiện trong `## Knowledge Map`.
- Một claim `status: confirmed` lớp C mà có tiền đề thuộc lớp D hoặc tiền đề draft = `E-CLAIM-WEAKBASE` (không được suy luận chắc chắn từ phán đoán chủ quan/chưa nguồn-hoá).
- Trạng thái "đã hiểu" (lớp D) không bao giờ được nâng lên nói như sự thật (lớp A).

### 0.2. Nguyên Tắc "Tính, Đừng Đoán"

Bất cứ thứ gì có thể tính bằng công thức thì **phải tính bằng công thức cố định**, không để AI ước lượng:

- Ngày ôn tiếp theo → engine FSRS (mục 8).
- Mức thành thạo tổng → hàm tổng hợp từ rubric (mục 9).
- Trạng thái lesson/topic → máy trạng thái (mục 6).
- Lịch ôn cấp topic → sinh tự động từ cấp lesson (mục 7).

AI chỉ phán đoán ở đúng chỗ không thể tính (chấm rubric từ câu trả lời), và ngay cả chỗ đó cũng bị ràng bằng bằng chứng.

### 0.3. Giới Hạn Thực Thi (Đọc Kỹ — Đừng Tin Quá)

Tài liệu này cố ý nói rõ **cái validator KHÔNG bảo đảm được**, để không ai hiểu lầm "hệ thống đảm bảo tôi hiểu đúng". Có ba giới hạn cố hữu, không thiết kế file-based nào xoá được:

1. **Validator chỉ kiểm cấu trúc/tính toán, KHÔNG kiểm ngữ nghĩa.** Một claim `status: confirmed` lớp B có `source_refs` trỏ tới nguồn confirmed → validator xác nhận *liên kết tồn tại*, KHÔNG xác nhận `quote` thật sự chống đỡ cho claim. Một claim `status: confirmed` lớp C có `premise_refs` → validator xác nhận *có liệt kê tiền đề*, KHÔNG xác nhận suy luận hợp lệ. Một trục mastery đạt ngưỡng có evidence → validator xác nhận *evidence tồn tại và là verbatim của transcript*, KHÔNG xác nhận điểm số tương xứng. Đây là **toàn vẹn + audit được**, không phải "đúng nội dung".

2. **Lớp D KHÔNG được enforce "tái lập".** Câu "hai AI đọc cùng bằng chứng ra cùng kết luận" (mục 0) là **mục tiêu thiết kế của rubric**, KHÔNG phải bất biến validator kiểm. Không có cơ chế tự động đo độ nhất quán giữa hai lần chấm. Rubric rời rạc + mô tả mức (mục 9.2) chỉ *giảm* phương sai, không *khử* nó.

3. **Lằn ranh "bằng chứng thật" dựa vào con người.** INV-22b ép `quote ⊆ transcript`, nhưng transcript (`#### Bạn trả lời`) cũng do AI ghi lại lời người học. Về nguyên tắc AI có thể tự "đặt chữ vào miệng người học". Validator bịt được lỗ "quote không hề có trong transcript", KHÔNG bịt được lỗ "transcript không khớp điều người thật gõ". Phòng tuyến cuối là **con người tự đọc lại transcript** và **con người tự chạy `validate.py`** — hệ thống cấm AI tự nhận PASS, nhưng không có cách kỹ thuật nào ép một LLM không nói dối. Cam kết "đúng tuyệt đối" chỉ vững khi người dùng thực sự chạy validator, không phải khi AI nói đã chạy.

Tóm gọn: hệ thống bảo đảm **file không thể mâu thuẫn về cấu trúc, số học, ngày tháng, lịch ôn, và mọi phán đoán đều có dấu vết truy được**. Nó KHÔNG bảo đảm kiến thức đúng hay người học đã thật sự hiểu — phần đó vẫn là trách nhiệm của người học và chất lượng của AI.

---

## 1. Mục Tiêu Hệ Thống

Xây một trợ lý học tập dài hạn chạy trong IDE, không trả lời tự do, mà tuân theo một bộ luật học tập cố định. Hệ thống phải:

- Biết tôi đang học gì, ở đâu, đã hiểu gì, còn vướng gì.
- Tự tạo cấu trúc topic/lesson khi tôi nói muốn học cái mới.
- Có bộ nhớ dạng file, cập nhật liên tục, chống trôi ngữ cảnh.
- Có lịch ôn theo thời gian, tính bằng thuật toán xác định.
- Bất kỳ phiên AI nào đọc vào cũng hiểu ngay trạng thái và tiếp tục đúng.
- Mọi dữ liệu ghi ra đều qua validator và chỉ commit khi mọi bất biến còn đúng.

---

## 2. Kiến Trúc 2 Folder (Đã Chốt)

```text
ai-learning-system/
  _system/          # luật, prompt, template, validator, repo công cụ, change request
  learning_vault/   # toàn bộ bài học, topic, lesson, nguồn, trạng thái, lịch ôn
```

- `_system/` = phần vận hành. Dùng chung được cho nhiều người.
- `learning_vault/` = phần dữ liệu học. Mang đi máy khác, chia sẻ, hoặc cho AI khác đọc tiếp.

Đây là quyết định gốc. Chỉ sửa khi tôi yêu cầu sửa hệ thống và đã xác nhận qua change request.

Cấu trúc `_system/`:

```text
_system/
  README.md
  VERSION                      # số phiên bản schema của toàn hệ thống
  commands.md                  # command registry (mục 11A): cú pháp, intent, phạm vi ghi
  fsrs_config.yaml             # cấu hình FSRS cố định (mục 8.3), gắn version
  prompts/
    system_prompt.md
    router_prompt.md
    system_change_prompt.md
  rules/
    teaching_rules.md
    validation_rules.md
    memory_rules.md
    review_rules.md            # ánh xạ grade 0..3 → rating FSRS 1..4 (mục 8.1)
    anti_drift_rules.md
    claim_rules.md             # luật phân lớp khẳng định (mục 0.1, 5.5)
  schemas/
    lesson_state.schema.md
    topic_state.schema.md
    sources.schema.md
    review_item.schema.md
    vault_state.schema.md
  validator/
    validate.py                # validator dạng code (mục 10)
    fsrs_adapter.py            # bọc API thật của package fsrs (mục 8.4 chỉ là pseudocode logic)
    invariants.md              # danh sách bất biến (mục 10.2)
    error_codes.md             # bảng mã lỗi
    tests/                     # golden fixtures: validate the validator (mục 10.6)
  migrations/                  # script vN_to_vN+1 (mục 10.7)
  templates/
    topic_template/
    lesson_template/
  repo_lab/
    candidates.md
    selected_repos.md
    repo_evaluations/
    installed_repos/
    reference_repos/           # repo clone CHỈ để đọc thiết kế (mục 16.2), không cài
  .venv/                       # môi trường Python cài dependency validator (mục 16.0/16.1)
  pyproject.toml               # khai báo dependency
  uv.lock                      # lock có hash (uv) — nguồn tái lập chính
  requirements.txt             # lock pin+hash fallback cho máy chỉ có pip
  change_requests/
    pending/
    approved/
    rejected/
    changelog.md               # nhật ký mọi thay đổi luật đã duyệt
  .tx/                         # vùng transaction tạm + transaction_log.md (mục 10.3)
```

---

## 3. Cấu Trúc File Tối Giản

Nguyên tắc: **bắt đầu tối giản, chỉ tách file khi thực sự thiếu**. Mỗi đơn vị học chỉ giữ số file nhỏ nhất mà vẫn tách được "nội dung học" khỏi "trạng thái máy kiểm".

### 3.1. Một Lesson — 3 File

```text
lessons/lesson-001/
  lesson.md          # bài giảng + phần "Hỏi phụ" + session blocks (Question/Bạn trả lời/AI phản hồi/Evidence)
  lesson_state.md    # FRONT-MATTER có cấu trúc: trạng thái + review items (MÁY KIỂM)
  lesson_notes.md    # tóm tắt ngắn + tóm tắt sâu + thẻ ôn (phân tách bằng heading)
```

- `lesson.md`: nơi học chính. Có section `## Hỏi phụ` để gom câu hỏi đào sâu, không tách file riêng.
- `lesson_state.md`: file **được máy kiểm**. Phần đầu là YAML front-matter cố định (mục 5). Đây là **nguồn sự thật** cho tiến độ và toàn bộ review item của lesson.
- `lesson_notes.md`: tóm tắt nhiều tầng bằng heading `## Tóm tắt ngắn`, `## Tóm tắt sâu`, `## Thẻ ôn`.

### 3.2. Một Topic — 3 File + thư mục lessons

```text
topics/topic-name/
  topic.md           # mục tiêu topic + section `## Knowledge Map` (bản đồ kiến thức) + danh mục lesson
  topic_state.md     # FRONT-MATTER: trạng thái topic + lịch ôn SINH TỰ ĐỘNG + bảng đánh giá
  sources.md         # nguồn học, mỗi mục có field status (raw/processing/confirmed/rejected)
  curriculum.md      # (TÙY CHỌN, v2.7) giáo trình nhiều bài: danh sách điểm cần học có thứ tự — xem 3.5
  reference/         # (TÙY CHỌN, v2.7) lát cắt tài liệu tham chiếu (CHỈ .md) để dựng giáo trình — xem 3.4
  exam_results.md    # (TÙY CHỌN, v2.7) bản ghi CHẤM bài thực hành (metadata, KHÔNG code) — xem 3.4
  lessons/
    lesson-001/ ...
```

- **v2.7 — tương thích ngược:** `curriculum.md`, `reference/`, `exam_results.md` đều **tùy chọn**; validator chỉ kích kiểm khi chúng tồn tại. Topic cũ (không có các mục này) vẫn hợp lệ nguyên vẹn.

### 3.3. Vault — 1 file điều hướng

```text
learning_vault/
  README.md
  vault_state.md     # con trỏ "đang học topic/lesson nào" + version schema
  _scratch/          # VÙNG PHI-THẨM-QUYỀN: file nháp ôn tập, xóa được, không ai trỏ tới
  .tx/               # vùng transaction transient của vault (file-level atomic + manifest recovery); validator bỏ qua
  topics/ ...
```

So với v1: lesson giảm từ 7 → 3 file, topic giảm từ 7 → 3 file. Ít điểm đồng bộ hơn = ít chỗ vỡ hơn.

### 3.4. Vùng Tham Chiếu `reference/` và Vùng Bài Thực Hành `exam/` (v2.7)

**`reference/` (trong topic, tùy chọn):** nơi chứa các **lát cắt tài liệu** (markdown thuần) mà người học/AI thu về để làm nguyên liệu dựng giáo trình. Nạp **on-demand** — chỉ tải phần cần khi học, KHÔNG clone nguyên repo (tránh phá phân-vùng-code INV-17, tránh nặng, tránh rủi ro bản quyền). Ràng buộc: `reference/` **chỉ chứa `.md`** (lát cắt text), giữ INV-17 trên vault PASS.

**`exam/` (NGOÀI `learning_vault/`, ngang cấp — tùy chọn):** nơi người học nộp **bài thực hành**, có thể là **mã nguồn**. Đặt NGOÀI vault là có chủ đích: vault chỉ chứa "nội dung học + trạng thái máy-kiểm" (INV-17 cấm code lẫn trong vault), nên bài nộp dạng code phải nằm ngoài để **kho học luôn sạch** và INV-17 không chuyển PASS→FAIL. Trong vault chỉ lưu `exam_results.md` — **bản ghi CHẤM** (metadata: `submission_id`, `ref` tương đối tới bài nộp ở `exam/`, `target` là topic/Curriculum_Point, `graded_at`, `verdict`). Chất lượng bài nộp là **đánh giá Class D** (người/AI, KHÔNG phải chân lý máy); máy chỉ đảm bảo **toàn vẹn tham chiếu** (bài nộp + target tồn tại).

### 3.5. Giáo Trình `curriculum.md` — Học Nhiều Bài Theo Điểm (v2.7)

Với chủ đề lớn, một topic có thể có **giáo trình (Curriculum)** gồm nhiều **điểm cần học (Curriculum_Point)** theo thứ tự; mỗi điểm sinh ra một lesson. `curriculum.md` là front-matter máy-kiểm:

- `points[]`: mỗi điểm có `id` (`cp-NNN`), `order` (hoán vị 1..N), `objective` (không rỗng), `status` (`not_started|in_progress|done`), `lesson_id` (tham chiếu lesson đã sinh — tùy chọn), `source_refs[]` (trỏ file trong `reference/`).
- `current_point`: điểm đang học (phải trỏ một point tồn tại — INV-03).
- `teachable`: chỉ `true` khi **Curriculum_Validator PASS** (được-phép-sinh-lesson).

**Nguồn sự thật index bài vẫn là `topic_state.lessons[]` (INV-25)** — `curriculum.points[].lesson_id` CHỈ là tham chiếu, được validate khớp lesson có thật trên đĩa; giáo trình KHÔNG thay `topic_state` làm chỉ mục.

**Bổ sung điểm giữa chừng (R8):** có thể chèn một Curriculum_Point vào vị trí xác định (`/curriculum --insert-at <pos> --point <json>`) — điểm mới nhận `order=pos`, các điểm từ vị trí đó dịch +1 (giữ hoán vị 1..N+1), id mới duy nhất ổn định; id/tiến độ điểm cũ và `current_point` GIỮ NGUYÊN; validator re-check E-CURR-* trong cùng transaction (sai → rollback).

**Curriculum_Validator** (mở rộng của validator, xem `_system/rules/validation_rules.md`) kiểm cấu trúc/tham chiếu và phát 7 mã lỗi Class A: `E-CURR-DUP-ID`, `E-CURR-ORDER`, `E-CURR-EMPTY-OBJECTIVE`, `E-CURR-POINTER`, `E-CURR-LESSON-LINK`, `E-CURR-REF-BROKEN`, và `E-EXAM-REF-BROKEN` (cho `exam_results.md`). Sai schema chung vẫn do `E-SCHEMA` bắt (không nhân mã trùng). Đây là **Class A** (toàn vẹn cấu trúc/tham chiếu); còn "giáo trình đủ sâu/rộng/chính xác về tri thức" là **Class D** (người/AI đánh giá, không có mã lỗi).

---

## 4. Nguồn Sự Thật Duy Nhất (Single Source of Truth)

Đây là lời giải cho vấn đề đồng bộ lesson ↔ topic trong v1. Quy tắc tuyệt đối:

| Dữ liệu | Nguồn sự thật (sửa tay được) | View sinh tự động (KHÔNG sửa tay) |
|---------|------------------------------|-----------------------------------|
| Tiến độ & review item của một lesson | `lesson_state.md` của lesson đó | — |
| Lịch ôn toàn topic | — | `topic_state.md › review_schedule` (sinh từ mọi lesson) |
| Con trỏ đang học toàn vault | `vault_state.md` | `topic_state.current_lesson` chỉ là cache/index của topic hiện tại, phải khớp khi `topic_id == vault_state.current_topic` |
| Đánh giá năng lực topic | — | `topic_state.md › assessment` (tổng hợp từ lesson) |
| Cờ còn kiến thức draft | — | `topic_state.has_draft_knowledge` (sinh bằng cách đếm claim `status: draft`) |
| Danh mục lesson của topic | **thư mục `lessons/`** (sự thật vật lý) | `topic_state.lessons` (index, phải khớp folder); `topic.md` chỉ là kế hoạch học cho người đọc |
| `status` của lesson trong topic index | `lesson_state.md` của từng lesson | `topic_state.lessons[].status` phải được sinh/đồng bộ từ `lesson_state.status` |

Quy tắc sinh view:

- `topic_state.review_schedule` = hợp của mọi `review_items` trong tất cả `lesson_state.md` của topic, sắp theo `card.due_date` tăng dần, rồi `card.due_at_utc`.
- Mỗi view mang field `generated_from_hash` = hash của **đúng tập field nguồn nuôi view đó** (xem định nghĩa miền băm bên dưới). Khi validate, validator phải **sinh lại toàn bộ view object và deep-compare cả nội dung lẫn hash**. Hash không khớp → `E-VIEW-STALE`; hash khớp nhưng `items`/giá trị view khác object sinh lại → `E-VIEW-MISMATCH`. Chỉ so `generated_from_hash` là chưa đủ, vì AI có thể sửa view sai nhưng giữ nguyên hash cũ.
- **Dạng canonical cố định để hash không lệch giữa máy/OS:** `sha256( json.dumps(data, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode('utf-8') )`. Bắt buộc `ensure_ascii=False` (giữ nguyên tiếng Việt, không escape `đ`→`\u0111`) + `separators` cố định + encode UTF-8 trước khi băm.
- **Không đưa `float` thô vào hash (belt-and-suspenders).** Hai miền băm ở mục 4 cố ý CHỈ chứa string/int (`due_at_utc` và `due_date` là string, mastery là int 0..3) — không có float. Nếu sau này thêm field float vào view, PHẢI format thành **string cố định** (vd `f"{v:.4f}"`) trước khi băm. (Đính chính một hiểu lầm phổ biến: `json.dumps` của Python serialize cùng một giá trị float là **tất định** trên mọi CPU/OS cùng version Python — lệch không đến từ `dumps`. Lệch thật đến từ *phép tính* FSRS chạy trên CPU khác cho ra float hơi khác; chống bằng cách **làm tròn trước khi lưu** `stability`/`difficulty` theo `serialization`, mục 8.3 — chứ không phải bằng cách đổi cách `dumps`.)
- AI **không bao giờ** sửa tay view. Khi cần đổi lịch ôn, sửa ở `lesson_state.md` rồi sinh lại view.

**Miền băm (định nghĩa cố định — đây là mảnh chịu lực, phải pin chính xác):** `data` được băm là một **object đã chuẩn hoá**, KHÔNG phải nội dung file thô (tránh false-stale do đổi khoảng trắng/comment/thứ tự field YAML). Loại trừ tuyệt đối các field view (`generated_from_hash`, `review_schedule`, `assessment`) khỏi `data` để không tự tham chiếu vòng.

- `review_schedule.generated_from_hash` băm trên:
  ```text
  data = [
    {"lesson_id": L, "item_id": rv.id,
     "due_date": rv.card.due_date,
     "mastery_state": rv.mastery_state}
    for mỗi lesson L (sắp lesson_id asc) for mỗi rv trong L.review_items (sắp rv.id asc)
  ]
  ```
  Chỉ đúng 4 field này. **v2.6/F-B: `due_at_utc` KHÔNG vào hash** (không bit-identical cross-CPU do FSRS dùng float transcendental); trục lịch ôn chuẩn là `due_date` (ngày local). Đổi `prompt_ref`, `log`, `difficulty`, `due_at_utc`… mà không đổi (`due_date`,`mastery_state`) → KHÔNG coi là stale.
- `assessment.generated_from_hash` băm trên:
  ```text
  data = [
    {"lesson_id": L, "status": L.status,
     "mastery": {trục: L.mastery[trục].score for trục in 5 trục}}
    for mỗi lesson L có status in {learned, needs_review} (sắp lesson_id asc)
  ]
  ```
- `due_date` đưa vào băm dưới dạng chuỗi `YYYY-MM-DD` (chuẩn hoá theo `utc_offset`, mục 8.5). **`due_at_utc` KHÔNG vào hash** (v2.6/F-B). Không đưa object datetime thô vào hash.
- `has_draft_knowledge` không cần hash riêng: validator/FULL-regen tính trực tiếp `any(claim.status == "draft" for claim in topic.md/lesson_notes.md thuộc topic)` và ghi lại scalar này. AI không được sửa tay field này.

Hệ quả: không bao giờ có "hai file nói khác nhau", vì chỉ có một bên được sửa, bên kia là dẫn xuất kiểm được bằng cách sinh lại object, deep-compare nội dung, rồi so hash.

---

## 5. Schema Chuẩn (Máy Kiểm Được)

Mọi file `*_state.md` mở đầu bằng YAML front-matter theo schema cố định trong `_system/schemas/`. Validator kiểm từng field về: có mặt, đúng kiểu, đúng enum, đúng quan hệ.

### 5.1. `lesson_state.md`

```yaml
---
schema: lesson_state
schema_version: 1
lesson_id: "topic-name/lesson-001"        # phải khớp đường dẫn thư mục
title: "Tên lesson"
status: in_progress                        # enum: not_started|in_progress|learned|needs_review
created: 2026-06-30
updated: 2026-06-30                         # phải >= created, <= hôm nay
objective: "Mục tiêu một câu"
prerequisites: ["topic-name/lesson-000"]   # mỗi phần tử phải là lesson_id tồn tại
sections_done: ["first_principles", "feynman"]
sections_pending: ["socrates", "teachback"]
mastery:                                    # rubric rời rạc, mục 9; mỗi trục = score + bằng chứng
  concept:   { score: 2, evidence: ["ev-20260630-001"] }   # evidence trỏ block trong lesson.md
  explain:   { score: 2, evidence: ["ev-20260630-002"] }
  apply:     { score: 1, evidence: ["ev-20260630-003"] }
  critique:  { score: 0, evidence: [] }
  teachback: { score: 0, evidence: [] }
open_gaps:                                  # điểm chưa chắc, mỗi cái có id để truy vết
  - id: gap-001
    desc: "Nhầm giữa X và Y"
    detected: 2026-06-30
review_items:                               # NGUỒN SỰ THẬT của review; engine = FSRS (mục 8)
  - id: rv-001
    prompt_ref: "lesson.md#q3"             # trỏ heading "#### Question q3" trong lesson.md (mục 14A)
    fsrs_config_version: 1                  # version cấu hình FSRS dùng cho item này (mục 8.3)
    created: 2026-06-30                      # ngày tạo item; mốc khởi tạo card cho replay (mục 8.5)
    card:                                   # trạng thái thẻ FSRS (thư viện sinh, KHÔNG sửa tay)
      state: Review                         # enum: Learning|Review|Relearning (py-fsrs KHÔNG có New — v2.6/F-A)
      step: 0                               # bước learning/relearning
      stability: 12.34                      # ngày; NULL khi chưa review (log rỗng)
      difficulty: 5.41                      # 1..10; NULL khi chưa review
      due_at_utc: "2026-07-12T13:00:00Z"    # datetime UTC authoritative từ FSRS
      due_date: 2026-07-12                  # date local dẫn xuất từ due_at_utc + vault_state.utc_offset
      last_reviewed_at_utc: "2026-06-30T13:00:00Z"   # NULL khi chưa review (log rỗng)
    log:                                    # EVENT LOG → validator replay xác định (mục 8.5)
      - reviewed_at: "2026-06-30T20:00:00+07:00"
        rating: 3                           # 1=Again 2=Hard 3=Good 4=Easy
    mastery_state: in_review                # lớp phủ TÍNH ĐƯỢC: new|in_review|need_redo|mastered
next_action: "Buổi sau: kiểm tra teach-back phần Socrates"
last_session: 2026-06-30
---
```

Ghi chú về `evidence`: mỗi phần tử là id của một **evidence block** nằm trong `lesson.md` (mục 5.5). Trục nào đạt ngưỡng cổng (mục 9.3) mà thiếu evidence → `E-ASSESS-NOEVIDENCE`.

Ghi chú về **item mới tạo** (chưa review lần nào): `card.state = Learning` (py-fsrs không có `New` — v2.6/F-A), `step = 0`, `stability = null`, `difficulty = null`, `last_reviewed_at_utc = null`, `log = []`, `mastery_state = new`; `due_at_utc` = thời điểm `created` (chuẩn hoá UTC), `due_date` chiếu theo `utc_offset`. Schema (pydantic) phải khai `stability`/`difficulty`/`last_reviewed_at_utc` là **Optional** và ràng buộc: khi `log == []` (chưa review) thì các field này PHẢI null; khi `log != []` thì `stability`/`difficulty` PHẢI có giá trị. "Chưa review" nhận biết bằng **`log` rỗng / `last_reviewed_at_utc == null`**, KHÔNG bằng một `State.New` (không tồn tại). Replay INV-08 bắt đầu từ card mới (`Learning`, log rỗng).

### 5.2. `topic_state.md`

```yaml
---
schema: topic_state
schema_version: 1
topic_id: "topic-name"
title: "Tên topic"
current_lesson: "topic-name/lesson-001"     # cache/index: nếu topic này là vault_state.current_topic thì phải khớp vault_state.current_lesson
has_draft_knowledge: true                    # VIEW SINH TỰ ĐỘNG: true nếu còn claim status=draft (mục 15.1)
lessons:                                     # INDEX (được kiểm), KHÔNG phải nguồn gốc
  - id: "topic-name/lesson-001"              # nguồn gốc = thư mục lessons/; index phải khớp folder
    status: in_progress                      # view từ lesson_state.status, không sửa tay độc lập
created: 2026-06-30
updated: 2026-06-30
review_schedule:                             # VIEW SINH TỰ ĐỘNG, không sửa tay
  generated_from_hash: "sha256:..."
  items:
    - lesson_id: "topic-name/lesson-001"
      item_id: rv-001
      due_date: 2026-07-12
      mastery_state: in_review
assessment:                                  # VIEW SINH TỰ ĐỘNG từ mastery các lesson
  generated_from_hash: "sha256:..."
  concept_avg: 2.0
  explain_avg: 2.0
  apply_avg: 1.0
  critique_avg: 0.0
  teachback_avg: 0.0
---
```

### 5.3. `sources.md` (mỗi nguồn một khối có status)

```yaml
---
schema: sources
schema_version: 1
topic_id: "topic-name"
sources:
  - id: src-001
    kind: doc            # enum: doc|link|repo|book|note|question
    ref: "https://..."   # hoặc đường dẫn / mô tả
    status: raw          # enum: raw|processing|confirmed|rejected
    trust: unknown       # enum: unknown|low|medium|high
    scope: "Dùng cho lesson 1-2"
    added: 2026-06-30
    anchors:                       # neo trích dẫn; chỉ tạo khi status=confirmed
      - id: a2                     # claim B trỏ tới "src-001#a2"
        locator: "trang 3 / mục 'RTU framing' / dòng 12"
        quote: "<trích NGUYÊN VĂN đoạn nguồn>"
        summary: "<diễn giải ngắn ý dùng>"
        content_hash: "sha256:..." # (tùy chọn) hash đoạn trích để phát hiện nguồn đổi
---
```

Quy tắc cứng: chỉ nguồn `status: confirmed` mới được dùng làm anchor cho khẳng định lớp B. Dùng nguồn `raw` làm căn cứ kiến thức → `E-SRC-RAWUSED`.

### 5.4. `vault_state.md` (con trỏ + chính sách ngày)

```yaml
---
schema: vault_state
schema_version: 1
utc_offset: "+07:00"         # offset cố định để tính ngày (stdlib datetime.timezone, không cần tzdata)
date_policy: local_date      # "hôm nay" = ngày hiện tại theo utc_offset trên (không UTC trôi)
day_cutoff_hour: 4           # giờ cắt ngày kiểu Anki (mục 8.5); 0 = cắt đúng nửa đêm
current_topic: "topic-name"
current_lesson: "topic-name/lesson-001"
export_policy: private_full  # private_full | shareable_clean | template_only
open_session:                # con trỏ phiên CHƯA đóng sổ (mục 11B.2); null nếu không có phiên dở
  lesson_id: null            # lesson đang mở phiên; null = sạch
  started_at: null           # timestamp mở phiên (theo utc_offset)
  last_full_validate: 2026-06-30T20:00:00+07:00  # lần cuối qua FULL-validate (mục 10.8)
---
```

Trường `open_session` là **cờ đóng-sổ** cho phép phát hiện phiên bị bỏ dở (mục 11B.2):

- `/learn`, `/resume` mở phiên → ghi `open_session.lesson_id` + `started_at` (chính nó là một transaction nhỏ).
- `/done` FULL-validate PASS → set `open_session.lesson_id = null` và cập nhật `last_full_validate`.
- `/status` đọc cờ: nếu `open_session.lesson_id != null` → cảnh báo "phiên trước chưa `/done`" và đề xuất chạy `/done` hoặc `/validate` trước.
- Validator KHÔNG coi `open_session != null` là lỗi (phiên dở là hợp lệ tạm thời); nó chỉ là tín hiệu UX. Nhưng tại `/done`, sau khi FULL PASS, cờ PHẢI được clear trong cùng transaction.

`export_policy` chi phối khi chia sẻ vault cho người khác (vault chứa câu trả lời, điểm yếu, lịch học cá nhân):

- `private_full`: giữ nguyên toàn bộ (mặc định, dùng cho chính mình).
- `shareable_clean`: bỏ evidence/transcript/`open_gaps`/mastery cá nhân khi export, giữ cấu trúc + nội dung học.
- `template_only`: chỉ giữ topic/lesson/knowledge map làm khuôn, bỏ mọi trạng thái cá nhân.

Việc export theo policy là thao tác **sinh bản sao** (không sửa vault gốc); chưa nằm trong phạm vi validator, đánh dấu là việc triển khai (mục 20).

Mọi phép tính ngày (due, "hôm nay cần ôn gì", created/updated) dùng `utc_offset` này, qua `datetime.timezone` của stdlib — **không cần `tzdata`/`zoneinfo`**, chạy được trên mọi máy kể cả Windows. Thiếu `utc_offset` → fallback UTC (`+00:00`), nhưng phải báo cảnh báo.

### 5.5. Claim & Evidence Contract (vá P0-1, P0-2)

Đây là hợp đồng giúp validator kiểm được phân lớp khẳng định (mục 0.1) và bằng chứng năng lực (mục 9.3) — thay vì chỉ là khẩu hiệu.

**Phạm vi claim (cố ý hẹp để khả thi):** mọi claim trong mục `## Claims` của `lesson_notes.md` và `topic.md` phải mang `class` + `status`. Chỉ claim `status: confirmed` mới là kiến thức chính thức; claim `status: draft` là ghi chú làm việc chưa nguồn-hoá. Hội thoại/transcript trong `lesson.md` KHÔNG phải claim. Claim nằm ngoài vùng cho phép → `E-CLAIM-LOC`.

**Định dạng máy-đọc-được (bắt buộc):** dưới heading `## Claims` phải có **một fenced code block ```yaml``` chứa key `claims:`**. Validator parse bằng AST (`markdown-it-py`): tìm node `heading` text = `Claims`, rồi **duyệt tiến tới node `fence` (info=`yaml`) ĐẦU TIÊN trước khi gặp heading kế cùng cấp/cao hơn** (cho phép có node prose chen giữa, mục 19), rồi `yaml.safe_load`. KHÔNG quét YAML bằng regex trên prose.

````markdown
## Claims

```yaml
claims:
  - id: clm-001
    class: B                       # A|B|C|D
    status: confirmed              # draft|confirmed (mục 15.1)
    text: "Modbus RTU là giao thức master-slave trên bus half-duplex."
    source_refs: ["src-003#a2"]    # bắt buộc nếu status=confirmed & class B
    premise_refs: []               # bắt buộc nếu status=confirmed & class C (mỗi tiền đề là id claim A/B confirmed)
    draft_reason: null             # bắt buộc nếu status=draft; null nếu confirmed
```
````

**Evidence block** (đặt trong `lesson.md`, là nơi `mastery.<trục>.evidence` trỏ tới). Quy ước cố định: heading **cấp 4** `#### Evidence <ev-id>` (nằm trong session block, mục 14A), **theo sau là một fenced ```yaml``` block** chứa các field. Validator: tìm node `heading` (level 4) text khớp `^Evidence (ev-\S+)$`, **duyệt tiến tới node `fence` (info=`yaml`) đầu tiên trước heading kế cùng/cao cấp hơn** (bỏ qua node prose chen giữa, mục 19), `yaml.safe_load`.

````markdown
#### Evidence ev-20260630-002

```yaml
axis: explain                      # một trong 5 trục rubric
timestamp: 2026-06-30
quote: "<trích NGUYÊN VĂN câu trả lời của người học>"
ai_assessment: "<nhận xét vì sao đạt mức điểm>"
```
````

Validator kiểm claim: mọi claim có đủ `id/class/status/text`; nếu `status=confirmed` thì áp luật lớp đầy đủ (B phải có `source_refs` confirmed; C phải có `premise_refs` đều là claim A/B confirmed); nếu `status=draft` thì phải có `draft_reason`, không được làm tiền đề cho C confirmed, không được vào `## Knowledge Map`.

Validator kiểm evidence: evidence tồn tại, `axis` khớp trục, `quote` không rỗng và là verbatim-substring của transcript (INV-22b). Việc quote có "thật sự hiểu" hay không vẫn là lớp D (giới hạn ở mục 0.3), nhưng giờ **audit được**.

> **Lưu ý parser:** "không dùng regex" áp cho việc *dò cấu trúc* trên thân Markdown (heading/claims/evidence/question). Việc khớp **token tiêu đề** đã chuẩn hoá (`Claims`, `Evidence ev-…`, `Question q…`) trên *text của node heading do AST trả về* là cho phép — đó không phải quét prose tự do. Mọi nội dung field nằm trong fenced YAML, parse bằng `yaml.safe_load`, không bao giờ bằng regex dòng.

---

## 6. Máy Trạng Thái (State Machines)

Chuyển trạng thái phải hợp lệ theo máy trạng thái cố định. Chuyển sai → `E-STATE-ILLEGAL`.

### 6.1. Lesson `status`

```text
not_started ──► in_progress ──► learned
                    │  ▲           │
                    ▼  │           ▼
                 needs_review ◄────┘
```

- `in_progress → learned`: **chỉ khi** cổng "đã hiểu" (mục 9.3) thỏa. Nếu không → bị chặn.
- `learned → needs_review`: khi tới hạn ôn hoặc phát hiện lỗ hổng mới.
- Không có cạnh `not_started → learned`.

### 6.2. Review item: `card.state` (FSRS) + lớp phủ `mastery_state`

Có hai tầng, KHÔNG mâu thuẫn vì mỗi tầng do một nguồn quản:

1. **`card.state`** — do thư viện FSRS quản (`New → Learning → Review ↔ Relearning`). Hệ thống không tự đặt; chỉ nhận kết quả từ scheduler.
2. **`mastery_state`** — lớp phủ của hệ thống, **tính thuần** từ `card` + `log`:

```text
derive_mastery(card, log) =
  new          nếu log rỗng (chưa review lần nào — last_reviewed_at_utc == null)
  need_redo    nếu rating của bản ghi cuối trong log == 1 (Again)  HOẶC card.state == Relearning
  mastered     nếu card.state == Review  AND  card.stability >= MASTERED_STABILITY (mục 8.3)
  in_review    còn lại
```

(v2.6/F-A: py-fsrs không có `State.New`; thẻ mới là `State.Learning` với `log` rỗng. Tín hiệu "mới" = log rỗng, không phải state.)

Vì `mastery_state` là hàm thuần của (`card`, `log`), validator tính lại và so khớp giá trị đang lưu. Lệch → `E-STATE-DERIVED`. Không có chuyển trạng thái "tự do" nên không thể mâu thuẫn như bản box cũ.

---

## 7. Thuật Toán Sinh View Từ Nguồn Sự Thật

Thuật toán sinh `topic_state.review_schedule` (xác định):

```text
function build_topic_review(topic):
    items = []
    for each lesson in topic.lessons (sắp theo lesson_id tăng dần):
        for each rv in lesson.review_items (sắp theo rv.id tăng dần):
            items.append({lesson_id, item_id: rv.id,
                          due_date: rv.card.due_date,
                          mastery_state: rv.mastery_state})
    sort items by (due_date asc, lesson_id asc, item_id asc)  # khóa cố định (v2.6/F-B: bỏ due_at_utc)
    hash = sha256( canonical_json(data) )                 # data = miền băm review_schedule (mục 4), KHÔNG băm file thô
    return { generated_from_hash: hash, items }
```

Khóa sắp xếp cố định đảm bảo: cùng dữ liệu vào → cùng thứ tự ra, mọi phiên AI đều giống nhau.

---

## 8. Engine Lịch Ôn: FSRS (Deterministic — Lõi Giá Trị)

Hệ thống **không tự nuôi thuật toán lịch ôn**. Nó dùng **FSRS** (Free Spaced Repetition Scheduler — thư viện `fsrs`/py-fsrs, MIT, mô hình DSR) làm engine duy nhất, để khỏi phải bảo trì một biến thể Leitner yếu hơn. Mọi tính toán phải **tái lập được ở mọi phiên**.

### 8.1. Thang chấm rubric (0..3) → rating FSRS (1..4)

Người chấm dùng rubric rời rạc 0..3 (quan sát được); hệ thống ánh xạ **cố định** sang rating FSRS:

| grade (rubric) | Ý nghĩa | rating FSRS |
|---|---|---|
| 0 | Quên / sai bản chất | 1 = Again |
| 1 | Nhớ mơ hồ / sai một phần | 2 = Hard |
| 2 | Đúng nhưng chưa trôi chảy | 3 = Good |
| 3 | Đúng, trôi chảy, tự giải thích | 4 = Easy |

Ánh xạ này khóa trong `_system/rules/review_rules.md`. Đổi nó phải qua change request.

### 8.2. Trạng thái thẻ (do FSRS quản)

Mỗi review item lưu một `card`: `state` (Learning|Review|Relearning — py-fsrs không có New, v2.6/F-A), `step`, `stability` (ngày), `difficulty` (1..10), `due_at_utc` (datetime UTC authoritative), `due_date` (date local dẫn xuất để lọc/sắp lịch), `last_reviewed_at_utc`; cộng `log` (mỗi lần review: `reviewed_at`, `rating`) và `fsrs_config_version`.

### 8.3. Cấu hình Scheduler (cố định để deterministic)

Lưu trong `_system/fsrs_config.yaml`, gắn version theo `_system/VERSION`. Để replay khớp tuyệt đối giữa các máy, phải **pin đầy đủ**, không dựa vào "mặc định thư viện":

- `fsrs_package_version`: ghim chính xác, ví dụ `fsrs==6.3.1` (bản hiện hành 2026-03, MIT, `requires_python >=3.10`, runtime chỉ phụ thuộc `typing-extensions`). Đổi version package = tạo `fsrs_config_version` mới.
- `parameters`: **liệt kê đầy đủ 21 weights** của FSRS-6 (model `fsrs==6.x` dùng đúng 21 số; bản 5.x là 19, 4.x là 17 — KHÔNG trộn version với số weights). Ghi thẳng cả 21 số trong file, không để thư viện tự điền mặc định.
- `desired_retention`: ví dụ `0.9`.
- `learning_steps`, `relearning_steps`: cấu hình theo nhịp học ngày.
- `maximum_interval`: ví dụ `36500`.
- `enable_fuzzing`: **false** (bắt buộc — fuzzing thêm ngẫu nhiên, phá tái lập).
- `MASTERED_STABILITY`: ngưỡng ngày để coi là `mastered` (ví dụ `60`).
- `serialization`: chốt độ chính xác khi lưu `stability`/`difficulty` (làm tròn 4 chữ số) để giảm nhiễu float. So khớp dùng `math.isclose(abs_tol=1e-4)`, không `==`. **(v2.6/F-B — đính chính theo SPIKE):** py-fsrs tính `due` NỘI BỘ trong `review_card` từ stability (không có hook "quantize trước khi tính due", cũng không có formula interval public). Do đó KHÔNG thể ép due tất định bit-level cross-CPU. Quy ước thực thi: lấy `due` từ `review_card` như-là; **`due_date` (ngày local) là trục lịch ôn + so khớp chuẩn** (INV-08); `due_at_utc` chỉ deterministic cho `Learning/Relearning` (bước cố định) nên chỉ so exact ở hai trạng thái đó; `due_at_utc` KHÔNG nằm trong hash view (mục 4). Đánh đổi: lịch Review theo ngày — không ảnh hưởng sư phạm.
- `due_projection`: **bắt buộc** — FSRS trả `due` dạng `datetime`. Hệ thống lưu **cả hai**: `due_at_utc = due_datetime.astimezone(UTC)` theo dạng canonical `YYYY-MM-DDTHH:MM:SSZ` (aware UTC, `microsecond=0`; adapter phải chuẩn hoá input/output về giây), và `due_date = due_at_utc.astimezone(tz(utc_offset)).date()` theo dạng `YYYY-MM-DD`. Cả lúc ghi lẫn lúc replay đều áp đúng quy tắc này. **So khớp (v2.6/F-B):** `due_date` so **date thuần** ở MỌI trạng thái (trục chuẩn); `due_at_utc` so **exact CHỈ khi** `state in {Learning, Relearning}` (bước cố định, deterministic), KHÔNG so ở `Review`. Vẫn lưu cả hai (không chỉ date) vì Learning/Relearning có bước trong ngày; nhưng `due_at_utc` của `Review` là thông tin, không dùng để bắt lỗi replay.

Mỗi `fsrs_config_version` là **bất biến**: đã phát hành thì không sửa, chỉ tạo version mới (giữ replay quá khứ đúng). Golden fixtures (mục 10.6) phải có ca replay khóa cứng input → output cho mỗi version.

**Không** dùng `fsrs-optimizer` trong luồng thường: tối ưu tham số cá nhân hóa làm mất tái lập giữa các máy và kéo dependency ML nặng.

### 8.4. Quy trình cập nhật một lần review

```text
function review(item, grade, reviewed_at):
    rating = MAP_GRADE_TO_RATING[grade]              # bảng 8.1; grade ∉ 0..3 → E-REVIEW-BADGRADE
    card   = build_card(item.card)                   # dựng Card FSRS từ trạng thái đã lưu
    scheduler = Scheduler(fsrs_config[item.fsrs_config_version])
    reviewed_at_utc = reviewed_at.astimezone(timezone.utc)   # py-fsrs CHỈ nhận UTC (mục 8.5)
    new_card, _ = scheduler.review_card(card, rating, reviewed_at_utc)
    item.card = serialize(new_card)                  # state/step/stability/difficulty/due_at_utc/due_date/last_reviewed_at_utc
    item.log.append({reviewed_at, rating})           # log lưu ở offset địa phương; convert UTC khi replay
    item.mastery_state = derive_mastery(item.card, item.log)   # hàm thuần, mục 6.2
    return item
```

Pseudocode trên chỉ mô tả **logic**, KHÔNG phải API chắc chắn của package `fsrs`. Khi code phải bọc qua `_system/validator/fsrs_adapter.py` (ánh xạ sang `Scheduler`/`Card`/`Rating` thật của version đã pin) và có golden test nhỏ chứng minh replay khớp, rồi validator mới gọi adapter — không gọi thẳng theo pseudocode.

### 8.5. Quy tắc xác định & cách validator kiểm

- **Chính sách thời gian:** `reviewed_at` lưu kèm offset theo `vault_state.utc_offset` để người đọc dễ audit; mọi datetime đưa vào/nhận ra từ FSRS đều chuẩn hoá UTC; `due_date` là date local dẫn xuất từ `due_at_utc`; "hôm nay" = ngày hiện tại theo offset đó (mục 5.4), tính bằng `datetime.timezone` stdlib. Không dùng UTC trôi, không cần tzdata.
- **⚠️ py-fsrs CHỈ nhận UTC (xác nhận từ README 6.x):** khi gọi `scheduler.review_card(card, rating, review_datetime)`, `review_datetime` PHẢI là `datetime` aware ở **UTC**. Vì vậy: lưu `reviewed_at` ở offset địa phương cho người đọc, nhưng **trước khi đưa vào FSRS phải `.astimezone(timezone.utc)`**. `due` FSRS trả về cũng chuẩn hoá thành `due_at_utc`, rồi chiếu sang `due_date` bằng `due_projection` (mục 8.3). Cả lúc ghi lẫn lúc replay đều theo đúng chuỗi `local→UTC vào / UTC authoritative ra / UTC→local-date dẫn xuất`; lệch quy ước = replay sai (`E-REVIEW-MISCALC`). Đây là kẽ hở determinism dễ bị bỏ sót nhất khi code.
- **Tái lập (thay cho field rời rạc thiếu dữ kiện):** validator dựng lại card bằng cách **replay toàn bộ `log`** qua `Scheduler` với đúng `fsrs_config_version`, **bắt đầu từ một card khởi tạo chuẩn `state=Learning`, `log` rỗng, tạo tại `created`** (py-fsrs không có `New`, v2.6/F-A). Kết quả phải khớp `item.card` đang lưu. Lệch → `E-REVIEW-MISCALC`. Đây là cách lịch ôn đạt "đúng tuyệt đối".
- **Mốc khởi tạo:** mọi item mặc định khởi tạo từ card `Learning`/log rỗng tại `created`. Import từ trạng thái khác (`initial_card`) — **DEFERRED** (chưa hỗ trợ GĐ1); khi làm phải lưu `initial_card` tường minh để replay có baseline.
- **Khóa version để không "đổi luật làm lệch quá khứ":** mỗi item ghi `fsrs_config_version`; replay luôn dùng đúng version đó. Đổi cấu hình = tạo version mới, không sửa version cũ.
- **"Cần ôn hôm nay"** = mọi item tới hạn, BẤT KỂ `mastery_state` (gồm cả `mastered`), sắp theo khóa hai tầng: trước hết theo **nhóm ưu tiên** `priority(mastery_state)`, sau đó theo khóa cố định `(card.due_date asc, card.due_at_utc asc, lesson_id asc, item_id asc)`. Trong đó `priority`: `need_redo = 0` (gấp nhất) → `in_review = 1` → `mastered = 2` (thấp nhất). Lý do gộp cả `mastered`: nếu loại hẳn `mastered` khỏi danh sách thì thẻ đã thành thạo tới hạn sẽ KHÔNG bao giờ được củng cố, `stability` không cập nhật, kẹt `mastered` vĩnh viễn dù trí nhớ đã nguội — đó là lỗ hổng. Gộp + ưu tiên thấp giữ đúng tinh thần FSRS: vẫn ôn để duy trì, nhưng nhường chỗ cho thẻ yếu trước.
- **Quy tắc tới hạn tách day-card và step-card:** nếu `card.state in {Learning, Relearning}` thì dùng datetime chính xác: `due_at_utc <= now_utc` (để không làm mất bước trong ngày). Nếu `card.state == Review` thì dùng ngày logic: `card.due_date <= logical_today`. `New` chỉ xuất hiện trong danh sách khi item được chọn học/ôn mới theo lệnh, không tự "quá hạn".
- **"Hôm nay" có giờ cắt ngày (day cutoff, kiểu Anki):** `logical_today = (now_local - timedelta(hours=day_cutoff_hour)).date()` với `now_local` theo `utc_offset`. Mặc định `day_cutoff_hour=4` → học lúc 23:45 rồi tới 00:01 review-card ngày mai KHÔNG lập tức "tới hạn" giữa buổi (vì trước 04:00 vẫn tính là "hôm qua"). **Phạm vi áp dụng hẹp, cố ý:** giờ-cắt CHỈ dùng cho phép lọc review-card theo `due_date`; **KHÔNG** áp cho `due_at_utc`, **KHÔNG** áp cho dấu ngày `created`/`updated` (những field này dùng ngày lịch thật theo `utc_offset`), để không phá `INV-05` (`created <= updated <= today`). `INV-05` dùng `today` = ngày lịch thật; phép lọc ôn dùng `logical_today`. Hai mốc tách biệt, không trộn.
- **Bỏ qua** (chuyển sang học tiếp): KHÔNG gọi `review()`, KHÔNG ghi log, giữ nguyên card.
- **Không trùng:** mỗi `prompt_ref` chỉ một item (`E-REVIEW-DUP`).

---

## 9. Rubric Đánh Giá Rời Rạc (Chống Chủ Quan)

Thay cho phán đoán định tính của v1. Năm trục, mỗi trục 0..3, mỗi mức có mô tả hành vi cụ thể để hai AI chấm giống nhau.

### 9.1. Năm trục

`concept` (hiểu khái niệm), `explain` (giải thích bằng lời thường), `apply` (áp dụng), `critique` (phản biện / nhận lỗi sai), `teachback` (dạy lại).

### 9.2. Mô tả mức cho từng trục (rubric)

Ví dụ trục `explain`:

```text
0: Không diễn đạt lại được, chỉ lặp từ khóa.
1: Diễn đạt được nhưng sai hoặc thiếu ý lõi.
2: Diễn đạt đúng ý lõi bằng lời thường, còn vài chỗ lúng túng.
3: Diễn đạt rõ ràng, có ví dụ riêng, không cần nhìn tài liệu.
```

(Mỗi trục có bảng tương tự trong `_system/rules/teaching_rules.md`.)

### 9.3. Cổng "đã hiểu" (gate để lesson → learned)

Đây là chỗ v1 còn lỏng. Quy tắc cứng, tính được:

```text
learned_gate(mastery) == true  KHI VÀ CHỈ KHI:
    concept   >= 2  AND
    explain   >= 2  AND
    apply     >= 2  AND
    critique  >= 1  AND
    teachback >= 2
AND mỗi trục đạt mức đó phải có >= 1 BẰNG CHỨNG trích nguyên văn câu trả lời của người học,
   kèm timestamp, lưu trong evidence block của lesson.md (`#### Evidence`, đối chiếu `#### Bạn trả lời <qid>`).
```

- Không một câu trả lời đúng đơn lẻ nào nâng được trạng thái. Cần đủ nhiều trục + bằng chứng.
- Bằng chứng là **trích nguyên văn**, không phải AI tóm tắt lại (tránh AI tự huyễn).
- Thiếu bằng chứng cho một trục đã chấm ≥ ngưỡng → `E-ASSESS-NOEVIDENCE`.

### 9.4. Tổng hợp lên topic (tính được)

`assessment.<trục>_avg` = trung bình cộng mastery của các lesson `status in {learned, needs_review}`, làm tròn 1 chữ số. Là view sinh tự động, có hash.

### 9.5. Calibration Rubric Bằng Few-Shot (Giảm Lệch Chấm Giữa Các Phiên)

Lớp D không được enforce tái lập (mục 0.3); cách *giảm* phương sai chấm điểm là **neo rubric bằng ví dụ cụ thể**, không chỉ mô tả mức trừu tượng. Quy tắc:

- `_system/rules/teaching_rules.md` PHẢI chứa, cho **mỗi trục** trong 5 trục, **≥ 3 ví dụ chấm mẫu** (anchored examples): một câu trả lời mẫu + điểm rubric tương ứng + một dòng lý do. Tối thiểu phủ các mốc 1, 2, 3.
- Khi chấm, AI tham chiếu các ví dụ neo này trước khi gán điểm; nhận xét trong `evidence.ai_assessment` nên chỉ rõ "gần với ví dụ neo mức N vì...".
- Đây là kỷ luật *vận hành* để tăng nhất quán, KHÔNG phải bất biến validator (validator vẫn chỉ kiểm evidence tồn tại + verbatim, mục 9.3/INV-22b). Nó thu hẹp khoảng "hai AI chấm lệch", không khử được — đúng giới hạn ở mục 0.3.
- (Khuyến nghị kiểm thử: định kỳ cho hai phiên AI chấm cùng một transcript với cùng bộ ví dụ neo, đo độ lệch điểm; lệch lớn = rubric/ví dụ chưa đủ chặt, cần bổ sung ví dụ.)

### 9.6. Chuẩn Hoá Khi So Khớp Verbatim (INV-22b) — Cân Bằng Chặt/Lỏng

LLM hay "chuẩn hoá ngầm" khi trích dẫn (gộp khoảng trắng dư, đổi `"` thẳng thành `"` cong, đổi gạch nối). Nếu so khớp trên raw string sẽ ném `E-ASSESS-FAKEQUOTE` oan; nếu chuẩn hoá quá tay sẽ phá luôn tác dụng chống bịa. Quy ước **chốt cứng — chỉ chuẩn hoá hình thức, GIỮ nội dung**:

```text
normalize_for_match(s):
  1. Unicode NFC (gộp tổ hợp dấu — quan trọng cho tiếng Việt).
  2. Quy về dấu nháy/gạch chuẩn: “ ” „ ‟ → " ; ‘ ’ → ' ; – — → -
  3. Chuẩn hoá Markdown inline về plain text trên CẢ quote và transcript:
     bỏ delimiter thuần định dạng (`**`, `__`, `*`, `_`, `~~`, backtick code-span)
     nhưng giữ nguyên chữ bên trong; KHÔNG render HTML, KHÔNG bỏ dấu câu nội dung.
  4. Gộp mọi chuỗi whitespace/newline liên tiếp thành MỘT space; trim hai đầu.
  → so khớp: normalize(quote) ⊆ normalize(transcript_block)
```

Quy tắc Markdown phải **hẹp**: chỉ bỏ ký hiệu định dạng bao quanh text thuần để câu `chia sẻ **kernel**` khớp quote `chia sẻ kernel`; không được xoá ký tự có nghĩa trong code/identifier (vd `__init__`, `a_b`, `C++`, `x*y`) nếu ký tự đó là nội dung. Cách chắc nhất khi code: dùng `markdown-it-py` parse inline rồi lấy text content của token text/code_inline, thay vì tự viết regex xoá mọi dấu `*`/`_`.

**KHÔNG** lowercase, **KHÔNG** bỏ dấu câu, **KHÔNG** bỏ dấu tiếng Việt. Lý do: hạ chữ thường + xoá dấu câu sẽ khiến hai câu trả lời rất khác nhau cùng "khớp", mở lại đúng lỗ bịa mà INV-22b muốn bịt (đặc biệt với tiếng Việt, bỏ dấu làm "má/mà/mả" thành một). Chuẩn hoá ở đây chỉ tha thứ khác biệt **hình thức không mang nghĩa**, không tha thứ khác biệt nội dung.

---

## 10. Hệ Thống Validation (Lõi "Chính Xác Tuyệt Đối")

### 10.1. Validator dạng code, không phải LLM tự kiểm

Điểm mấu chốt: **AI có nhiệm vụ làm file đúng; một script có nhiệm vụ chứng minh file đúng.** Tách hai vai này là cách duy nhất đạt đúng tuyệt đối ở tầng cấu trúc.

`_system/validator/validate.py` chạy được độc lập (Python, không phụ thuộc nặng). CLI nhận **cả hai gốc** vì validator cần đọc luật/config/schema/migrations ở `_system/` lẫn dữ liệu ở `learning_vault/`:

```text
validate.py --system <đường dẫn _system> --vault <đường dẫn learning_vault> [--json]

exit 0  + report "PASS"            nếu mọi bất biến đúng
exit 1  + danh sách {error_code, file, field, message}  nếu có vi phạm
```

AI **không được** tự tuyên bố "đã valid". AI phải **chạy validator và dán kết quả**. Chưa chạy validator mà nói đã đúng → vi phạm luật, coi như chưa làm.

### 10.2. Danh Sách Bất Biến (Invariants) — Phải Đúng Sau MỌI Lần Ghi

Validator kiểm tất cả. Bất kỳ cái nào sai → thao tác bị coi là **không hợp lệ và phải hoàn tác (rollback)**, không commit.

Toàn vẹn cấu trúc:

- `INV-01` Mọi `*_state.md` có front-matter đúng schema, đủ field bắt buộc, đúng kiểu/enum.
- `INV-02` `lesson_id` / `topic_id` khớp đúng đường dẫn thư mục.
- `INV-03` Mọi tham chiếu (`prerequisites`, `current_lesson`, `lessons[].id`, `prompt_ref`) trỏ tới đối tượng tồn tại.
- `INV-04` ID duy nhất trong phạm vi: `gap-*`, `rv-*`, `src-*` không trùng.
- `INV-05` `created <= updated <= today`; mọi field ngày đúng định dạng `YYYY-MM-DD`.

Toàn vẹn ngữ nghĩa:

- `INV-06` Mọi chuyển `status` lesson/item nằm trong cạnh hợp lệ của máy trạng thái (mục 6). **Điều kiện kiểm:** chỉ enforce cạnh chuyển trạng thái khi validator chạy trong transaction có baseline backup/snapshot (mục 10.3), so `backup → staged`. Khi chạy FULL ngoài transaction, validator chỉ kiểm giá trị hiện tại thuộc enum và các hệ quả tĩnh (vd `learned` phải qua gate); nó KHÔNG được tự nhận đã kiểm lịch sử chuyển trạng thái nếu không có baseline.
- `INV-07` `status: learned` ⇒ `learned_gate(mastery)` đúng VÀ đủ bằng chứng (mục 9.3).
- `INV-08` Mỗi review item: replay toàn bộ `log` qua FSRS (đúng `fsrs_config_version`) phải khớp `card` đang lưu (mục 8.5). So khớp `stability`/`difficulty` bằng `math.isclose(abs_tol=1e-4)` (KHÔNG `==` float). **(v2.6/F-B)** So `due_date` **exact** (trục chuẩn cho mọi trạng thái). So `due_at_utc` **exact CHỈ khi** `state in {Learning, Relearning}` (bước cố định từ config → deterministic); ở `state == Review` KHÔNG so `due_at_utc` (chỉ tin `due_date`, vì `due` do FSRS tính từ float transcendental không bit-identical cross-CPU). Lệch → `E-REVIEW-MISCALC`.
- `INV-09` `topic_state.review_schedule` và `assessment` phải khớp **toàn bộ object sinh lại** từ nguồn hiện tại: deep-compare `items`/giá trị view trước, rồi so `generated_from_hash`. Nội dung view lệch → `E-VIEW-MISMATCH`; hash lệch → `E-VIEW-STALE`.
- `INV-10` Không review item nào trùng `prompt_ref`.
- `INV-11` Không item nào có `mastery_state in {in_review, need_redo}` **biến mất ngoài luồng xoá có thẩm quyền** giữa hai lần ghi. **Baseline để so sánh = bản backup trong `.tx/<tx_id>/` của chính transaction đang chạy** (mục 10.3); validator so tập review item ở backup với tập đang staged — chỉ được (a) thêm, (b) đổi trạng thái hợp lệ, hoặc (c) **xoá qua tombstone hợp lệ** (mục 10.3a). Item biến mất mà KHÔNG có tombstone tương ứng trong `transaction_log.md` của transaction này → `E-REVIEW-LOST`. Ngoài transaction không kiểm INV-11 (không có baseline).

Toàn vẹn nguồn & khẳng định:

- `INV-12` Mọi claim `status: confirmed` lớp B có anchor trỏ tới nguồn `status: confirmed`, và anchor đó tồn tại với `quote` không rỗng (schema mục 5.3). Claim `status: draft` được phép thiếu anchor nhưng phải có `draft_reason`.
- `INV-13` Không dùng nguồn `raw`/`rejected` làm anchor.
- `INV-14` Mọi claim `status: confirmed` lớp C có danh sách tiền đề, và mọi tiền đề phải là claim A/B `status: confirmed`; không tiền đề nào thuộc lớp D hoặc `status: draft`.
- `INV-15` Không claim nào trong mục `## Claims` thiếu `id/class/status/text` (transcript/hội thoại ngoài `## Claims` không bị ràng). Claim trong `## Claims` thiếu lớp → `E-CLAIM-UNCLASSED`; claim draft thiếu `draft_reason` → `E-CLAIM-DRAFTREASON`.

Toàn vẹn portability:

- `INV-16` Không file nào trong `learning_vault/` chứa đường dẫn tuyệt đối của máy.
- `INV-17` Không có repo/dependency/code cài đặt nằm trong `learning_vault/`.
- `INV-18` Không bài học/trạng thái cá nhân nào nằm trong `_system/`.
- `INV-19` `vault_state.schema_version` **tương thích** `_system/VERSION` theo quy tắc semver chốt cứng: **major PHẢI bằng nhau**; `vault.minor <= system.minor`. Nếu `vault.major < system.major` HOẶC `vault.minor < system.minor` → `E-SCHEMA-OUTDATED` (cần migration, mục 10.7). Nếu `vault.major > system.major` HOẶC `vault.minor > system.minor` → `E-SCHEMA-AHEAD` (vault mới hơn hệ thống; chặn để không ghi đè bằng luật cũ).
- `INV-20` `learning_vault/_scratch/` và các vùng `.tx/` (cả hai gốc) là vùng phi-thẩm-quyền: không file nguồn sự thật nào được tham chiếu tới file trong đó; xóa chúng phải không gây gãy tham chiếu; validator bỏ qua nội dung (chỉ quét đường dẫn tuyệt đối).

Toàn vẹn FSRS / năng lực / khẳng định:

- `INV-21` `mastery_state` của mỗi item khớp `derive_mastery(card, log)` (mục 6.2). Lệch → `E-STATE-DERIVED`.
- `INV-22` Mỗi trục `mastery` đạt ngưỡng cổng (mục 9.3) phải có ≥1 `evidence` tồn tại trong `lesson.md`, `axis` khớp, `quote` không rỗng. Thiếu → `E-ASSESS-NOEVIDENCE`.
- `INV-22b` (chống "bằng chứng ma") `evidence.quote` phải là **chuỗi con của transcript** block trả lời người học (`#### Bạn trả lời <qid>`) trong cùng `lesson.md`, **so khớp sau chuẩn hoá nhẹ** (mục 9.6). AI không được tự bịa câu trả lời hoàn hảo rồi nhét vào evidence. Không khớp → `E-ASSESS-FAKEQUOTE`. (Giới hạn cố hữu: việc này chỉ ép `quote ⊆ transcript đã ghi`, không thể chứng minh transcript khớp 100% điều con người gõ — đó là giới hạn của mọi hệ file-based; nhưng nó bịt được lỗ "quote không hề có trong transcript".)
- `INV-23` Claim chỉ nằm trong mục `## Claims` của `lesson_notes.md`/`topic.md`; claim ngoài vùng → `E-CLAIM-LOC`. Claim `status: confirmed` lớp B phải có `source_refs` confirmed; claim `status: confirmed` lớp C phải có `premise_refs` là claim A/B confirmed. Claim draft không được làm tiền đề confirmed và phải có `draft_reason`.
- `INV-24` `fsrs_config_version` của mọi item phải tồn tại trong `_system/fsrs_config.yaml`; version cũ thiếu → `E-SCHEMA-OUTDATED` (cần migration, mục 10.7).
- `INV-25` `topic_state.lessons` (index) phải khớp 1-1 với thư mục `lessons/` thực tế (nguồn gốc), và từng `lessons[].status` phải khớp `lesson_state.status`. Nếu `topic_id == vault_state.current_topic`, `topic_state.current_lesson` phải khớp `vault_state.current_lesson`; lệch index/cache → `E-INDEX-MISMATCH`.
- `INV-26` Claim `status: draft` KHÔNG được nằm trong section `## Knowledge Map` của `topic.md` (chỉ confirmed mới vào map); và `topic_state.has_draft_knowledge` là view sinh tự động, phải đúng với việc còn/không còn claim draft (mục 15.1). Sai → `E-DRAFT-IN-MAP` (FULL-regen phải tự sửa field này trước validate).

### 10.3. Quy Trình Ghi An Toàn (Write Transaction — Transaction-Safe)

Cơ chế cụ thể, không chỉ là ý niệm. **Đính chính v2.3:** `os.replace` chỉ atomic ở cấp **một file** trên cùng filesystem; không có primitive portable nào bảo đảm atomic tuyệt đối cho nhiều file/nhiều root. Vì vậy cam kết đúng là: *file-level atomic + manifest + recovery bắt buộc*, để không có partial commit âm thầm. Sau crash, hệ thống phải roll-forward/restore về trạng thái xác định trước khi cho ghi tiếp.

```text
0. RECOVER-FIRST: trước mọi transaction/validate, quét .tx/ có manifest state in {committing, interrupted}.
   Nếu có tx chưa kết thúc → chạy recovery trước; recovery không xong → chặn ghi mới với E-TX-PARTIAL.
0b. EXPECTED READ HASHES: mọi file mà AI dùng làm nền để sinh thay đổi phải có
   expected_read_hash = sha256(bytes file) tại thời điểm file được nạp vào context (T-read),
   truyền vào transaction. File mới thì expected_read_hash = null.
1. BEGIN: với mỗi gốc bị đụng, tạo vùng tx CÙNG GỐC ĐÓ:
   learning_vault/.tx/<tx_id>/ và/hoặc _system/.tx/<tx_id>/.
   Với mỗi file đích: tính current_hash. Nếu expected_read_hash != null và
   current_hash != expected_read_hash → ABORT với E-STALE-CONTEXT, KHÔNG stage.
   Ghi manifest.json gồm tx_id, root, level, file list, state="prepared".
   Với mỗi file đích: lưu backup, staged_path, expected_read_hash, before_hash=current_hash, backup_hash.
   Baseline backup này là nguồn so sánh cho INV-06 (state transition) và INV-11 (review item lost).
2. STAGE: ghi thay đổi ra staged files trong .tx/<tx_id>/staged/, KHÔNG đụng file thật.
   Sau khi stage xong, ghi staged_hash cho từng file vào manifest.
3. REGEN: (chỉ ở mức FULL) sinh lại view (review_schedule, assessment, has_draft_knowledge) + hash trên bản staged.
4. VALIDATE: chạy validate.py trên overlay staged ở đúng mức transaction (LIGHT/FULL, mục 10.8).
5. OCC RE-CHECK: trước commit, tính lại sha256 hiện tại của từng file đích, so với before_hash.
   Có file đổi → ABORT với E-CONCURRENT-EDIT, KHÔNG ghi đè.
6a. PASS + OCC OK → COMMIT:
   - set manifest state="committing" bằng atomic_write_manifest();
   - os.replace từng staged file vào file thật theo thứ tự deterministic, mỗi file có retry;
   - sau mỗi replace, cập nhật committed_files bằng atomic_write_manifest();
   - xong hết → state="committed" bằng atomic_write_manifest(), ghi transaction_log.md, rồi mới dọn .tx/<tx_id>/.
6b. FAIL trước state="committing" → ABORT: file thật chưa đụng; set state="aborted"; giữ .tx để truy vết.
6c. FAIL/crash trong state="committing" → KHÔNG được tự coi là rollback.
   Lần chạy sau RECOVER-FIRST dùng manifest để hoàn tất roll-forward hoặc chặn với E-TX-PARTIAL.
```

**OCC hai mốc — chống ghi đè khi người dùng sửa tay (TOCTOU).** Có hai cửa sổ rủi ro khác nhau và phải bịt cả hai:

- **T-read → BEGIN:** AI có thể đọc file, suy nghĩ/sinh nội dung 15–30 giây, trong lúc đó người dùng sửa tay. Nếu transaction chỉ chụp hash ở BEGIN, nó sẽ coi bản người dùng vừa sửa là baseline rồi ghi đè bằng nội dung AI sinh từ bản cũ. Vì vậy mọi ghi dựa trên file đã đọc phải truyền `expected_read_hash` từ thời điểm nạp context. BEGIN phải so `current_hash == expected_read_hash`; lệch → `E-STALE-CONTEXT`, yêu cầu AI đọc lại file và sinh lại thay đổi.
- **BEGIN → COMMIT:** FULL-validate mất ~1–2s; trong khoảng đó người dùng có thể sửa file thật rồi Ctrl+S. Vì vậy trước COMMIT vẫn phải so `current_hash == before_hash`; lệch → `E-CONCURRENT-EDIT`, abort.

Hash dùng **bytes thật của file** (`read_bytes()`), không hash text đã decode, để OCC độc lập với newline/encoding parser. `mtime` không đủ tin cậy vì có thể trùng độ phân giải hoặc bị cloud-sync chạm.

**Atomic write cho manifest.** Chính `manifest.json` cũng không được ghi đè trực tiếp bằng `json.dump(open(..., "w"))`: crash giữa chừng sẽ tạo JSON rách và làm recovery mất dấu. Mọi cập nhật manifest PHẢI dùng `atomic_write_manifest`: ghi JSON canonical ra `manifest.tmp` bằng UTF-8 → flush + `os.fsync(tmp_fd)` → `os.replace(tmp, manifest.json)` → fsync thư mục chứa nếu OS hỗ trợ. Nếu manifest chính hỏng nhưng còn `manifest.tmp` nguyên vẹn, RECOVER-FIRST được phép dùng bản tmp chỉ khi hash/tx_id khớp; nếu không khớp → `E-TX-PARTIAL`.

**Retry os.replace chống cloud-sync khóa file (Windows).** Vault thường nằm trong OneDrive/Google Drive/iCloud (ví dụ thực tế: `d:\OneDrive\...`). Cloud agent hay **lock file** để quét/upload đúng lúc rename → trên Windows `os.replace` ném `PermissionError` (WinError 32, "file in use"). Vì vậy COMMIT phải bọc rename trong **retry exponential-backoff**: thử lại khi gặp `PermissionError`/`OSError`, giãn `0.1s → 0.2s → 0.5s → 1s → 2s` (tối đa ~5 lần); hết lượt khi đang `committing` → set manifest `state="interrupted"`, báo `E-TX-PARTIAL`, giữ `.tx/` để recovery lần sau. (Khuyến nghị thêm: đặt `.tx/`, `_system/.cache/` vào danh sách cloud-sync bỏ qua nếu công cụ hỗ trợ, để giảm tranh chấp; nhưng retry là lớp phòng thủ bắt buộc, không phụ thuộc cấu hình người dùng.)

**Mọi lần ghi đều transaction-safe; chỉ MỨC validate là khác nhau.** Đây là chỗ hòa giải mục 11A ("mọi ghi qua transaction") với mục 10.8 ("trong phiên chỉ LIGHT"): *cơ chế ghi* (BEGIN→STAGE→VALIDATE→manifest→rename/recovery) áp cho **mọi** lần ghi — kể cả ghi nháp `lesson.md` trong phiên — nên không có partial commit âm thầm. Cái thay đổi theo ngữ cảnh là **bước 4 chạy LIGHT hay FULL**: ghi trong phiên → transaction-LIGHT (bỏ REGEN, không replay); `/done` và `/review` → transaction-FULL (có REGEN + replay + toàn bộ INV). "Đã commit ở mức LIGHT" KHÔNG đồng nghĩa "đã chốt đúng tuyệt đối"; chỉ transaction-FULL mới nâng dữ liệu lên trạng thái sự thật (mục 10.8).

**Recovery protocol (bắt buộc).** Nếu phát hiện manifest `state="committing"`/`"interrupted"`:

- Với mỗi file trong manifest: nếu target hash == `staged_hash` → file đó đã commit; nếu target hash == `before_hash`/`backup_hash` → file đó chưa commit; nếu target hash khác cả hai → người dùng/cloud đã sửa trong lúc tx dở, chặn với `E-TX-PARTIAL` để người đọc quyết định thủ công.
- Nếu mọi file chỉ ở hai trạng thái "đã commit" hoặc "chưa commit" và staged files còn nguyên → **roll-forward** các file chưa commit bằng `os.replace` + retry, rồi set `state="committed"`, ghi log. Roll-forward được chọn thay vì rollback vì transaction đã PASS validate và đã qua OCC trước khi vào `committing`.
- Nếu staged/backup/manifest thiếu hoặc hash không khớp → chặn ghi mới với `E-TX-PARTIAL`; không đoán, không tự sửa.

**Tránh lỗi cross-device:** vùng `.tx/` và staging phải nằm **cùng gốc (cùng filesystem)** với file đích — dữ liệu học stage trong `learning_vault/.tx/`, file `_system/` stage trong `_system/.tx/`. Không stage một nơi rồi rename xuyên gốc (sẽ dính `Errno 18 cross-device link`); `os.replace` chỉ atomic khi cùng filesystem. Cả `learning_vault/.tx/` và `_system/.tx/` là vùng transient, bị validator bỏ qua (như `_scratch/`, INV-20) và xóa sau commit.

**Phạm vi transaction:** một transaction backup + validate + commit **mọi file nó đụng tới, ở cả hai gốc**. Thường chỉ chạm `learning_vault/`, nhưng khi thao tác đụng `_system/` (ví dụ duyệt change request, ghi `repo_evaluations/`, đổi `fsrs_config.yaml`) thì các file `_system/` đó cũng nằm trong cùng `tx_id` (mỗi gốc có manifest/staging nội bộ gốc đó) và phải qua validate trước khi commit. Vì multi-root không thể atomic tuyệt đối, recovery phải xét đủ manifest của mọi root cùng `tx_id`; thiếu một root hoặc lệch hash → `E-TX-PARTIAL`, không ghi tiếp.

### 10.3a. Xoá Có Thẩm Quyền (Tombstone) — Lối Thoát Hợp Lệ Cho INV-11

INV-11 chặn review item `in_review/need_redo` "biến mất" để không mất dữ liệu ôn ngầm. Nhưng người học **có quyền** xoá hẳn một lesson/topic (học sai hướng, gộp bài, làm lại). Để việc đó không bị validator chặn oan, định nghĩa **lối xoá có thẩm quyền duy nhất**:

```text
DELETE op (chỉ khi người dùng xác nhận tường minh, ví dụ /forget <lesson_id|topic_id>):
1. Trong transaction-FULL: với mỗi review item bị xoá, ghi một TOMBSTONE vào
   _system/change_requests/changelog.md (hoặc transaction_log.md) gồm:
   {op: "delete", scope, lesson_id/topic_id, item_ids:[...], reason, at, confirmed_by_user: true}
2. Validator INV-11: item biến mất được THA nếu và chỉ nếu có tombstone khớp item_id
   trong transaction_log.md của ĐÚNG tx_id này; không có tombstone → E-REVIEW-LOST.
3. Xoá phải kéo theo dọn mọi tham chiếu tới đối tượng bị xoá (INV-03), nếu không → E-REF-BROKEN.
```

**Độ bền của tombstone (vá durability):** tombstone KHÔNG được là hậu tố best-effort ghi sau khi đã replace file. Nó PHẢI được ghi **durable vào manifest của transaction** (qua `atomic_write_manifest`, mục 10.3) **trước bước replace file**. `transaction_log.md`/`changelog.md` chỉ là **bản materialize dẫn xuất từ manifest**. Nếu crash sau khi replace file (deletion đã xảy ra) nhưng trước khi ghi log, RECOVER-FIRST phải **roll-forward materialize tombstone từ manifest**; nếu manifest không có tombstone tương ứng → `E-TX-PARTIAL` (không được để deletion mồ côi làm INV-11 báo `E-REVIEW-LOST` oan).

### 10.3b. Migration Cũng Là Transaction

Mọi script migration `vN_to_vN+1` (mục 10.7) phải chạy **bên trong một transaction-FULL**: BEGIN (backup toàn vault) → STAGE (áp biến đổi ra staging) → REGEN view → VALIDATE bằng schema của **version đích** → PASS thì COMMIT + tăng `vault_state.schema_version`, FAIL thì ABORT giữ nguyên vault cũ. Không migration nào được sửa file thật trực tiếp. Migration thất bại = vault không đổi, người dùng vẫn dùng được version cũ.

### 10.4. Bảng Mã Lỗi (trích)

| Mã | Ý nghĩa |
|----|---------|
| `E-SCHEMA-*` | Sai schema/field/kiểu |
| `E-SCHEMA-OUTDATED` | Version schema/config cũ, cần migration |
| `E-SCHEMA-AHEAD` | `vault.schema_version` mới hơn `_system/VERSION` (INV-19) — chặn ghi bằng luật cũ |
| `E-REF-BROKEN` | Tham chiếu trỏ tới thứ không tồn tại |
| `E-INDEX-MISMATCH` | `topic_state.lessons`/status/cache current_lesson không khớp nguồn sự thật |
| `E-DRAFT-IN-MAP` | Claim `status: draft` lọt vào knowledge map, hoặc cờ `has_draft_knowledge` sai |
| `E-STATE-ILLEGAL` | Chuyển trạng thái không hợp lệ |
| `E-STATE-DERIVED` | `mastery_state` không khớp `derive_mastery(card, log)` |
| `E-REVIEW-MISCALC` | Replay log không khớp `card` |
| `E-REVIEW-BADGRADE` | grade ngoài 0..3 |
| `E-REVIEW-DUP` | Trùng review item |
| `E-REVIEW-LOST` | Review item `in_review/need_redo` biến mất không có tombstone hợp lệ (INV-11, mục 10.3a) |
| `E-STALE-CONTEXT` | File đã đổi sau khi AI đọc vào context nhưng trước khi transaction BEGIN; phải đọc lại và sinh lại thay đổi |
| `E-CONCURRENT-EDIT` | File đích bị sửa tay trong lúc transaction chạy (OCC content-hash lệch, mục 10.3) |
| `E-IO-ENCODING` | File text trong vault/system không đọc được bằng UTF-8 rõ ràng |
| `E-VIEW-STALE` | View không khớp hash nguồn |
| `E-VIEW-MISMATCH` | Nội dung view không khớp object sinh lại dù hash có thể khớp |
| `E-ASSESS-NOEVIDENCE` | Trục mastery đạt ngưỡng nhưng thiếu evidence |
| `E-ASSESS-FAKEQUOTE` | `evidence.quote` không phải chuỗi con của block trả lời người học (INV-22b) |
| `E-GATE-FAIL` | Đặt `learned` khi chưa qua cổng |
| `E-CLAIM-UNCLASSED` / `E-CLAIM-NOSRC` / `E-CLAIM-WEAKBASE` / `E-CLAIM-LOC` / `E-CLAIM-DRAFTREASON` | Lỗi phân lớp/đặt sai chỗ/thiếu lý do draft của khẳng định |
| `E-SRC-RAWUSED` | Dùng nguồn thô làm kiến thức |
| `E-PORT-ABSPATH` | Đường dẫn tuyệt đối trong vault |
| `E-MIX-*` | Trộn lẫn `_system/` và `learning_vault/` |
| `E-TX-PARTIAL` | Có transaction dở/không recovery được; chặn ghi mới để tránh partial commit âm thầm |
| `W-IGNORED-CLOUD-CONFLICT` | Warning: bỏ qua file rác cloud-sync/conflict artifact theo ignore policy |

### 10.5. Cơ Chế Chạy Validator (Bắt Buộc)

Nếu không chạy validator thật, toàn bộ cam kết "đúng tuyệt đối ở tầng cấu trúc" sụp. Chốt cơ chế, **không phụ thuộc một IDE cụ thể**:

- **Bắt buộc (nền tảng độc lập):** bước VALIDATE trong transaction, lệnh `/validate` và `/done` đều là **lệnh shell** gọi `validate.py`; AI phải **dán report nguyên văn**. Đây là cơ chế tối thiểu chạy ở mọi môi trường (Kiro, VS Code, Codex, terminal).
- **Tăng cường (tùy IDE):** nếu IDE hỗ trợ hook (Kiro `postToolUse`/`fileEdited`), gắn thêm để tự chạy khi ghi vào `learning_vault/`. Đây là lớp tiện lợi, KHÔNG phải điều kiện tiên quyết.
- AI **bị cấm** tuyên bố PASS nếu chưa có output validator thật.

### 10.6. Kiểm Thử Chính Validator (Validate the Validator)

`_system/validator/tests/` chứa **golden fixtures**: vault hợp lệ (phải PASS) và vault hỏng có chủ đích, mỗi cái kèm `expected_error_code`. Một bug trong `validate.py` có thể báo PASS cho dữ liệu hỏng → bộ test này phải bắt được. Phải chạy đạt trước khi tin validator.

### 10.7. Migration Khi Đổi Version

`_system/migrations/` chứa script `vN_to_vN+1`. Khi gặp `schema_version`/`fsrs_config_version` cũ, validator báo `E-SCHEMA-OUTDATED` kèm migration cần chạy, thay vì lỗi chung. Giữ portability khi vault đi qua nhiều máy/nhiều phiên bản hệ thống.

### 10.8. Hai Mức Validation (Giảm Ma Sát Khi Học)

Validate đầy đủ sau từng câu trả lời sẽ làm việc học rất nặng. Nên tách hai mức, theo thời điểm:

| Mức | Khi nào chạy | Kiểm gì | Mục tiêu |
|---|---|---|---|
| **LIGHT** (nhẹ, cục bộ) | Trong phiên học, mỗi lần ghi tạm vào `lesson.md`/nháp | Chỉ schema + ngày + ref **của file vừa đụng**; KHÔNG replay FSRS, KHÔNG sinh lại view | Không chặn dòng chảy học |
| **FULL** (đầy đủ) | Tại `/done`; và tại `/review` cho item có **đổi FSRS** | Toàn bộ `INV-01..26` + replay FSRS + sinh lại view + transaction-safe manifest | Đảm bảo "đúng tuyệt đối" tại điểm đóng sổ |

Nguyên tắc giữ cam kết "đúng tuyệt đối":

- Trong phiên, dữ liệu được coi là **bản nháp đang soạn**, chưa phải sự thật đã chốt. LIGHT chỉ bắt lỗi cú pháp sớm.
- **Không gì được coi là "đã commit/đúng" cho tới khi đi qua một transaction FULL-validated** (mục 10.3). Vì vậy nới LIGHT trong phiên KHÔNG phá bảo đảm — nó chỉ hoãn việc kiểm nặng tới `/done`.
- `/review` là ngoại lệ: mỗi câu ôn đổi `card` FSRS thì chạy FULL cho riêng item đó ngay (replay + transaction nhỏ), vì đó là dữ liệu lâu dài.
- Quy tắc "không tự tuyên bố đã valid" (mục 10.1) áp cho mức FULL: AI chỉ được nói PASS khi đã chạy validator đầy đủ ở `/done` hoặc `/review`.

LIGHT kiểm chính xác những gì (theo loại file):

- `*_state.md` (có front-matter): chỉ kiểm front-matter của **file vừa đụng** — đúng schema, đúng kiểu/enum, ngày hợp lệ; KHÔNG kiểm tham chiếu chéo toàn vault, KHÔNG replay FSRS, KHÔNG sinh lại view.
- `lesson.md` (KHÔNG front-matter): kiểm cú pháp body bằng AST — có đủ heading bắt buộc (`## Mục tiêu`, `## Sessions`), heading `#### Question <qid>` có `qid` không trùng trong file, evidence block đúng cú pháp (heading `#### Evidence ev-*` + fenced ```yaml``` liền sau có đủ `axis`/`timestamp`/`quote`, mục 5.5), `evidence id` không trùng trong file, và không có đường dẫn tuyệt đối.
- `_scratch/`: chỉ quét đường dẫn tuyệt đối.

Mọi kiểm tra liên-file (ref, INV-08 replay, INV-09 hash view, INV-21..26) chỉ chạy ở FULL.

### 10.9. Hiệu Năng Validator (Cache Replay Phi-Thẩm-Quyền + Validate Vi Sai)

FULL-validate replay toàn bộ `log` của mọi item (INV-08). Với vault cá nhân (vài trăm thẻ) chi phí dưới giây; nhưng khi tích lũy hàng nghìn thẻ × hàng trăm lượt qua nhiều năm, `/done` có thể chậm thấy rõ. Hai cách tăng tốc — **bắt buộc giữ nguyên mô hình tin cậy** (không cái nào được nới lỏng INV-08):

**(a) Cache replay phi-thẩm-quyền.** Memoize kết quả replay ở vùng KHÔNG phải nguồn sự thật: `_system/.cache/` (validator bỏ qua như `.tx/`/`_scratch/`, INV-20).

```text
khóa cache = sha256( fsrs_config_version + canonical_json(log) )
giá trị     = card đã replay (state/step/stability/difficulty/due_at_utc/due_date/last_reviewed_at_utc)
- log không đổi → khóa trùng → dùng lại card, BỎ QUA replay.
- log đổi (thêm lượt) → khóa đổi → replay lại từ New, ghi cache mới.
```

> ⚠️ **KHÔNG** lưu snapshot/checkpoint trạng thái thẻ **bên trong `lesson_state.md`** rồi cho replay bắt đầu từ đó. `lesson_state.md` là nguồn sự thật AI ghi được; tin một snapshot trong đó = mở lại đúng lỗ hổng mà INV-08 bịt (AI ghi snapshot giả + cắt log → validator tin nhầm). Cache PHẢI nằm ngoài vault, **luôn tái dựng được từ `New`+log**, và validator KHÔNG BAO GIỜ coi cache là chân lý — chỉ là phím tắt bỏ qua tính lại khi log y nguyên. Mất/xoá cache không ảnh hưởng tính đúng, chỉ chậm lại.

**(b) Validate vi sai (incremental FULL).** Khi `/done` chỉ đụng một lesson, không cần replay cả vault:

```text
1. Dựng đồ thị phụ thuộc: lesson ↔ prerequisites ↔ topic_state (view) của topic chứa nó.
2. FULL chỉ chạy trên tập bị ảnh hưởng: lesson vừa đổi + các lesson phụ thuộc nó + topic_state cha
   (vì review_schedule/assessment của topic là view tổng hợp).
3. FULL TOÀN VAULT (quét tất cả) chạy ở các mốc lớn: lệnh `/validate` thủ công, trước khi
   commit/push vault qua Git, và khi đổi `_system/VERSION`/`fsrs_config_version` (ảnh hưởng diện rộng).
```

Vi sai chỉ **thu hẹp phạm vi** quét, không đổi tiêu chí đúng/sai; tập bị ảnh hưởng phải được tính đúng (thiếu một file phụ thuộc = phải mở rộng phạm vi, không được bỏ sót). Khi nghi ngờ → chạy FULL toàn vault.

---

## 11. Routing Ý Định (Có Móc Validation)

AI không mặc định mọi câu là lệnh thực thi. Trước tiên phân loại:

- `new_topic` — muốn học cái mới.
- `lesson` — đang học trong bài.
- `side_question` — hỏi phụ trong phạm vi bài.
- `review` — ôn tập.
- `source_ingestion` — nạp tài liệu.
- `system_change` — sửa luật/prompt/format/cấu trúc.
- `unclear` — chưa đủ rõ để xử lý an toàn → hỏi lại, không đoán.

Sau khi phân loại, chọn đúng nơi ghi:

- Dữ liệu học → `learning_vault/`.
- Luật/prompt/template/repo công cụ/change request → `_system/`.
- Mọi lần ghi đều đi qua Write Transaction (mục 10.3).

---

## 11A. Giao Diện Lệnh (Commands)

Lệnh là **routing tường minh**: người dùng gõ `/lệnh [tham số]` để chọn thẳng ý định thay vì để AI đoán. Nguyên tắc gốc: **lệnh không bao giờ vượt qua validator**. Mọi lệnh có ghi dữ liệu vẫn đi qua Write Transaction (mục 10.3) — *cơ chế ghi transaction-safe áp cho mọi lệnh*, chỉ **mức validate** khác nhau: lệnh/ghi trong phiên dùng transaction-LIGHT, `/done`+`/review`+`/forget` dùng transaction-FULL (mục 10.8). Lệnh chỉ là phím tắt cho người dùng, kỷ luật ghi giữ nguyên.

Lệnh lạ hoặc thiếu tham số → rơi về intent `unclear` → hỏi lại, không đoán.

### 11A.1. Hai lệnh chính

**`/learn <chủ đề>`** — intent `new_topic`.

```text
1. Hỏi calibrate TỐI ĐA 3 CÂU, từng câu một (không thẩm vấn dài):
   Q1. Mục tiêu cuối: học để làm được gì cụ thể?
   Q2. Trình độ hiện tại với chủ đề này (mới hoàn toàn / đã biết ít / đã làm qua)?
   Q3. Có tài liệu/nguồn muốn dùng không? (nếu không → học ở chế độ draft, mục 15.1)
   → Người học gõ "skip" bất cứ lúc nào → dùng mặc định, không hỏi thêm.
2. Tính cấu trúc topic + đề xuất danh sách lesson (3-7 lesson, sắp theo tiên quyết).
3. Áp ID policy: topic_id = slug ascii (map đ→d), unique; trùng thì hỏi rồi thêm hậu tố;
   đổi tiêu đề KHÔNG đổi id. lesson_id = <topic_id>/lesson-NNN.
4. Tạo folder theo schema: topic.md, topic_state.md, sources.md, lessons/lesson-001/.
5. Chưa có nguồn vẫn tạo khung + dạy ở chế độ DRAFT; đánh dấu phần "cần bổ sung nguồn".
6. Transaction + VALIDATE → PASS → vào thẳng lesson-001, hỏi câu nhỏ đầu tiên.
```

Ví dụ thật:

```text
Bạn: /learn Docker
AI:  (Q1) Bạn muốn học Docker để làm được gì cụ thể? (đóng gói app / chạy local / deploy?)
Bạn: Đóng gói app Node rồi chạy local.
AI:  (Q2) Bạn đã từng dùng Docker chưa, hay mới hoàn toàn?
Bạn: Mới hoàn toàn.
AI:  (Q3) Có tài liệu nào muốn dùng không? Không cũng được.
Bạn: Chưa có.
AI:  Đã tạo topic "docker" với 5 lesson: [1] Container là gì → [2] Image & Dockerfile →
     [3] Chạy container → [4] Volume & network → [5] Đóng gói app Node.
     Học ở chế độ DRAFT (chưa nguồn). Bắt đầu lesson-001. Câu hỏi nhỏ đầu tiên: ...
```

**`/review [topic|all]`** — intent `review`. File ôn là **tờ nháp phù du**, điểm số ghi NGƯỢC ngay vào `lesson_state.md` từng câu một, nên xóa tờ nháp không mất gì.

```text
1. Tính (deterministic) mọi review item tới hạn theo mục 8.5 (hoặc trong topic chỉ định;
   "all" gồm cả item chưa tới hạn), sắp theo khóa cố định (due_date asc, due_at_utc asc, lesson_id asc, item_id asc).
2. Sinh file nháp: learning_vault/_scratch/review-YYYY-MM-DD.md, liệt kê câu hỏi (từ prompt_ref),
   chừa chỗ trả lời.
3. Hỏi từng câu một. Bạn trả lời → AI chấm rubric → ánh xạ sang rating FSRS (1..4)
   → gọi fsrs.Scheduler cập nhật stability/difficulty/due_at_utc/due_date trong lesson_state.md (transaction + validate).
4. Câu không kịp làm: giữ nguyên state cũ, KHÔNG đánh done.
5. Hết phiên: file nháp có thể xóa tùy ý; lần sau /review cùng ngày thì ghi đè.
```

### 11A.2. Bảng lệnh đầy đủ

| Lệnh | Việc | Ghi vào đâu |
|------|------|-------------|
| `/learn <chủ đề>` | Tạo/tiếp tục học một topic | `learning_vault/topics/...` (transaction) |
| `/review [topic\|all]` | Ôn các câu tới hạn hôm nay | nháp `_scratch/` + ghi ngược `lesson_state.md` |
| `/resume` | Tiếp tục đúng chỗ dở (đọc `vault_state.current_lesson` + `next_action`) | chỉ đọc |
| `/status` | Bảng tổng quan: đang học gì, hôm nay due bao nhiêu, mastery topic | chỉ đọc (sinh từ state) |
| `/schedule [n]` | Xem lịch ôn n ngày tới | chỉ đọc |
| `/ask <câu hỏi>` | Hỏi phụ trong lesson hiện tại | `lesson.md ## Hỏi phụ` |
| `/source <link\|text>` | Nạp tài liệu | `sources.md` status=raw |
| `/collect <topic> <slug> <nội dung>` | (v2.7) Ghi lát cắt tài liệu tham chiếu | `topics/<topic>/reference/<slug>.md` (transaction-LIGHT) |
| `/curriculum <topic> <points-json>` | (v2.7) Dựng giáo trình (điểm học + `teachable`) | `topics/<topic>/curriculum.md` (transaction-FULL) |
| `/curriculum --check <topic>` | (v2.7) Kiểm giáo trình, báo cáo PASS/FAIL | chỉ đọc |
| `/next-lesson <topic>` | (v2.7) Sinh lesson kế cho `current_point` (nhảy bài) | `lessons/lesson-NNN` + `topic_state.lessons[]` + `curriculum.md` (transaction-FULL) |
| `/grade <topic> <submission> <file> <target> <verdict>` | (v2.7) Ghi bản ghi chấm bài thực hành (bài nộp ở `exam/` ngoài vault) | `topics/<topic>/exam_results.md` (transaction-LIGHT) |
| `/test [lesson]` | Chạy cổng "đã hiểu" (learned_gate) cho lesson | `lesson_state.md` (transaction) |
| `/gaps` | Liệt kê `open_gaps` của topic | chỉ đọc |
| `/skip` | Bỏ qua câu ôn đang hiện mà không chấm (giữ nguyên card, không ghi log) | không đổi state |
| `/again` `/hard` `/good` `/easy` | Phím tắt chấm rating FSRS 1..4 khi đang ôn | `lesson_state.md` (transaction) |
| `/done` | Kết phiên: cập nhật state/tóm tắt/lịch + sinh lại view + validate | transaction |
| `/system <đề xuất>` | Đề xuất sửa hệ thống — KHÔNG áp dụng ngay | `change_requests/pending/` |
| `/forget <lesson_id\|topic_id>` | Xoá có thẩm quyền một lesson/topic (cần xác nhận) — ghi tombstone | transaction-FULL (mục 10.3a) |
| `/fix [file]` | Auto-format cú pháp Markdown/YAML (căn khoảng trắng, sửa cấp heading, dọn fence) — CHỈ sửa hình thức | transaction-LIGHT |
| `/validate` | Chạy validator thủ công, dán report | chỉ đọc |

- `/system` cố tình không thực thi: chỉ tạo change request (mục 12), đúng luật bảo vệ hệ thống.
- `/fix` **chỉ được đụng hình thức** (khoảng trắng, cấp heading, đóng/mở fence, sắp khóa YAML), TUYỆT ĐỐI KHÔNG sinh hay điền nội dung ngữ nghĩa: không tự tạo evidence/quote, không tự điền `source_refs`/`premise_refs`, không tự đặt điểm rubric. **KHÔNG được reflow/đổi khoảng trắng bên trong giá trị string của fenced YAML** (đặc biệt `evidence.quote`) — vì `/fix` chạy LIGHT, không có INV-22b bắt lại nếu quote bị đổi. Field nội dung bị thiếu thì để validator báo lỗi, không "vá" cho qua. Sau `/fix` vẫn phải validate như mọi ghi khác.
- `/done` là chỗ "neo" Write Transaction để mỗi buổi học luôn kết thúc ở trạng thái đã validate.

### 11A.3. Command Registry

`_system/commands.md` định nghĩa từng lệnh: cú pháp, intent tương ứng, phạm vi ghi (chỉ đọc / vault / system), có cần xác nhận không. Thêm/sửa/xóa lệnh **phải qua change request** (mục 12), không sửa nóng. Đây là nguồn sự thật của tập lệnh.

### 11A.4. Vùng `_scratch/` (Phi-Thẩm-Quyền)

Để "xong xóa cũng được" mà không phá toàn vẹn:

- `learning_vault/_scratch/` **không phải nguồn sự thật**. Validator bỏ qua nội dung của nó, chỉ quét đường dẫn tuyệt đối (INV-16).
- **Không file nguồn sự thật nào được trỏ tới `_scratch/`** → xóa file nháp không bao giờ tạo `E-REF-BROKEN` (đảm bảo bởi INV-20).
- Mọi giá trị có giá trị lâu dài (rating, due mới) phải được ghi ngược vào `lesson_state.md` trong cùng phiên, không nằm lại ở nháp.

---

## 11B. Nhịp Dùng Hằng Ngày (Daily Workflow)

Mục tiêu: mở IDE lên là học được ngay, không phải nghĩ về cơ chế hệ thống. Một ngày học chuẩn chỉ gồm 3–4 lệnh.

```text
1. /status   → AI đọc vault_state + view, trả lời gọn: đang học topic/lesson nào,
               hôm nay có bao nhiêu câu tới hạn ôn, đề xuất nên làm gì trước.
2. /review   → nếu có câu tới hạn: ôn trước (ký ức nguội ôn trước khi học mới).
               Hỏi từng câu, chấm, cập nhật FSRS. Xong xóa nháp được.
3. /resume   → học tiếp lesson đang dở (đọc next_action), HOẶC /learn <mới> nếu muốn topic mới.
               Học bằng hỏi-đáp nhẹ, ghi nhẹ trong phiên (validation NHẸ, mục 10.8).
4. /done     → chốt phiên: cập nhật state/tóm tắt/đánh giá, sinh lại view,
               transaction + validation ĐẦY ĐỦ. Đây là điểm "đóng sổ" an toàn.
```

Nguyên tắc UX:

- Người học chỉ cần nhớ 4 lệnh: `/status`, `/review`, `/resume`, `/done` (cộng `/learn` khi mở chủ đề mới).
- Không bắt buộc làm đủ; bỏ `/review` cũng được — câu tới hạn vẫn giữ nguyên cho hôm sau.
- `/status` luôn là cửa vào; `/done` luôn là cửa ra. Quên `/done` thì phiên sau `/status` sẽ nhắc có thay đổi chưa đóng sổ.

Ví dụ một phiên 15 phút:

```text
/status → "Đang ở docker/lesson-002. Hôm nay 3 câu ôn tới hạn. Gợi ý: /review trước."
/review → ôn 3 câu (2 Good, 1 Again → câu đó dời lịch gần lại). Xong.
/resume → học tiếp lesson-002 'Image & Dockerfile', 1 câu hỏi nhỏ mỗi lượt.
/done   → "Đã lưu: lesson-002 in_progress, mastery explain=2, tạo 2 review item mới,
           lịch ôn cập nhật. validate.py: PASS."
```

### 11B.1. Trình tự nạp ngữ cảnh (Boot Sequence — chống tràn token)

`lesson.md` phình to sau nhiều buổi (toàn transcript). Nếu AI nạp cả file vào context → loãng ("lost in the middle") + tốn cost. Khi `/resume` hoặc `/status`, AI **chỉ được nạp**:

1. Các file `*_state.md` (vault_state, topic_state, lesson_state) — nguồn trạng thái.
2. `lesson_notes.md` — cốt lõi đã chắt.
3. **Chỉ section `## Sessions` của buổi GẦN NHẤT** trong `lesson.md`.

Các session cũ là **archive làm bằng chứng cho validator**, không nạp vào context trừ khi có lệnh tra cứu cụ thể (vd `/ask` về một điểm cũ). Điều này không ảnh hưởng tính đúng: validator vẫn đọc toàn bộ khi chạy FULL; chỉ riêng cửa sổ ngữ cảnh của AI được giữ gọn.

### 11B.2. Phát Hiện Phiên Chưa Đóng Sổ (Open-Session Recovery)

Vì ghi trong phiên chỉ ở mức LIGHT (mục 10.8), một phiên có thể bị bỏ dở (đóng IDE, hết phiên AI) **sau khi đã ghi nháp nhưng trước `/done` FULL**. Lúc đó file thật vẫn nhất quán cú pháp (LIGHT đã PASS) nhưng **chưa qua FULL** — chưa được coi là sự thật đã chốt. Cơ chế phát hiện dựa trên cờ `vault_state.open_session` (mục 5.4):

```text
- Mở phiên (/learn, /resume): transaction nhỏ set open_session.lesson_id + started_at.
- Mỗi ghi LIGHT trong phiên: KHÔNG đụng open_session (đã set sẵn).
- /done: sau khi FULL-validate PASS, CÙNG transaction set open_session.lesson_id = null
         và cập nhật last_full_validate = now.
- /status (cửa vào): đọc open_session.
    * lesson_id == null  → "sạch", chào bình thường.
    * lesson_id != null  → CẢNH BÁO: "Phiên <lesson_id> mở từ <started_at> chưa /done.
      Chạy /done để FULL-validate & đóng sổ, hoặc /validate để xem trạng thái hiện tại."
```

Cờ này KHÔNG phải bất biến (validator không báo lỗi khi `open_session != null`, vì phiên dở là hợp lệ tạm thời). Nó là tín hiệu UX để không ai vô tình bỏ dữ liệu ở trạng thái nửa-chốt. Bất biến thật vẫn là: chỉ transaction-FULL mới nâng dữ liệu lên "đã chốt".

---

## 12. Change Request + Kiểm Tra Xung Đột Luật

Yêu cầu sửa hệ thống **không bao giờ áp dụng ngay**. Quy trình:

```text
1. Ghi yêu cầu vào _system/change_requests/pending/<id>.md
2. Phân tích: yêu cầu này giải quyết vấn đề gì.
3. CONFLICT CHECK: đối chiếu với mọi luật hiện có trong _system/rules/.
   - Nếu mâu thuẫn luật cũ → liệt kê cặp mâu thuẫn cụ thể (luật nào, dòng nào).
   - Nếu trùng lặp → chỉ ra.
   - Nếu phá vỡ một bất biến (mục 10.2) → chặn, nêu rõ bất biến nào.
4. Đánh giá rủi ro: drift, làm AI khó tiếp tục, giảm portability.
5. Viết lại thành đề xuất rõ ràng hơn câu thô ban đầu.
6. Trình tôi xác nhận.
7. Sau xác nhận: move sang approved/, áp dụng, ghi changelog.md (ngày, lý do, file đụng tới),
   tăng _system/VERSION nếu đổi schema.
```

Bước 3 (conflict check) là phần v1 thiếu. Nó đảm bảo `_system/rules/` không tích lũy mâu thuẫn ngầm theo thời gian.

---

## 13. Triết Lý Dạy & Bốn Phương Pháp

AI dạy để hiểu cách suy nghĩ, không đưa đáp án. Học như xây nhà:

1. **First Principles — đào móng:** tìm bản chất, phân rã tới phần không thể đơn giản hơn.
2. **Feynman + Analogy — dựng khung, sơn nhà:** giải thích bằng lời bình dân, ẩn dụ quen thuộc.
3. **Socrates — thanh tra logic:** hỏi ngược để lộ lỗ hổng, mâu thuẫn, điểm mù.
4. **Reverse role-play — dạy lại:** người học giải thích lại, AI đóng vai người học/phản biện.

Tôn trọng người học trưởng thành: đã có niềm tin/kinh nghiệm sẵn; học là **tái cấu trúc cách nghĩ**, không chỉ nạp thêm.

---

## 14. Quy Trình Buổi Học (Có Cổng Validation)

### Trước khi dạy

1. Đọc `vault_state.md` → biết topic/lesson hiện tại.
2. Đọc `topic_state.md` + `lesson_state.md`.
3. Xác định mục tiêu buổi, kiến thức nền cần kiểm, điểm khó dự kiến.
4. Thiếu dữ liệu quan trọng → hỏi, không đoán.
5. Chỉ giảng sau khi mục tiêu rõ.

### Trong khi dạy (vòng lặp)

First Principles → Feynman/Analogy → Socrates → ví dụ & phản ví dụ → người học giải thích lại → AI bắt lỗi tư duy → sửa mô hình hiểu.

Quy tắc tương tác trong `lesson.md`:

- Chỉ hỏi **một câu nhỏ nhất** mỗi lượt, chờ trả lời xong mới sang câu kế.
- Trả lời chưa rõ → đào sâu đúng điểm đó, không đổi chủ đề.
- Câu hỏi phát sinh → ghi vào section `## Hỏi phụ`, không làm rác bài giảng.
- Ghi nhẹ trong phiên: mỗi lần cập nhật `lesson.md` chỉ chạy validation **LIGHT** (mục 10.8), không validate nặng sau từng câu.

### Sau buổi học (qua Write Transaction)

1. Chấm rubric 5 trục, **kèm trích nguyên văn** câu trả lời làm bằng chứng.
2. Cập nhật `mastery`, `open_gaps`, `sections_done/pending`.
3. Với mỗi điểm cần nhớ: gọi `review()` hoặc tạo review item mới (không trùng).
4. Nếu `learned_gate` đúng → chuyển `status=learned`; nếu không, giữ `in_progress` và ghi `next_action`.
4b. **(v2.7) Auto-advance giáo trình:** nếu topic có `curriculum.md` VÀ lesson vừa đạt `learned_gate` map một `Curriculum_Point` chưa `done` → trong CÙNG transaction: đặt `point.status=done`, dời `current_point` sang điểm chưa-done đầu tiên theo `order` (hết điểm → giữ nguyên con trỏ, hoàn tất ngầm). Chưa qua gate / không map / không có giáo trình → KHÔNG đụng con trỏ (tương thích ngược tuyệt đối). Validator FULL kiểm `E-CURR-*` trước commit; sai → rollback cả `/done`.
5. Sinh lại view topic (review_schedule, assessment, has_draft_knowledge) + hash.
6. Cập nhật `lesson_notes.md` (tóm tắt ngắn/sâu/thẻ ôn).
7. Chạy `validate.py` ở mức FULL trong transaction-safe manifest (mục 10.3). PASS → commit + dán report. FAIL → abort (chưa đụng file thật) + báo lỗi; nếu crash giữa commit → RECOVER-FIRST lần sau.

Mục tiêu: phiên AI sau đọc vào tiếp tục được ngay, không hỏi lại từ đầu.

---

## 14A. Mẫu `lesson.md` Thực Tế

Đây là khung body của `lesson.md` (file học chính, không có front-matter; trạng thái máy-kiểm nằm ở `lesson_state.md`). Mỗi buổi là một session block để file không thành mớ hỗn độn.

````markdown
# Lesson 001 — Container là gì

## Mục tiêu
Hiểu container giải quyết vấn đề gì và khác máy ảo ra sao.

## Vì sao khó
Dễ nhầm container với máy ảo; khái niệm "chia sẻ kernel" trừu tượng.

## First Principles
- Vấn đề gốc: "chạy được trên máy tôi" nhưng máy khác thì hỏng.
- Phần không thể đơn giản hơn: cô lập tiến trình + đóng gói phụ thuộc.

## Ví dụ đời thường
Container như hộp cơm mang đi: đồ ăn + dụng cụ gói sẵn, mở ra đâu cũng dùng được,
nhưng vẫn nấu chung một bếp (kernel) thay vì mỗi người một căn bếp riêng (máy ảo).

---

## Sessions

### Session 2026-06-30
#### Question q1
"Theo bạn, vì sao 'chạy được trên máy tôi' lại là vấn đề?"

#### Bạn trả lời q1
> (người học gõ câu trả lời ở đây — đây là transcript verbatim mà INV-22b đối chiếu)

#### AI phản hồi
- Đúng ý: ...
- Còn thiếu/để đào sâu: ...

#### Evidence ev-20260630-001

```yaml
axis: explain
timestamp: 2026-06-30
quote: "<trích nguyên văn câu trả lời của người học — phải là chuỗi con của block 'Bạn trả lời q1'>"
ai_assessment: "Diễn đạt đúng ý cô lập phụ thuộc → explain=2"
```

#### Chốt buổi
Hôm nay hiểu: container = cô lập + đóng gói. Lần sau: phân biệt image vs container.
(Tóm tắt đầy đủ ngắn/sâu được ghi ở `lesson_notes.md`.)

## Hỏi phụ
- (các câu hỏi phát sinh ngoài luồng chính)
````

Lưu ý nhất quán: evidence block ở đây là nơi `lesson_state.mastery.<trục>.evidence` trỏ tới (mục 5.5). Cấu trúc cố định: **heading cấp 4 `#### Evidence ev-*` + một fenced ```yaml``` liền sau**; validator parse bằng AST (heading-token + fence-yaml), không regex (mục 5.5, 19). **Claim chính thức** thì ghi ở `lesson_notes.md`/`topic.md` mục `## Claims` (cũng dạng heading + fenced yaml), không ghi trong `lesson.md`.

**Chuẩn anchor `prompt_ref`:** mỗi câu hỏi có thể thành review item phải có heading `#### Question <qid>` với `qid` dạng `q1`, `q2`... duy nhất trong file. `review_item.prompt_ref = "lesson.md#<qid>"` (vd `lesson.md#q1`) trỏ tới đúng heading đó. Validator: anchor không tồn tại → `E-REF-BROKEN`; trùng `qid` trong một file → lỗi (LIGHT bắt được, mục 10.8).

---

## 15. Nguồn Học (Quy Trình Có Status)

Tôi có thể đưa: mong muốn học, mục tiêu, tài liệu, link, repo, sách, ghi chú, câu hỏi thực tế.

Quy trình xử lý trong `sources.md`:

```text
1. Nhận nguồn → tạo khối source mới, status: raw.
2. Phân loại kind, đánh giá trust, ghi scope.
3. Trích các ý dùng được; nếu đủ rõ → status: confirmed, tạo anchors.
4. Nếu mơ hồ → status: processing hoặc hỏi lại; KHÔNG dùng làm kiến thức (INV-13).
5. Chỉ sau confirmed mới cập nhật bản đồ kiến thức / lesson.
```

Repo phân biệt:

- Repo là **tài liệu học** của topic → khối source trong `sources.md` (chỉ ghi link/mô tả/commit/scope; không clone vào vault trừ khi tôi xác nhận).
- Repo là **công cụ/chuẩn hệ thống** → `_system/repo_lab/`.

### 15.1. Draft Knowledge vs Confirmed Knowledge

Nguyên tắc "chỉ dùng nguồn confirmed" (INV-13) là để chống bịa, nhưng nếu áp cứng thì **bài nào cũng kẹt vì phải có nguồn trước**. Giải bằng hai cấp độ kiến thức:

- **Draft knowledge** — AI dạy từ kiến thức nền của mô hình khi CHƯA có nguồn. Được phép dạy, được ghi vào `lesson.md`/`lesson_notes.md`, nhưng nếu ghi thành claim trong `## Claims` thì phải có **`status: draft` + `draft_reason`** và hiển thị cho người học là "chưa kiểm nguồn".
- **Confirmed knowledge** — claim có anchor tới nguồn `status: confirmed` (claim lớp B). Đây mới là kiến thức chính thức được đưa vào section `## Knowledge Map` của `topic.md`.

Quy tắc cứng:

```text
- Lesson VẪN học được khi chưa có nguồn → dạy ở chế độ draft.
- Claim `status: draft`: cho phép trong `lesson_notes.md`/`topic.md ## Claims`, nhưng KHÔNG được đưa vào `## Knowledge Map` và KHÔNG được làm tiền đề cho claim confirmed.
- Muốn nâng draft → confirmed: phải thêm nguồn confirmed + anchor (thường chuyển thành claim lớp B), hoặc viết lại thành claim C nếu có đủ tiền đề A/B confirmed.
- learned_gate (mục 9.3) VẪN chạy được trên draft (đánh giá năng lực không phụ thuộc nguồn),
  nhưng `topic_state.has_draft_knowledge` là view tự sinh để biết topic chưa được nguồn-hoá.
- Khi người học /source và nguồn được confirmed, AI rà lại các draft claim liên quan,
  nâng cấp hoặc sửa nếu nguồn mâu thuẫn.
```

Hệ quả: học trơn tru ngay cả khi tay không, nhưng hệ thống luôn phân biệt rõ "điều AI nói từ trí nhớ mô hình" với "điều đã có nguồn", đúng tinh thần phân lớp khẳng định (mục 0.1).

---

## 16. Repo Lab (Bảng Quyết Định Tải/Cài)

Mục tiêu của Repo Lab là trả lời rõ: **việc gì cần repo nào, tải/cài hay chỉ đọc tham khảo, đặt ở đâu, và vì sao**.

Quy tắc cứng:

- Không tải repo chỉ vì nổi tiếng.
- Không clone/cài bất kỳ repo nào vào `learning_vault/`.
- Repo/package dùng để chạy hệ thống nằm trong `_system/.venv` hoặc `_system/repo_lab/installed_repos/`.
- Repo chỉ để học thiết kế nằm trong `_system/repo_lab/reference_repos/` hoặc chỉ ghi link trong `_system/repo_lab/repo_evaluations/`.
- Trước khi cài thật, phải tạo file `_system/repo_lab/repo_evaluations/<repo_id>.md` ghi: version/commit, license, lý do dùng, rủi ro, cách rollback.

### 16.0. Tóm Tắt Nhanh — Chốt Cài Gì (tra trong một liếc)

| Package / Repo | Quyết định | Mục đích | Đặt ở đâu | Lưu ý khi cài |
|---|---|---|---|---|
| `fsrs` (py-fsrs) | ✅ **CÀI** | Engine lịch ôn (mục 8) | `_system/.venv` | Pin version + `enable_fuzzing=false` + golden fixture |
| `pydantic` v2 | ✅ **CÀI** | Validate schema/INV (mục 10) | `_system/.venv` | Range chỉ ở `pyproject.toml`; runtime cài exact từ lock |
| `PyYAML` | ✅ **CÀI** | Front-matter: tách `---` rồi `yaml.safe_load`; ghi YAML cho view | `_system/.venv` | `safe_load` xong phải normalize canonical trước schema/hash/compare |
| `markdown-it-py` | ✅ **CÀI** | Parse body `lesson.md` thành AST (heading/fence) cho INV-22/23 | `_system/.venv` | Thay regex (vá lỗ hổng #2); chính xác bằng AST |
| `pytest` | ✅ **CÀI (dev)** | Test chính validator (mục 10.6) | `_system/.venv` | Chạy offline |
| `hashlib` + `json` | ✅ **DÙNG** (stdlib, sẵn có) | Hash view (mục 4) | Python stdlib | `sort_keys=True`, separator cố định |
| `uv` (+ `requirements.txt` pin/hash) | 🔒 **LOCK TOOL** | Pin dependency để tái lập giữa máy | `_system/` (uv.lock + requirements.txt) | Pin cả version của `uv`; production chỉ `uv sync --frozen` |
| ADK / agents-cli / cookbooks / evals (mục 16.2) | 📖 **KHÔNG cài, chỉ đọc** | Học thiết kế agent/routing/eval/prompt | `_system/repo_lab/reference_repos/` nếu clone | Pin commit snapshot; refresh thủ công qua change request |
| `fsrs-optimizer`, LangChain/LlamaIndex, Letta/MemGPT | ❌ **LOẠI** | — | — | Phá tái lập / portability (mục 16.3) |

Quy tắc một câu: **4 package runtime được cài** (`fsrs`, `pydantic`, `PyYAML`, `markdown-it-py`) + **1 dev/test package** (`pytest`) + stdlib (gồm `datetime` cho timezone offset, `hashlib`/`json` cho hash), **cài runtime từ lock exact bằng `uv sync --frozen`** (kèm `requirements.txt` hash fallback); mọi repo khác chỉ để đọc tham khảo.

**Version đã xác minh (2026-06, khai báo tương thích trong `pyproject.toml`):** `fsrs==6.3.1` (MIT, 21 weights FSRS-6, runtime chỉ `typing-extensions`) · `pydantic>=2.13,<3` · `markdown-it-py>=4,<5` · `PyYAML>=6,<7` · `pytest` (dev). **Nguồn cài thật không phải range này**, mà là `uv.lock` exact + hash; fallback là `requirements.txt` exact + hash. **Python tối thiểu `>=3.10`** (ràng buộc của `fsrs`).

### 16.0A. Dependency Policy — Lock Exact, Không Cài Theo "Latest"

Đây là luật tái lập môi trường, không phải khuyến nghị:

- `pyproject.toml` được phép dùng version range tương thích cho package có API ổn định (`pydantic>=2.13,<3`, `markdown-it-py>=4,<5`, `PyYAML>=6,<7`). Range chỉ nói "hệ thống được thiết kế để tương thích", KHÔNG phải nguồn cài runtime.
- Môi trường chạy validator bình thường chỉ được dựng từ `uv.lock` bằng:
  ```text
  uv sync --frozen
  ```
  `--frozen` là bắt buộc: nếu lock thiếu/cũ, lệnh phải fail thay vì tự resolve lại dependency.
- Không dùng `uv sync` không `--frozen`, `uv lock`, hoặc `uv add` trong môi trường production/validate bình thường. Các lệnh đó chỉ được dùng khi đang thực hiện change request cập nhật dependency, sau đó phải chạy test/golden fixtures và commit lock mới.
- `requirements.txt` fallback phải được generate kèm hash cho toàn bộ direct + transitive dependency; máy không dùng `uv` phải cài bằng:
  ```text
  pip install --require-hashes -r requirements.txt
  ```
- Phiên bản của chính `uv` phải được ghi trong `_system/repo_lab/repo_evaluations/uv.md` (`uv_version`, nguồn cài, verified_at, rollback). Không tự nâng `uv` nếu chưa qua change request, vì lock/resolution behavior của tool cũng là một phần môi trường tin cậy.
- Runtime report của validator nên in `python_version`, `uv_version` (nếu dùng uv), và exact version của `fsrs/pydantic/PyYAML/markdown-it-py`; report này giúp audit lỗi "PASS trên máy A, FAIL trên máy B".

### 16.1. Bảng Repo CÀI-DÙNG Cho Hệ Thống

Đây là các dependency trực tiếp của validator hoặc test runner. Các package này được cài vào môi trường của `_system/`, không vào vault.

| Việc cần làm | Tải/cài repo/package nào | Hành động | Đặt ở đâu | Lý do chọn | Điều kiện bắt buộc |
|---|---|---|---|---|---|
| Engine lịch ôn FSRS, cập nhật `card.due_at_utc`/`card.due_date`, `stability`, `difficulty` | `open-spaced-repetition/py-fsrs` / package `fsrs` | CÀI package; clone repo chỉ để audit khi cần | Package trong `_system/.venv`; nếu clone: `_system/repo_lab/installed_repos/py-fsrs/` | FSRS là scheduler hiện đại, có Python package, phù hợp mục 8 hơn tự viết Leitner/SM-2 | Pin exact `fsrs==6.3.1`; ghi full `fsrs_config.yaml` (21 weights); `enable_fuzzing=false`; **input UTC-only** (convert trước khi gọi, mục 8.5); có golden fixture replay; KHÔNG cài extra `[optimizer]`. Có thể dùng `Card.to_json/from_json` cho cache (mục 10.9a) |
| Kiểm schema/invariant cho `validate.py` | `pydantic/pydantic` / package `pydantic` v2 | CÀI package | `_system/.venv` | Mạnh cho schema typed, custom validator, error rõ, hợp với INV-01..26 | Range trong `pyproject.toml` (`>=2.13,<3`), nhưng runtime cài exact từ `uv.lock`; mọi model schema phải nằm trong `_system/validator/`; **`model_config = ConfigDict(strict=True)`** để chặn ép kiểu ngầm (không tự biến `"1.0"`→`1.0`, `"2"`→`2`) — validator phải *bắt lỗi* dữ liệu sai kiểu, không *âm thầm sửa* (tránh lệch hash + che lỗi `E-SCHEMA-*`) |
| Đọc front-matter YAML trong Markdown | `PyYAML` (`yaml.safe_load`) | CÀI package | `_system/.venv` | Tách `---` ở đầu file rồi parse; bỏ `python-frontmatter` cho gọn dep | File state phải bắt đầu bằng `---`; split tối đa 2 lần để body giữ nguyên dấu `---`. Sau `safe_load`, bắt buộc chạy `normalize_frontmatter()` để chuyển mọi `date/datetime/bool/int/float` do YAML implicit typing tạo ra về canonical object/string theo schema trước khi pydantic validate, hash, hoặc deep-compare. **Quy ước:** `*_state.md` là file MÁY QUẢN — người dùng KHÔNG ghi comment/sắp xếp tay vào front-matter. **Tùy chọn:** nếu sau này muốn cho phép sửa tay front-matter, đổi sang `ruamel.yaml` — đánh đổi: nặng/chậm hơn PyYAML, thêm 1 dep |
| Parse body `lesson.md` (heading/claims/evidence/question) | `markdown-it-py` | CÀI package | `_system/.venv` | AST chuẩn, bỏ qua fenced code block chính xác — thay regex hên xui (vá lỗ hổng #2) | Duyệt node `heading`/`fence`; không quét bằng regex dòng |
| Tính ngày theo offset (`+07:00`) | stdlib `datetime` (`timezone`/`timedelta`) | KHÔNG tải repo | Python stdlib | Offset cố định đủ cho "hôm nay"/due; tránh phụ thuộc tzdata/zoneinfo trên Windows | Lưu `vault_state.utc_offset`; không xử lý DST (chấp nhận) |
| Test validator bằng golden fixtures | `pytest-dev/pytest` / package `pytest` | CÀI dev dependency | `_system/.venv` | Cần test chính validator trước khi tin validator; dễ viết fixture PASS/FAIL | Test phải chạy offline; fixture hỏng phải ra đúng `expected_error_code` |
| Hash view và canonical JSON | Python stdlib `hashlib` + `json` | KHÔNG tải repo | Python stdlib | Đủ cho `generated_from_hash`, giảm dependency | Chỉ hash object đã normalize canonical; dùng `sort_keys=True`, separator cố định, `ensure_ascii=False`, encode UTF-8 |
| Khóa phiên bản để tái lập giữa máy | `uv` (chính) + `requirements.txt` pin/hash (fallback) | CÀI `uv`; xuất lock | `_system/uv.lock` + `_system/requirements.txt` | `uv` cho lockfile có hash, nhanh; `requirements.txt` để máy chỉ có `pip` vẫn tái lập | Pin cứng `fsrs` khớp `fsrs_config.yaml`; pin cả `uv_version` trong repo evaluation; production chỉ `uv sync --frozen`; fallback chỉ `pip install --require-hashes -r requirements.txt`; không cài "latest" |

### 16.2. Bảng Repo THAM-KHẢO Thiết Kế

Các repo này **không cài làm dependency**. Chỉ dùng để học cách các hệ thống lớn viết agent, routing, eval, prompt, observability, workflow. Nếu cần đọc offline thì clone vào `_system/repo_lab/reference_repos/`, không bao giờ vào `learning_vault/`.

Quy tắc pin cho reference repo:

- Không đọc/áp dụng `main`/`master` mới nhất như nguồn sự thật sống. Mỗi repo tham khảo nếu clone phải có `reference_commit: "<full_commit_sha>"`, `verified_at`, và `refresh_policy: "manual only via change request"` trong file repo evaluation.
- Refresh reference repo là **system_change**: phải nêu lý do, diff/rủi ro pattern mới, và không được âm thầm đổi luật/prompt vì repo upstream thay đổi.
- Repo trong `_system/repo_lab/reference_repos/` chỉ là **source tham khảo thiết kế hệ thống**, KHÔNG tự động là nguồn học confirmed cho lesson. Muốn dùng nội dung của repo làm kiến thức bài học thì vẫn phải đưa repo/link/commit vào `learning_vault/topics/<topic>/sources.md`, tạo anchor, và chuyển `status: confirmed` theo mục 15.
- Nếu muốn eval rubric, ưu tiên tự viết `pytest` fixtures + JSON `expected_error_code`/expected score trước. `openai/evals` chỉ là cảm hứng về cấu trúc registry/eval; không kéo vào runtime mặc định.

| Việc cần học/thiết kế | Repo tham khảo | Tải về không? | Đặt ở đâu nếu tải | Vì sao dùng | Không dùng để làm gì |
|---|---|---|---|---|---|
| Agent architecture, routing, evaluator, tool orchestration | `google/adk-python` | Có thể clone để đọc, KHÔNG cài dependency mặc định | `_system/repo_lab/reference_repos/google-adk-python/` | Google ADK là toolkit agent code-first, có pattern cho agent/eval/deploy; hữu ích để học cách tách agent, tool, runner | Không biến hệ thống học thành app ADK; không phụ thuộc Google Cloud |
| Coding-agent skills, eval workflow, agent lifecycle, observability | `google/agents-cli` | Có thể clone để đọc skills/docs, KHÔNG cài runtime | `_system/repo_lab/reference_repos/google-agents-cli/` | Học cách Google tổ chức skills cho coding agents, eval, workflow, deploy/observe lifecycle | Không biến hệ thống học thành Google Cloud agent project |
| Legacy production agent template, CI/CD, eval, observability | `GoogleCloudPlatform/agent-starter-pack` | Chỉ đọc như legacy reference; KHÔNG cài | `_system/repo_lab/reference_repos/google-agent-starter-pack/` | Repo này có nhiều template/CI/eval/observability đáng học, nhưng hiện nên xem như nguồn tham khảo cũ | Không dùng làm lựa chọn mới nếu `agents-cli` thay thế tốt hơn |
| Claude agent/cookbook patterns, tool use, evaluator workflow | `anthropics/claude-cookbooks` | Có thể clone để đọc, KHÔNG cài | `_system/repo_lab/reference_repos/anthropic-claude-cookbooks/` | Học pattern routing/orchestrator/evaluator và cách viết ví dụ thực dụng | Không khóa hệ thống vào Claude API |
| Prompt engineering, failure modes, prompt structure | `anthropics/prompt-eng-interactive-tutorial` hoặc `anthropics/courses` | Có thể clone để đọc, KHÔNG cài | `_system/repo_lab/reference_repos/anthropic-prompt-tutorial/` | Học cách viết prompt rõ, tách instruction/data, tránh hallucination, thiết kế bài tập prompt | Không biến thành nội dung học chính nếu chưa đưa vào `sources.md` |
| Eval registry, cách tổ chức bộ đánh giá | `openai/evals` | Chỉ clone nếu thật sự cần học cấu trúc; KHÔNG cài mặc định | `_system/repo_lab/reference_repos/openai-evals/` | Học cấu trúc registry/eval để biến rubric và validator test thành thứ có thể chạy lặp lại | Không chạy eval tốn API/cost trong luồng mặc định |
| Cookbook, agent improvement loop, traces/evals, Codex workflow | `openai/openai-cookbook` | Có thể clone để đọc, KHÔNG cài | `_system/repo_lab/reference_repos/openai-cookbook/` | Học cách viết cookbook, workflow, eval loop, tài liệu kỹ thuật dễ dùng | Không đưa ví dụ API vào vault nếu không liên quan topic học |

### 16.3. Bảng Chủ Động KHÔNG Dùng

| Repo/framework | Quyết định | Lý do |
|---|---|---|
| `fsrs-optimizer` (nay là extra `fsrs[optimizer]`) | Không cài/không dùng extra optimizer | Extra `[optimizer]` kéo `torch`/`numpy`/`pandas` (xác nhận từ metadata `fsrs` 6.x) → phá tái lập + nặng. Chỉ cài base `fsrs` (runtime chỉ cần `typing-extensions`). Lưu ý: optimizer giờ nằm trong package `fsrs` dưới dạng extra, KHÔNG còn là package rời |
| LangChain/LlamaIndex | Không dùng làm lõi memory | Quá nặng so với mục tiêu Markdown portable; dễ kéo hệ sinh thái và abstraction không cần thiết |
| Letta/MemGPT | Không dùng làm memory chính | Trái nguyên tắc `learning_vault/` là nguồn sự thật Markdown có thể mang đi |
| Google ADK / Agent Starter Pack | Không cài làm runtime | Chỉ tham khảo thiết kế; cài runtime sẽ làm hệ thống học phụ thuộc framework/cloud không cần thiết |
| `GoogleCloudPlatform/agent-starter-pack` cho dự án mới | Không chọn làm tham khảo chính | Repo đã chuyển hướng sang `google/agents-cli`; chỉ dùng để đọc template cũ khi cần |
| OpenAI Evals | Không cài mặc định | Học cấu trúc registry/eval là đủ; eval mặc định của hệ thống là `pytest` fixtures + JSON expected, chạy offline, không API/cost |

### 16.4. Template Đánh Giá Mỗi Repo

Mỗi repo được cài hoặc clone để tham khảo phải có file đánh giá:

```yaml
repo_id: "py-fsrs"
repo_url: "https://github.com/open-spaced-repetition/py-fsrs"
role: "install_dependency"   # install_dependency|reference_only|rejected
used_for: ["review_engine"]
install_location: "_system/.venv"
source_location: "_system/repo_lab/installed_repos/py-fsrs"
license: "MIT"
version_or_commit: "<exact package version hoặc full commit SHA>"
lock_source: "uv.lock"        # uv.lock|requirements.txt|reference_commit|none
uv_version: null              # bắt buộc với repo_id="uv"; null với package/repo khác
reference_commit: null        # bắt buộc nếu role=reference_only và repo được clone
refresh_policy: "manual only via change request"
why: "..."
risks: ["..."]
rollback: "..."
verified_at: 2026-06-30
```

Không có file đánh giá = chưa được coi là repo đã duyệt. Với `role=install_dependency`, `version_or_commit` phải khớp exact version trong `uv.lock`/`requirements.txt`; với `role=reference_only`, `reference_commit` phải là full SHA nếu có clone local. Với `repo_id="uv"`, thiếu `uv_version` = chưa đủ điều kiện chạy validator trong chế độ tin cậy.

---

## 17. Nguyên Tắc Chống Drift (Mở Rộng)

- Mỗi file có mục đích rõ; mỗi `*_state.md` có front-matter ở đầu.
- Mọi cập nhật ghi ngày; không đổi mục tiêu học nếu chưa ghi lý do.
- Không đánh dấu hoàn thành nếu chưa qua cổng (mục 9.3).
- Không để AI đoán trạng thái khi file đã có dữ liệu.
- Không áp dụng change request khi chưa routing/đánh giá/xác nhận/kiểm xung đột.
- Không xóa review item chưa hoàn thành khi chuyển bài (INV-11).
- Không trộn `_system/` và `learning_vault/` (INV-16..18).
- Không đường dẫn tuyệt đối trong vault (INV-16).
- **Không tự tuyên bố "đã valid" — phải chạy validator và dán kết quả (mục 10.1).**
- Không nâng khẳng định lớp D thành lớp A.

---

## 18. System Prompt Khung (v2.4)

```text
Bạn là AI tutor dài hạn của tôi trong IDE, vận hành theo hệ thống file học tập đã định nghĩa.
Mục tiêu không phải trả lời, mà giúp tôi hiểu bản chất, nhớ lâu, và dạy lại được.

KIẾN TRÚC: hai folder. `_system/` chứa luật/prompt/template/validator/repo công cụ/change request.
`learning_vault/` chỉ chứa bài học, topic, lesson, nguồn, trạng thái, lịch ôn — để mang đi được.
Không trộn hai phần.

CHÍNH XÁC TUYỆT ĐỐI: phân lớp các khẳng định CHÍNH THỨC (claim trong mục `## Claims`): A: cấu trúc/
tính toán; B: bám nguồn confirmed; C: suy luận có tiền đề; D: phán đoán năng lực. Transcript hội thoại
không bị ràng lớp. Cái gì tính được thì TÍNH bằng công thức cố định,
không đoán: lịch ôn, mức thành thạo, chuyển trạng thái, view topic. Không nâng D thành A.

ROUTING: trước khi hành động, phân loại ý định (new_topic, lesson, side_question, review,
source_ingestion, system_change, unclear). Nếu là system_change: KHÔNG áp dụng ngay — ghi change
request, kiểm xung đột với luật cũ, đánh giá rủi ro, viết lại rõ hơn, chờ tôi xác nhận.

GHI DỮ LIỆU: khi nạp file vào context phải ghi read_hash; trong phiên học validate NHẸ (cục bộ);
tại `/done` và `/review` chạy Write Transaction ĐẦY ĐỦ — expected_read_hash → stage →
sinh lại view+hash → CHẠY validate.py → OCC → manifest commit/recovery.
PASS thì commit và dán report, FAIL thì abort/rollback theo manifest. KHÔNG tự nói "đã valid" nếu
chưa chạy validator đầy đủ. Nếu thấy `.tx` dở, recovery trước rồi mới ghi tiếp.

NHỊP HẰNG NGÀY: người dùng chỉ cần `/status` (vào), `/review`, `/resume` hoặc `/learn`, rồi `/done` (ra).
Khi `/resume`/`/status`: CHỈ nạp `*_state.md` + `lesson_notes.md` + section `## Sessions` buổi gần nhất của
`lesson.md` (mục 11B.1); không nạp toàn bộ transcript cũ vào context.

NGUỒN: nguồn mới vào status=raw. Chưa có nguồn VẪN dạy được ở chế độ DRAFT (claim status=draft,
có draft_reason, hiển thị "chưa kiểm nguồn"); chỉ claim status=confirmed có nguồn confirmed mới thành
kiến thức chính thức vào knowledge map. Không bịa nguồn.

DẠY: trước khi dạy đọc trạng thái topic/lesson/lịch ôn. Bắt buộc dùng First Principles + Feynman/
Analogy + Socrates + dạy lại. Trong lesson chỉ hỏi MỘT câu nhỏ mỗi lượt, chờ trả lời xong mới hỏi
tiếp. Câu hỏi phụ ghi vào section Hỏi phụ.

ĐÁNH GIÁ: chấm rubric 5 trục (concept/explain/apply/critique/teachback, 0..3) kèm TRÍCH NGUYÊN VĂN
câu trả lời làm bằng chứng. Chỉ chuyển lesson sang learned khi qua learned_gate. Một câu đúng đơn lẻ
không đủ.

ÔN TẬP: lấy item tới hạn theo quy tắc 8.5 (Review dùng due_date <= logical_today; Learning/Relearning
dùng due_at_utc <= now_utc), hỏi từng câu, chấm grade 0..3 → rating FSRS 1..4, cập nhật bằng engine
FSRS (tham số cố định, fuzzing off). Giữ lại item chưa làm, không xóa log, không tạo trùng.

SAU BUỔI: cập nhật trạng thái/tóm tắt/thẻ ôn/đánh giá/lịch ôn đủ rõ để phiên AI sau tiếp tục ngay.
```

---

## 19. Đặc Tả Validator (Bước Triển Khai Quan Trọng Nhất)

`_system/validator/validate.py` cần:

- Trước khi validate/ghi, chạy **RECOVER-FIRST**: quét `learning_vault/.tx/` và `_system/.tx/` tìm manifest `state in {committing, interrupted}`; recovery được thì hoàn tất roll-forward, không được thì báo `E-TX-PARTIAL` và exit 1 trước khi đọc trạng thái như bình thường.
- Đọc toàn bộ `learning_vault/` bằng file discovery có ignore policy rõ: bỏ qua dotfile/dotdir không thuộc whitelist (`.tx`), `_scratch/` theo INV-20, cache, và cloud-sync conflict artifacts theo basename case-insensitive như `*conflict*`, `*conflicted copy*`, `*(... copy ...)*`, `*PC-conflicted copy*`. Không dùng rule quá rộng kiểu bỏ mọi path chứa chuỗi `copy` trần, vì có thể bỏ nhầm topic hợp lệ như `copywriting`. Mọi file bị ignore vì cloud artifact phải được đưa vào warning `W-IGNORED-CLOUD-CONFLICT` trong report.
- Mọi đọc/ghi text Markdown/YAML/JSON phải dùng `encoding="utf-8"` rõ ràng. Không dùng `open(path)` mặc định, vì Windows có thể dùng code page hệ thống và làm vỡ tiếng Việt. Decode fail → `E-IO-ENCODING`. Content hash/OCC hash dùng bytes thật (`Path.read_bytes()`); canonical JSON hash encode UTF-8 như mục 4.
- Parse front-matter YAML bằng `PyYAML`: tách `---` rồi `yaml.safe_load`, sau đó bắt buộc chạy `normalize_frontmatter()` trước khi đưa vào pydantic/schema/hash/deep-compare. `normalize_frontmatter()` chuyển object do YAML implicit typing sinh ra về dạng canonical theo schema: date → `YYYY-MM-DD`, datetime → UTC/local string đã chốt, bool/int/float giữ đúng type nếu schema yêu cầu, scalar không khớp schema thì để pydantic strict báo lỗi chứ không tự ép.
- Khi dò cấu trúc trong body Markdown (`## Claims`, `#### Evidence ev-*`, `#### Question <qid>`): **bắt buộc dùng parser AST `markdown-it-py`**. Quy trình: duyệt node `heading`, khớp **token tiêu đề đã chuẩn hoá** trên text node heading (cho phép — đây là token cố định, không phải quét prose); với claim/evidence thì **duyệt tiến tới node `fence` (info=`yaml`) ĐẦU TIÊN, bỏ qua mọi node prose (Paragraph) chen giữa, và dừng khi gặp một `heading` kế cùng cấp hoặc cao hơn** (nếu chạm heading kế mà chưa thấy fence → coi như thiếu YAML, báo lỗi cấu trúc). Logic "đầu tiên-trước-heading-kế" này chịu được việc LLM chèn câu dẫn (vd "Dưới đây là bằng chứng:") giữa heading và fence — KHÔNG được dùng quy tắc "fence phải là node ngay sát" vì sẽ gãy oan. KHÔNG dùng regex dò cấu trúc trên prose, KHÔNG parse field bằng regex dòng — mọi field nằm trong fenced YAML (mục 5.5). Bỏ qua nội dung trong các `fence` không liên quan để code block ví dụ không bị bắt nhầm.
- **Schema "chân lý" là model `pydantic` trong `_system/validator/`**, KHÔNG phải các file `*.schema.md`. File `*.schema.md` chỉ là tài liệu cho người đọc, có thể trôi; khi lệch thì model pydantic thắng. (Tùy chọn: sinh `*.schema.md` từ model để khỏi lệch.)
- Kiểm lần lượt `INV-01..INV-26`, gom mọi lỗi (không dừng ở lỗi đầu).
- **Replay** `log` của mỗi review item qua FSRS (đúng `fsrs_config_version`) và so khớp `card` (`INV-08`); `stability`/`difficulty` so bằng dung sai float (`math.isclose 1e-4`), `last_reviewed_at_utc` so exact, `due_date` so exact (mọi trạng thái), `due_at_utc` so exact CHỈ khi `Learning/Relearning` (v2.6/F-B, mục 8.3).
- Tính lại `mastery_state = derive_mastery(card, log)` và so khớp (`INV-21`).
- Tự sinh lại **toàn bộ view object** trên đúng miền băm đã định nghĩa (mục 4), deep-compare nội dung view và so `generated_from_hash` (`INV-09`).
- Kiểm evidence cho trục mastery đạt ngưỡng (`INV-22`) + verbatim-substring transcript (`INV-22b`) và vùng/đủ trường của claim (`INV-23`), gồm luật draft/confirmed: draft phải có `draft_reason`, không được vào Knowledge Map, không được làm tiền đề cho claim confirmed.
- Quét chuỗi đường dẫn tuyệt đối (`C:\`, `/Users/`, `/home/`) trong vault (`INV-16`).
- Tính ngày theo `vault_state.utc_offset` (stdlib `datetime`, không cần tzdata).
- Nhận tham số `--level light|full` (mặc định `full`); ở `light` chỉ chạy nhóm INV cú pháp/schema/ngày của file được chỉ định (mục 10.8).
- Xuất report máy đọc được (JSON) và người đọc được (bảng), gồm cả warnings không-fatal như `W-IGNORED-CLOUD-CONFLICT`.
- Exit code: 0 = PASS, 1 = có lỗi.

Phụ thuộc runtime: `fsrs`, `pydantic`, `PyYAML`, `markdown-it-py` (mục 16.1). Phụ thuộc dev/test: `pytest`. Ngày tính bằng stdlib `datetime` + offset (không tzdata). Môi trường tin cậy cài từ `uv.lock` exact bằng `uv sync --frozen`; fallback dùng `requirements.txt` exact+hash với `pip install --require-hashes`. Chạy được offline, ít dependency để giữ portability.

---

## 20. Những Việc Chưa Làm & Thứ Tự Triển Khai

Bản này đã chốt: kiến trúc 2 folder, mô hình **toàn vẹn cấu trúc đúng tuyệt đối + tầng phán đoán audit được** (phân lớp + bất biến, giới hạn ở mục 0.3), nguồn sự thật duy nhất, số file tối giản, **engine lịch ôn FSRS** (thay thuật toán box tự chế), rubric rời rạc + evidence, cổng "đã hiểu", claim/evidence contract, transaction-safe manifest (LIGHT/FULL + recovery), xoá có thẩm quyền (tombstone), cờ phiên chưa đóng sổ, cơ chế chạy validator, và quy trình change request có kiểm xung đột.

Thứ tự triển khai (đã sắp theo độ phụ thuộc — lõi trước, vỏ sau):

1. **Tạo repo evaluation files cho các dependency/công cụ cài thật**: `fsrs`, `pydantic`, `PyYAML`, `markdown-it-py`, `pytest`, **và `uv`** (tool cài thật); ghi license, exact version/lock source, `uv_version`, lý do, rủi ro, rollback.
2. **Khởi tạo môi trường bằng `uv` trong giai đoạn bootstrap/change request** (`uv init`; `uv add fsrs pydantic pyyaml markdown-it-py`; `uv add --dev pytest`; tạo `_system/.venv` + `uv.lock` + xuất `requirements.txt --generate-hashes`). Sau khi lock đã chốt, mọi lần chạy validator bình thường dùng `uv sync --frozen`; fallback dùng `pip install --require-hashes -r requirements.txt`. Viết `fsrs_config.yaml` (copy cứng mảng weights, fuzzing off) + `fsrs_adapter.py` + golden test FSRS replay. Đây là nền của lịch ôn deterministic.
3. **Viết `validate.py` + `invariants.md` + `error_codes.md`** (INV-01..26), kèm hàm replay FSRS và `derive_mastery`.
4. **Viết golden fixtures `_system/validator/tests/`** (mục 10.6) — validate the validator — và đạt test trước khi tin.
5. **Chốt cơ chế chạy validator** (bước shell bắt buộc cho `/validate` `/done` + transaction; hook IDE là tăng cường, mục 10.5) — không có nó thì cam kết "đúng tuyệt đối" chỉ là khẩu hiệu.
6. Viết các schema trong `_system/schemas/` (lesson_state, topic_state, sources, review_item, vault_state).
7. Khóa ánh xạ grade→rating + cấu hình FSRS vào `review_rules.md`.
8. Viết rubric 5 trục đầy đủ + `learned_gate` + evidence contract vào `teaching_rules.md`.
9. Viết `claim_rules.md` + `validation_rules.md`.
10. Viết `commands.md` (registry, mục 11A) + `router_prompt.md` + `system_prompt.md` + `system_change_prompt.md`.
11. Tạo template thật cho topic/lesson (3 file mỗi loại) + cơ chế transaction-safe manifest/recovery (`.tx/`) + `migrations/`.
12. Tạo một topic thử nghiệm trong `learning_vault/`, chạy validator tới khi PASS.
13. Kiểm chéo: một phiên AI khác đọc vault + `_system/` có tiếp tục đúng trạng thái không.

---

## Phụ Lục A. Nhật Ký Vá Theo Version

Bản v2.1 không đổi kiến trúc; nó **vá các mâu thuẫn/định nghĩa hở** trong v2 để spec triển khai được mà không gãy. Tóm tắt từng vá và chỗ sửa:

| # | Vấn đề trong v2 | Cách vá v2.1 | Mục đã sửa |
|---|-----------------|--------------|------------|
| 1 | Heading Evidence lệch cấp (`### Evidence` ở 5.5/10.8 vs `#### Evidence` ở 14A) → AST bắt nhầm | Chốt **`#### Evidence` (cấp 4)** ở mọi nơi | 5.5, 10.8, 14A |
| 2 | Claim/Evidence là text rời / YAML không fence → "không regex" tự mâu thuẫn | Bắt buộc **heading + fenced ```yaml``` liền sau**; parse = AST heading-token + `yaml.safe_load` | 5.5, 14A, 19 |
| 3 | `"Cần ôn hôm nay"` loại `mastered` nhưng lại nói mastered có thể tới hạn → thẻ mastered kẹt vĩnh viễn | Gộp cả `mastered` vào danh sách, sắp theo **nhóm ưu tiên** (need_redo→in_review→mastered) | 8.5 |
| 4 | `due` lưu date nhưng FSRS trả datetime; thiếu quy tắc cắt | v2.1 thêm `due_truncation` cố định + so khớp date thuần; **v2.3 thay bằng `due_projection` + `due_at_utc`** | 8.3, INV-08, 19, A.4 |
| 5 | Miền băm `generated_from_hash` không định nghĩa → false-stale / vòng tự tham chiếu | Định nghĩa **chính xác tập field** cho review_schedule & assessment, loại field view | 4, 7, 19 |
| 6 | "Mọi ghi qua transaction" (11A) vs "trong phiên chỉ LIGHT" (10.8) đá nhau | Tách **cơ chế ghi** (luôn áp) khỏi **mức validate** (LIGHT/FULL); **v2.3 đổi thành transaction-safe manifest** | 10.3, 11A, 19, A.4 |
| 7 | Không có cờ phát hiện phiên bỏ dở, nhưng /status hứa nhắc | Thêm `vault_state.open_session` + quy trình phát hiện | 5.4, 11B.2 |
| 8 | INV-11 chặn xoá item → không có đường xoá lesson/topic hợp lệ | Thêm **xoá có thẩm quyền + tombstone** và lệnh `/forget`; INV-11 tha khi có tombstone | 10.3a, 11A.2, INV-11 |
| 9 | INV-19 "tương thích" mơ hồ; migration không có rollback | Chốt quy tắc semver (major bằng, minor ≤) + `E-SCHEMA-AHEAD`; migration chạy trong transaction-FULL | INV-19, 10.3b |
| 10 | Hai nguồn schema (`*.schema.md` vs pydantic) dễ trôi | Chốt **pydantic là chân lý**, `.schema.md` chỉ là tài liệu | 19, 16.1 (đã nêu) |
| — | "Chính xác tuyệt đối" nói quá so với cái validator kiểm được | Đổi nhãn thành **"toàn vẹn cấu trúc đúng tuyệt đối + tầng phán đoán audit được"** + thêm mục giới hạn | tiêu đề, 0.3, 20 |

Mã lỗi mới: `E-REVIEW-LOST` (mất item không tombstone), `E-SCHEMA-AHEAD` (vault mới hơn hệ thống).

**Lưu ý phạm vi v2.1:** đây mới là vá *tính nhất quán nội tại của spec*. Hai việc lớn còn để ngỏ (cố ý, vì không thuộc loại "lỗi spec"):

1. **Lớp D vẫn không được enforce tái lập** (mục 0.3) — cần một bước thử nghiệm inter-rater thật (cho 2 phiên AI chấm cùng transcript, đo lệch) trước khi tin rubric đủ chặt; đây là việc *vận hành*, không phải sửa file.
2. **ROI / độ phức tạp**: nên cân nhắc một **"lõi tối giản v1"** (schema + state machine + FSRS + transaction + ~10 INV cấu trúc) để bắt đầu học sớm, hoãn claim B/C/D contract, migrations, repo_lab. Xem đây là khuyến nghị lộ trình, chưa đưa vào phần "đã chốt".

### A.1. Lộ Trình MVP 3 Giai Đoạn (cụ thể hoá khuyến nghị #2)

Để "lõi tối giản v1" không còn mơ hồ, đây là 3 giai đoạn xếp theo độ phụ thuộc — học được thật từ Giai đoạn 1, đắp kiểm soát ngữ nghĩa sau:

| Giai đoạn | Mục tiêu | Invariant kiểm | Package |
|---|---|---|---|
| **GĐ1 — Lõi vận hành** | Tạo topic/lesson, học hỏi-đáp, FSRS deterministic, transaction-safe manifest. CHƯA có claim/evidence. | `INV-01..06`, `INV-08`, `INV-09`, `INV-10`, `INV-16..21`, `INV-24..25` | `fsrs`, `pydantic`, `PyYAML` |
| **GĐ2 — Cưỡng chế toàn vẹn** | Thêm AST parser; cổng "đã hiểu" + evidence; claim B/C/D; verbatim-check. Hoàn thiện FULL. | thêm `INV-07`, `INV-11..15`, `INV-22..23`, `INV-26` | thêm `markdown-it-py`, `pytest` |
| **GĐ3 — Tối ưu & vỏ** | Cache replay (10.9a), validate vi sai (10.9b), `/fix`, `open_session`, migrations, repo_lab. | tối ưu hoá, không thêm tiêu chí đúng/sai mới | giữ nguyên |

Nguyên tắc: **chỉ lên GĐ sau khi GĐ trước đã PASS golden fixtures (mục 10.6)**. GĐ1 đủ để dùng hằng ngày; GĐ2 mới là phần biến hệ thống thành "đúng tuyệt đối ở tầng cấu trúc"; GĐ3 thuần hiệu năng/UX, có thể hoãn vô thời hạn nếu vault còn nhỏ.

> Ghi chú nguồn: GĐ-hoá, calibration few-shot (9.5), cache replay + validate vi sai (10.9), và `/fix` được rút từ một bản đánh giá ngoài, đã **sửa lại cho khớp mô hình tin cậy** (đặc biệt: cache replay nằm ngoài vault, không phải snapshot trong `lesson_state.md`).

### A.2. Kiểm Toán Dependency (2026-06-30)

Đối chiếu các repo/package ở mục 16 với nguồn chính thức (PyPI/GitHub) tại thời điểm đánh giá:

| Package | Phát hiện | Tình trạng | Hành động đã vá |
|---|---|---|---|
| `fsrs` (py-fsrs) | Bản mới nhất **6.3.1** (2026-03-10), MIT, `requires_python>=3.10`, runtime chỉ `typing-extensions`. API `Scheduler/Card/Rating/ReviewLog`, `review_card`, có `to_json/from_json`. **FSRS-6 = 21 weights**. **README ghi rõ: py-fsrs CHỈ nhận UTC.** | ✅ Phù hợp, pin giữ `6.3.1` | Sửa "~19–21"→**21**; thêm **luật convert UTC** (8.4/8.5) — kẽ hở determinism; thêm py≥3.10 |
| `fsrs[optimizer]` | Optimizer giờ là **extra của chính `fsrs`** (không còn package rời), kéo `torch/numpy/pandas` | ✅ Đúng quyết định loại | Cập nhật 16.3: "không cài extra `[optimizer]`" |
| `pydantic` | V2 ổn định, mới nhất **2.13.x** (2026-05), V1 nhúng kèm | ✅ | Pin `>=2.13,<3` |
| `markdown-it-py` | Mới nhất **4.x** (2026), executablebooks, 100% CommonMark | ✅ | Pin `>=4,<5` |
| `PyYAML` | 6.x, `safe_load` chuẩn, ổn định (nhịp bảo trì chậm nhưng phổ biến) | ✅ | Pin `>=6,<7` |
| `pytest`, `uv` | Active, chuẩn ngành | ✅ | Giữ nguyên |
| `google/agents-cli` | **Repo có thật**, build quanh ADK + Google Cloud, kế thừa `agent-starter-pack` | ✅ Xác nhận phân loại "chỉ tham khảo" của spec là đúng và còn cập nhật | Không đổi |
| ADK / claude-cookbooks / openai-cookbook / openai-evals | Đều là repo thật, dùng để đọc thiết kế | ✅ | Không đổi |

**Kết luận audit:** lựa chọn dependency của spec **vững và còn đúng tới 2026-06**; bộ cài cực gọn (lõi chỉ `fsrs`+`typing-extensions`, rất tốt cho portability). Lỗi thực chất duy nhất là **bỏ sót ràng buộc UTC-only của py-fsrs** — đã vá ở mục 8.4/8.5 (nếu không, `due`/replay lệch giờ và INV-08 báo `E-REVIEW-MISCALC` oan hoặc tệ hơn là sai mà không bị bắt).

### A.3. Vá Tầng Thực Thi v2.2 (2026-06-30) — Từ Review Kiến Trúc Sư

Rút từ một bản review tầng implementation (OS/filesystem/LLM behavior). Đã thẩm định, giữ cái đúng, sửa cái quá tay:

| # | Vấn đề thực thi | Quyết định | Mục đã sửa |
|---|---|---|---|
| 1 | Verbatim INV-22b vỡ do whitespace/nháy cong | ✅ Nhận, **nhưng sửa**: chỉ chuẩn hoá NFC + nháy/gạch + gộp whitespace; **KHÔNG** lowercase/bỏ dấu câu/bỏ dấu TV (sẽ phá chống-bịa) | 9.6, INV-22b |
| 2 | AST "fence liền sau" gãy khi LLM chèn câu dẫn | ✅ Nhận: duyệt tới fence YAML **đầu tiên trước heading kế cùng/cao cấp** | 5.5, 19 |
| 3 | Float lệch hash đa nền tảng | ✅ Nhận (hardening) **+ đính chính**: miền băm hiện không có float; lệch thật do tính FSRS, chống bằng làm tròn trước khi lưu (đã có), không phải do `json.dumps` | 4 |
| 4 | Cloud sync (OneDrive…) khóa file → `os.replace` WinError 32 | ✅ Nhận (rất sát): retry exponential-backoff khi commit | 10.3 |
| 5 | TOCTOU: sửa tay trong lúc validate bị ghi đè | ✅ Nhận: OCC bằng **content-hash** (mạnh hơn mtime) → `E-CONCURRENT-EDIT` | 10.3, bảng lỗi |
| 6 | Thẻ tới hạn lúc 00:01 giữa buổi đêm | ✅ Nhận: `day_cutoff_hour` (mặc định 4h kiểu Anki), **phạm vi hẹp**: chỉ cho lọc "ôn hôm nay", KHÔNG đụng dấu ngày/INV-05 | 5.4, 8.5 |
| T1 | `pydantic strict=True` chặn ép kiểu ngầm | ✅ Nhận — validator phải bắt lỗi, không âm thầm sửa | 16.1 |
| T2 | `ruamel.yaml` giữ comment khi round-trip | ◐ Nhận **có điều kiện**: giữ PyYAML mặc định (state file là máy-quản, không comment tay); chỉ đổi nếu cho sửa tay front-matter | 16.1 |

Mã lỗi mới: `E-CONCURRENT-EDIT`. Config mới: `vault_state.day_cutoff_hour`.

**Ghi chú lịch sử v2.2:** toàn bộ phần này là tầng *thực thi vật lý*, KHÔNG đổi tính đúng của kiến trúc logic. Sau review v2.3, điều kiện "sẵn sàng code Giai đoạn 1" được siết thêm ở A.4.

### A.4. Vá Chính Xác v2.3 (2026-07-01) — Chốt Trước Khi Code

Vá từ review độ tin cậy triển khai. Mục tiêu: bỏ các lời hứa quá mức và đóng các kẽ hở validator có thể bỏ sót khi biến spec thành code.

| # | Vấn đề còn hở | Quyết định v2.3 | Mục đã sửa |
|---|---|---|---|
| 1 | Version tự lệch: tiêu đề v2.1, phụ lục v2.2, prompt v2 | Tại thời điểm v2.3, chốt tài liệu là **v2.3**; v2.1/v2.2 giữ lại như lịch sử vá | tiêu đề, trạng thái, 18, Phụ lục A |
| 2 | `os.replace` bị mô tả như atomic cho cả transaction nhiều file/nhiều root | Đổi cam kết thành **file-level atomic + manifest + recovery**; thêm `E-TX-PARTIAL` và RECOVER-FIRST | 10.3, 10.4, 19, 20 |
| 3 | `INV-06` đòi kiểm chuyển trạng thái nhưng validator tĩnh không có trạng thái trước | Chỉ enforce cạnh chuyển trạng thái khi có baseline transaction (`backup → staged`); ngoài transaction chỉ kiểm trạng thái hiện tại + hệ quả tĩnh | INV-06, 10.3 |
| 4 | View chỉ so `generated_from_hash`, có thể bỏ sót nội dung view sai nhưng hash giữ nguyên | Validator phải **regen full view object + deep-compare + so hash**; thêm `E-VIEW-MISMATCH` | 4, 7, INV-09, 19 |
| 5 | Lưu `due` dạng date làm mất time-of-day của Learning/Relearning | Lưu **`due_at_utc` authoritative + `due_date` dẫn xuất**; Review dùng day cutoff, Learning/Relearning dùng datetime thật | 4, 5.1, 5.2, 7, 8.2..8.5, INV-08 |
| 6 | Draft claim và claim lớp B confirmed bị lẫn luật nguồn | Chốt `status=draft` là ghi chú làm việc: phải có `draft_reason`, không cần source, không vào Knowledge Map, không làm tiền đề confirmed | 0.1, 5.5, INV-12/14/15/23/26, 15.1 |
| 7 | Single source of truth còn rò `current_lesson` và `topic_state.lessons[].status` | Chốt chúng là cache/index: phải khớp `vault_state`/`lesson_state`, lệch → `E-INDEX-MISMATCH` | 4, 5.2, INV-25 |

**Hệ quả triển khai:** Giai đoạn 1 phải code manifest/recovery và `due_at_utc` ngay từ đầu; không nên code schema date-only rồi migration sau, vì sẽ tạo dữ liệu FSRS thiếu precision.

### A.5. Vá Dependency/IO v2.4 (2026-07-01) — Chốt Môi Trường Tin Cậy

Vá từ review dependency và implementation gotchas trước khi code. Mục tiêu: môi trường chạy validator không bị trôi theo package/tool/repo upstream, và I/O vật lý không phá cam kết tái lập.

| # | Vấn đề còn hở | Quyết định v2.4 | Mục đã sửa |
|---|---|---|---|
| 1 | Dependency runtime dùng range dễ trôi dù spec nói "đúng tuyệt đối" | `pyproject.toml` được dùng range tương thích; runtime chỉ cài từ `uv.lock` exact bằng `uv sync --frozen`; fallback `pip install --require-hashes` | 16.0, 16.0A, 16.1, 19, 20 |
| 2 | `uv` là lock tool nhưng chưa pin version tool | Repo evaluation của `uv` phải ghi `uv_version`; không tự nâng `uv`; production không chạy `uv add/lock/sync` thiếu `--frozen` | 16.0A, 16.1, 16.4, 20 |
| 3 | PyYAML implicit typing có thể tạo object date/bool rồi làm hash/compare lệch | Sau `yaml.safe_load` bắt buộc `normalize_frontmatter()` về canonical object/string theo schema trước pydantic/hash/deep-compare | 16.0, 16.1, 19 |
| 4 | Reference repo clone `main` có thể âm thầm đổi pattern thiết kế | Reference repo phải pin `reference_commit`, `verified_at`, `refresh_policy: manual only via change request` | 16.2, 16.4 |
| 5 | Repo tham khảo thiết kế dễ bị lẫn thành nguồn học confirmed | `_system/repo_lab/reference_repos/` KHÔNG tự động là nguồn lesson; muốn dùng cho bài học phải đưa vào `sources.md`, tạo anchor, status confirmed | 16.2 |
| 6 | OpenAI Evals có thể bị kéo nhầm vào runtime eval | Rubric/eval mặc định dùng `pytest` fixtures + JSON expected trước; OpenAI Evals chỉ là cảm hứng registry/eval | 16.2, 16.3 |
| 7 | OCC chụp hash lúc BEGIN vẫn ghi đè sửa tay xảy ra trong lúc AI sinh text | Transaction phải nhận `expected_read_hash` từ thời điểm file được nạp context; lệch trước BEGIN → `E-STALE-CONTEXT` | 10.3, 10.4, 18 |
| 8 | Ghi `manifest.json` trực tiếp có thể tạo JSON rách khi crash | Mọi cập nhật manifest dùng `atomic_write_manifest()` qua tmp + fsync + replace | 10.3 |
| 9 | Verbatim evidence vỡ oan khi transcript có Markdown inline formatting | `normalize_for_match` render/strip Markdown inline delimiter hẹp trên cả quote và transcript | 9.6 |
| 10 | `has_draft_knowledge` do AI sửa tay vi phạm "Tính, đừng đoán" | Chuyển thành view sinh tự động từ việc còn claim draft; FULL-regen tự cập nhật | 4, 5.2, INV-26, 10.3, 15.1 |
| 11 | Windows default encoding làm vỡ tiếng Việt | Mọi đọc/ghi text dùng `encoding="utf-8"` rõ ràng; hash OCC dùng bytes | 19, 10.4 |
| 12 | Cloud sync sinh file conflict/copy làm validator đọc nhầm | File discovery ignore cloud conflict artifacts có warning `W-IGNORED-CLOUD-CONFLICT`; không dùng rule quá rộng bỏ mọi path chứa `copy` | 19, 10.4 |

**Hệ quả triển khai:** trước khi cho LLM ghi vault thật, Giai đoạn 1 phải có test cho dependency freeze (`uv sync --frozen`), `normalize_frontmatter`, `expected_read_hash`, atomic manifest corruption/recovery, UTF-8 Vietnamese file, và cloud-conflict ignored warning.

### A.6. Vá Schema Card / Edge Cases v2.5 (2026-07-01) — Chốt Cuối Trước Code

Vá từ review "cực sâu" cuối cùng. Không đụng kiến trúc; đóng nốt các điều kiện biên mà `strict=True` sẽ bắt oan hoặc golden test dễ bỏ sót.

| # | Vấn đề còn hở | Quyết định v2.5 | Mục đã sửa |
|---|---|---|---|
| 1 | Thẻ New / chưa review có `stability=difficulty=None` (py-fsrs 6.x) nhưng schema khai float bắt buộc → `strict=True` reject oan item mới | `stability`/`difficulty`/`last_reviewed_at_utc`/`step` là **Optional, ràng buộc theo `state`**: `New` ⇒ null + `log` rỗng; `!=New` ⇒ phải có giá trị. Định nghĩa rõ "item mới tạo" | 5.1 |
| 2 | `math.isclose` cứu `stability/difficulty` nhưng `due_at_utc` so exact + nằm trong hash → lệch interval ở ranh giới float đa nền tảng | `fsrs_adapter` phải **quantize `stability` (round 4) TRƯỚC khi tính interval/`due`**; golden fixtures bắt buộc có ca cross-platform (x86/ARM) nhắm ranh giới interval | 8.3 |
| 3 | Tên block cũ "Tôi trả lời / AI phản hồi" lẫn với tên chính tắc `#### Bạn trả lời <qid>` | Thống nhất tên block theo template 14A | 3.1, 9.3 |
| 4 | Mục 14 bước 5 thiếu regen `has_draft_knowledge`; bước 7 dùng từ "rollback" cũ | Bổ sung `has_draft_knowledge` vào regen; đổi bước 7 theo mô hình abort/RECOVER-FIRST (mục 10.3) | 14 |
| 5 | `/fix` (LIGHT) có thể reflow khoảng trắng trong `evidence.quote` mà không bị INV-22b bắt lại | Cấm `/fix` đổi khoảng trắng bên trong giá trị string của fenced YAML | 11A.2 |

**Kết luận v2.5:** không còn vấn đề kiến trúc/logic/edge đã biết chặn việc code Giai đoạn 1. Fix #1 là bắt buộc trước khi viết pydantic model (nếu không, `strict=True` chặn oan mọi review item chưa review). Fix #2 là mục tiêu golden test cross-platform, không phải đổi spec. Còn lại là dọn chữ cho người triển khai khỏi lăn tăn.

### A.7. Vá Theo SPIKE FSRS Thật v2.6 (2026-07-01) — Đã Chạm API

Sau khi **cài `fsrs==6.3.1` thật và chạy spike** (kết quả đầy đủ ở `_system/repo_lab/repo_evaluations/fsrs.md`), hai giả định của v2.5 sai so với API thật, phải sửa TRƯỚC khi code:

| # | Giả định v2.5 | Thực tế API (spike) | Quyết định v2.6 | Mục đã sửa |
|---|---|---|---|---|
| F-A | `card.state` có `New` | `State` enum chỉ `{Learning, Review, Relearning}`; thẻ mới = `Learning`, `stability/difficulty=None`, `last_review=None` | Bỏ `New` khỏi enum; "chưa review" = `log` rỗng / `last_reviewed_at_utc == null`; `derive_mastery` nhánh `new` = log rỗng | 5.1, 6.2 |
| F-B | Quantize stability TRƯỚC khi tính due; so `due_at_utc` exact + đưa vào hash | `due` tính NỘI BỘ `review_card` từ float transcendental; KHÔNG có hook/formula interval public → không thể ép due bit-identical cross-CPU | `due_date` (ngày) là trục lịch ôn + so khớp chuẩn; `due_at_utc` chỉ so exact ở `Learning/Relearning` (bước cố định); bỏ `due_at_utc` khỏi hash view | 4, 5.2, 7, 8.3, INV-08 |

Xác nhận thêm từ spike (spec đã đúng): `review_datetime` BẮT BUỘC aware-UTC (reject cả naive lẫn `+07:00`); `enable_fuzzing=False` cho kết quả tất định; 21 weights FSRS-6 (đã ghi cứng vào `fsrs_config.yaml`); runtime chỉ phụ thuộc `typing-extensions`.

**Giới hạn thực thi bổ sung (nối mục 0.3):** lịch ôn của thẻ `Review` chuẩn theo **ngày local** (`due_date`), KHÔNG theo giây. `due_at_utc` của thẻ Review là thông tin, không đảm bảo bit-identical giữa các CPU/libm khác nhau (FSRS dùng exp/pow). Đây là giới hạn của mọi hệ dùng float transcendental, không phải lỗi thiết kế; chọn `due_date` làm trục chuẩn là cách trung thực và đủ cho spaced repetition (vốn tính theo ngày).

**Trạng thái code (2026-07-01):** đã dựng `_system/.venv` + cài đủ 4 package runtime + pytest; `fsrs_config.yaml` (21 weights thật); `validator/fsrs_adapter.py` (grade→rating, new-card, replay, review, derive_mastery, cards_equal theo F-B); `validator/tests/phase01_fsrs/` **7/7 PASS** (gồm replay tất định + replay==incremental, nền tảng INV-08). P00 + P01 coi như xanh.
