# P01 — FSRS Adapter & Lõi Deterministic (RỦI RO CAO NHẤT)

**Mục tiêu:** bọc API thật của `fsrs` thành lớp thuần, xác định, tái lập cross-platform. Đây là lõi giá trị và chỗ dễ vỡ nhất.
**Phụ thuộc:** P00.
**Giai đoạn MVP:** GĐ1.

## P01.0 — SPIKE API TRƯỚC KHI CODE (ĐÃ XONG 2026-07-01 — kết quả ở `repo_evaluations/fsrs.md`)

> **ĐÃ CHỐT (v2.6):** spike xác nhận (a) py-fsrs KHÔNG có `State.New` → thẻ mới = `Learning`, log rỗng (F-A);
> (b) `due` tính nội bộ `review_card`, KHÔNG có hook/formula interval public → **Strategy A bất khả thi sạch → chọn Strategy B**,
> đã duyệt thành spec v2.6 (due_date là trục so khớp chuẩn; due_at_utc chỉ exact cho Learning/Relearning; bỏ khỏi hash).
> Adapter đã code + 9/9 test xanh. Phần A/B bên dưới giữ làm lịch sử quyết định.

Pseudocode spec 8.4 chỉ là logic. `due` có thể do `Scheduler.review_card` tính SẴN bên trong → không có chỗ "quantize stability trước khi tính due" nếu không can thiệp sâu. **Phải spike API py-fsrs 6.3.1 thật và ghi kết quả vào `_system/repo_lab/repo_evaluations/fsrs.md`** trước khi chốt cách làm:

```text
Câu hỏi spike:
1. review_card(card, rating, review_datetime) trả về gì? (new_card, review_log?) Có field due/stability/difficulty?
2. Có hàm/formula PUBLIC tính interval từ stability không (vd next_interval / get_retrievability)?
3. Card có to_dict/to_json + from_dict/from_json để serialize ổn định không?
4. Card mới (chưa review) có stability/difficulty = None không? state khởi tạo là gì?
5. review_datetime bắt buộc aware-UTC? (README nói CÓ) — thử truyền naive/local xem có raise.
```

**Chốt chiến lược determinism theo kết quả spike (chọn 1, ghi lý do vào fsrs.md):**

- **A. Nếu interval là số ngày NGUYÊN từ formula public:** `due_at_utc` tất định (last_review + N ngày), lệch chỉ ở ranh giới do stability float. Chống bằng: **quantize stability round-4 rồi tự tính interval bằng đúng formula public của version pin** → due = last_review + interval. Chỉ dùng formula đã tài liệu hoá của đúng `fsrs==6.3.1`, không tự chế.
- **B. Nếu KHÔNG can thiệp được trước due:** lấy `due` từ `review_card` như-là, và **hạ yêu cầu so khớp INV-08 cho `due_at_utc` xuống mức ngày**.
  ⚠️ **B MÂU THUẪN spec v2.5** (mục 8.3 bắt buộc "quantize stability TRƯỚC khi tính interval/due" + INV-08 so `due_at_utc` exact). Vì vậy theo spec hiện hành: **chọn A → P01 được PASS; nếu chỉ B khả thi → P01 BỊ BLOCK.** Không được viết golden test theo B rồi coi là đạt. Phải mở **change request sửa spec 8.3/INV-08 lên version mới (vd v2.6) và được duyệt TRƯỚC**, rồi mới code B. Ghi rõ quyết định + link change request vào `fsrs.md`.

> Không code P01.1 khi chưa: (a) chốt A, hoặc (b) có change request duyệt cho B. Đây là chỗ "đúng tuyệt đối" dễ thành giả nếu lách.

## P01.1 — Xây gì

`_system/validator/fsrs_adapter.py` — thuần hàm, KHÔNG I/O file:

- `map_grade_to_rating(grade:int)->int` — bảng 8.1 (0→1,1→2,2→3,3→4); grade∉0..3 → raise `EReviewBadGrade`.
- `new_card(created_utc)->CardDict` — card `state=Learning` (py-fsrs không có New, v2.6/F-A), `stability=None`, `difficulty=None`, `step=0`,
  `last_reviewed_at_utc=None`, `due_at_utc=created_utc`, `due_date=project(created_utc)` (spec 5.1 item mới).
- `review(card_dict, grade, reviewed_at)->CardDict` — spec 8.4:
  `.astimezone(utc)` (py-fsrs **UTC-only**) → `review_card` → áp chiến lược determinism đã chốt ở P01.0 (A: quantize+tự tính due; B: lấy due như-là) → serialize.
- `replay(created_utc, initial_card, log, fsrs_config)->CardDict` — dựng từ `new_card`/`initial_card` rồi áp tuần tự `log` (spec 8.5, INV-08).
- `derive_mastery(card, log)->str` — 4 nhánh spec 6.2.
- `project_due(due_at_utc, utc_offset)->(due_at_utc_canonical, due_date)` — spec 8.3 `due_projection`.
- `cards_equal(a,b)->bool` — `stability/difficulty`: `math.isclose(abs_tol=1e-4)`; `due_at_utc`/`due_date`: so theo **mức đã chốt ở P01.0** (A: exact; B: day-granularity).

## INV/mục spec liên quan

8.1–8.5, 6.2, INV-08, INV-21, 5.1 New-card.

## Cách test (golden JSON, `_system/validator/tests/phase01_fsrs/`)

```text
[ ] SPIKE ghi xong fsrs.md: 5 câu hỏi có câu trả lời + chiến lược A/B đã chọn + lý do.
[ ] grade→rating: 4 cặp đúng; grade=5, grade=-1 → EReviewBadGrade.
[ ] new_card: stability/difficulty/last_reviewed_at_utc == None; state==New; due_at_utc==created.
[ ] replay khóa cứng: log [(t1,3),(t2,2),(t3,1)] → card kỳ vọng (JSON vàng), so bằng cards_equal.
[ ] replay từ initial_card (import) → khớp; replay log rỗng → giữ New.
[ ] derive_mastery: phủ new / need_redo(rating cuối=1) / need_redo(Relearning) / mastered / in_review.
[ ] round-trip serialize/deserialize card (gồm New-card null) không đổi.
[ ] CROSS-PLATFORM boundary: ca stability sát ranh giới interval → cùng kết quả theo mức so khớp đã chốt (x86 vs ARM).
[ ] Determinism: replay 100 lần → cùng output.
```

## Cạm bẫy

- **py-fsrs CHỈ nhận datetime aware UTC.** Quên `.astimezone(utc)` → due lệch giờ → INV-08 báo oan.
- `enable_fuzzing=False` bắt buộc.
- New-card có `stability=None` — mọi hàm phải chịu được null.
- KHÔNG tự chế lại formula FSRS ở chiến lược A — chỉ dùng formula public của đúng version pin; nếu không chắc → chọn B + change request.
