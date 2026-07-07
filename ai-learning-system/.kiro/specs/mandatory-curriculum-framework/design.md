# Design Document

## Overview

Tính năng **Khung giáo trình bắt buộc** (`mandatory-curriculum-framework`) thêm một tầng **khung sườn**
(`Topic_Blueprint`) phía trên `curriculum-driven-learning`. Blueprint tuyên bố các **Mandatory_Area** (mảng
kiến thức bắt buộc) sắp theo lộ trình zero→chuyên-gia; validator ép **giáo trình (`curriculum.md`) phải phủ
đủ** mọi mảng bắt buộc trước khi được-phép-dạy.

Thiết kế bám **kiến trúc sẵn có** (không phát minh lại), đã được xác minh trực tiếp trên mã nguồn:
- **Validator là chân lý** (INV-01..26). Mọi thuộc tính máy-đảm-bảo của Blueprint + quan hệ phủ có mã lỗi
  riêng + test (Class A). Blueprint_Validator là phần MỞ RỘNG của `validate.py`, KHÔNG phải bộ máy thứ hai.
- **Write Transaction** cho mọi ghi vault (backup → validate → commit/rollback).
- **`topic_state.lessons[]`** vẫn là index bài (INV-25). Blueprint KHÔNG đụng vào index này.
- **Cổng `teachable`** của curriculum đã có (chặn `cmd_next_lesson`) — feature này thắt chặt cổng đó, không
  tạo cổng mới.
- **Artifact tùy chọn wire theo mẫu `_check_curriculum`/`_check_exam_results`** trong `_validate_topic`
  (chỉ chạy khi file tồn tại) — Blueprint_Validator wire y hệt.
- Mọi lệnh/schema/spec mới đi qua **change-request §12** (không sửa nóng).

## Ranh giới bảo đảm (quyết định kiến trúc)

- **Class A (máy đảm bảo — validator là chân lý):** blueprint đúng schema; mỗi Mandatory_Area có định danh
  duy nhất + tiêu đề không rỗng + order hoán vị liên tục 1..N; blueprint approved → curriculum phủ đủ mọi
  mảng bắt buộc; ánh xạ point→area trỏ mảng tồn tại (INV-03); point không-ngoài-khung khi có blueprint
  approved; con trỏ/trạng thái hợp lệ; portable (INV-16); phân vùng code/dữ liệu (INV-17/18); chỉ teachable
  khi phủ đủ.
- **Class D (người/AI đánh giá — validator KHÔNG tự nhận):** các mảng bắt buộc có **thật sự đủ để thành
  chuyên gia** không; nội dung mỗi mảng có **chính xác/đủ sâu** không. Máy chỉ ép **phủ đủ mảng đã khai
  báo**, KHÔNG bảo đảm "khung đúng tầm chuyên gia" (R3.7).

## Ba quyết định thiết kế gốc (đã chốt, có căn cứ)

### QĐ-1: Coverage_Map đặt ở phía CURRICULUM (`CurriculumPoint.area_refs`), KHÔNG ở blueprint

`CurriculumPoint` hiện KHÔNG có field ánh xạ tới Mandatory_Area (đã đọc `models.py`:297). Thêm
`area_refs: list[str] = []` vào `CurriculumPoint`. Phủ đầy = mỗi Mandatory_Area **bắt buộc** có id xuất
hiện trong `area_refs` của ≥1 Curriculum_Point.

**Vì sao phía curriculum, không phía blueprint:** R4.3 khóa blueprint khi `approved`. Nếu để mapping trong
blueprint (`covered_by`) thì mỗi lần sửa curriculum phải sửa blueprint approved → xung đột R4.3 + trùng
nguồn sự thật. Mapping thuộc về bên **editable** (curriculum). Blueprint chỉ **khai báo** mảng bắt buộc;
curriculum **khai báo phủ**. (Đánh đổi: cần CR mở rộng schema `curriculum` — xem CR-0012.)

### QĐ-2: Ép phủ CHỈ khi tồn tại blueprint `approved`

Đọc gộp R5.1 ("Mandatory_Area trong blueprint đã approved") + R5.2 + R5.4 ("chưa có blueprint HOẶC còn
draft → giữ hành vi cũ, không bắt buộc ánh xạ"): điều kiện kích hoạt ép phủ = **blueprint.md tồn tại VÀ
status == approved**. Draft blueprint = đang soạn, chưa phải chuẩn ràng buộc (R4.1) → không ép. Đây là cách
đọc nhất quán duy nhất giữa R3 (thuộc tính phủ tổng quát) và R5.4 (tương thích ngược).

### QĐ-3: Phủ là bất biến LIÊN TỤC (chạy trong mọi full-validate), không chỉ lúc dựng

`cmd_curriculum` đặt `teachable=True` ngay lúc dựng rồi để transaction-FULL validate abort nếu sai (đã đọc
`session.py`:771). Feature này KHÔNG thêm cổng riêng: chỉ cần `_check_blueprint_coverage` chạy trong
full-validate. Hệ quả đúng tinh thần "validator là chân lý": nếu approve blueprint SAU khi curriculum đã
teachable mà thiếu phủ → `validate --scope full` FAIL (E-BP-AREA-UNCOVERED). Không có trạng thái "teachable
nhưng thiếu phủ" tồn tại bền vững.

## Architecture

### Vị trí file (INV-16/17/18)

```
learning_vault/topics/<topic>/
  blueprint.md        # MỚI — Topic_Blueprint (front-matter máy-đọc). Dữ liệu học → trong vault (INV-18).
  curriculum.md       # SẴN CÓ — thêm field CurriculumPoint.area_refs (ánh xạ phủ). CR-0012.
  topic_state.md      # SẴN CÓ — KHÔNG đổi (blueprint không đụng index lesson).
  ...
```

- `blueprint.md` chỉ markdown/yaml text → INV-17 (không code) không kích; thêm `blueprint.md` vào
  `_SYSTEM_DATA_NAMES` để INV-18 chặn nó lọt vào `_system/`.
- Chỉ đường dẫn tương đối (`area_refs` là id nội-blueprint, không phải path; `source_refs` blueprint trỏ
  `reference/` như curriculum) → INV-16 giữ nguyên.

### Blueprint_Validator — phần mở rộng của validate.py (KHÔNG bộ máy thứ 2)

Thêm `_check_blueprint(topic_dir, vault_root, rep, ...)` + `_check_blueprint_coverage(...)`, wire vào cuối
`_validate_topic` NGAY SAU `_check_curriculum` (cùng mẫu artifact-tùy-chọn). Đăng ký `blueprint` vào
`_SCHEMA_MODELS`.

## Components and Interfaces

### Lệnh mới (năng lực — tên chốt trong CR-0011, KHÔNG đặt cứng ở đây)

Requirements KHÔNG chốt tên lệnh (R7.1). Đề xuất tên (chốt trong CR):
1. **Dựng blueprint** (đề xuất `blueprint`): sinh `blueprint.md` (status=draft) từ nguồn/reference —
   transaction-FULL. Đã tồn tại → từ chối (R2.4). Thiếu tham số/không rõ ý → hỏi lại, không đoán (R2.5).
2. **Sửa blueprint draft** (đề xuất `blueprint --edit`): thêm/xóa/sửa/sắp xếp Mandatory_Area khi status=draft
   — transaction-FULL (R4.1).
3. **Duyệt blueprint** (đề xuất `blueprint --approve`): draft→approved, chỉ khi Blueprint_Validator PASS
   (R4.2/R4.6) — transaction-FULL.
4. **Sửa blueprint approved có kiểm soát** (đề xuất `blueprint --amend --confirm`): sửa mảng khi approved
   NHƯNG bắt buộc cờ xác nhận tường minh (R4.3/R4.4) — transaction-FULL, rollback nếu validate FAIL.
5. **Kiểm blueprint** (gộp vào `/validate` như curriculum `--check`, DEC-063): read-only.

Ánh xạ phủ (`area_refs`) đặt qua **mở rộng lệnh curriculum sẵn có** (cp mang `area_refs`), không thêm lệnh
riêng — tránh ceremony (tiền lệ DEC-063/069 `--insert-at`).

## Data Models

### 1) `blueprint.md` (front-matter máy-đọc + body người-đọc)

```yaml
schema: blueprint
schema_version: 1
topic_id: <topic>
status: draft                 # {draft | approved} (R1.5, R4)
areas:
  - id: ma-001                # định danh ổn định, duy nhất trong blueprint (R1.2/R1.6)
    order: 1                  # thứ tự lộ trình 1..N, không trùng/không hở (R1.1)
    title: "Nền tảng Linux"   # tiêu đề không rỗng — >=1 ký tự non-space (R1.3)
    mandatory: true           # cờ bắt-buộc/tùy-chọn (R1.3)
    source_refs:              # truy vết nguồn dựng mảng (R2.2); rỗng nếu dựng từ nguồn ngoài
      - "reference/docker/roadmap-linux.md"
created: <date>
updated: <date>               # >= created (model), <= today (validator INV-05)
```

Model pydantic: `Blueprint` (strict, extra=forbid) + `MandatoryArea` (nested). Ràng buộc CẤU TRÚC ở model
(→ E-SCHEMA): `id` khớp `^ma-\S+$`; `order ≥ 1`; `status ∈ {draft,approved}`; `mandatory: bool`;
`updated ≥ created`. Ràng buộc NGỮ NGHĨA ở Blueprint_Validator (mã E-BP-* riêng — bảng dưới).

### 2) `CurriculumPoint` — thêm 1 field (CR-0012, tương thích ngược)

```yaml
# trong curriculum.md, mỗi point thêm:
    area_refs: []             # list[str] id Mandatory_Area mà point này phủ; mặc định [] (backward-compat)
```

Mặc định `[]` → curriculum cũ (không blueprint) đọc vẫn hợp lệ (R5.4). Model: `area_refs: list[str] = []`.

### Đăng ký schema (đồng nhất cơ chế hiện có — R6.5, DEC-008)

- `schemas/blueprint.schema.md` (khối `schema_fields` máy-đọc) + model `Blueprint` trong `models.py` +
  drift-guard `test_schemas_consistency.py` (`MODEL_BY_SCHEMA += 1`).
- Cập nhật `schemas/curriculum.schema.md` (thêm `area_refs` vào optional) — giữ drift-guard khớp.
- Thêm `blueprint` vào `_SCHEMA_MODELS`; thêm `blueprint.md` vào `_SYSTEM_DATA_NAMES` (INV-18).

## Error Handling — mã lỗi mới (RED-first, R6.1/R6.2)

Mỗi loại vi phạm đúng MỘT mã phân biệt, ổn định (R6.1). Mỗi mã có ≥1 test FAIL trước khi hiện thực (R6.2).

| Mã lỗi | Vi phạm | Requirement |
|---|---|---|
| `E-BP-DUP-ID` | hai Mandatory_Area trùng `id` | R1.6, R6.1 |
| `E-BP-EMPTY-TITLE` | `title` rỗng (chỉ khoảng trắng) | R1.3, R6.1 |
| `E-BP-ORDER` | `order` trùng hoặc hở (không hoán vị 1..N) | R1.1, R6.1 |
| `E-BP-AREA-UNCOVERED` | Mandatory_Area `mandatory:true` không được point nào phủ (blueprint approved) | R3.2, R3.3 |
| `E-BP-AREA-REF-BROKEN` | `area_refs` của point trỏ area không tồn tại trong blueprint | R3.6, R5 (INV-03) |
| `E-BP-POINT-OUTSIDE` | (blueprint approved) point không ánh xạ area nào | R5.2 |
| `E-BP-REF-BROKEN` | `source_refs` blueprint trỏ file `reference/` không tồn tại | R2.2 (song song E-CURR-REF-BROKEN) |

Ràng buộc SCHEMA/kiểu/status-ngoài-tập → `E-SCHEMA` sẵn có (model strict/Literal), KHÔNG tạo mã riêng —
tránh ceremony + trùng (tiền lệ DEC-058 bỏ E-CURR-SCHEMA/BADSTATUS). "Đủ tầm chuyên gia" KHÔNG có mã (Class
D, R3.7).

> **Lưu ý transaction-overlay (DEC-073):** blueprint + curriculum + area_refs đều nằm TRONG vault → không
> dính bug exam-overlay (sibling ngoài vault). `_check_blueprint*` resolve trong `topic_dir` (đã trong
> overlay). Không cần `real_vault_root`. Vẫn thêm test overlay khẳng định (đề phòng hồi quy).

## Correctness Properties (Class A, mỗi property có test tất định)

- **P1 — Định danh & thứ tự khung:** `area.id` duy nhất; `order` hoán vị 1..N. Vi phạm → `E-BP-DUP-ID`/
  `E-BP-ORDER`. (R1.1, R1.2, R1.6)
- **P2 — Tiêu đề không rỗng:** mỗi area `title` có ≥1 ký tự non-space. Vi phạm → `E-BP-EMPTY-TITLE`. (R1.3)
- **P3 — Phủ đủ khi approved:** blueprint approved → mọi area mandatory được ≥1 point phủ. Vi phạm →
  `E-BP-AREA-UNCOVERED`; curriculum không teachable, không sinh lesson. (R3.1–3.4)
- **P4 — Toàn vẹn tham chiếu ánh xạ:** mọi `area_refs[i]` trỏ area tồn tại. Vi phạm → `E-BP-AREA-REF-BROKEN`.
  (R3.5, R3.6, INV-03)
- **P5 — Không điểm-ngoài-khung khi approved:** blueprint approved → mọi point ánh xạ ≥1 area. Vi phạm →
  `E-BP-POINT-OUTSIDE`. (R5.1, R5.2)
- **P6 — Vòng đời approve có cổng:** draft→approved chỉ khi Blueprint_Validator PASS; approved → sửa chỉ qua
  bước có xác nhận; mọi đổi để lại vết transaction log. (R4.2, R4.3, R4.5, R4.6)
- **P7 — Tất định + portable:** cùng đầu vào → cùng tập mã lỗi + cùng phán quyết; không lệ đồng hồ/thứ tự
  file. (R6.3, R6.4)
- **P8 — Bảo toàn bất biến nền:** sau feature, vault PASS INV-16/17/18/25; blueprint không path tuyệt đối;
  thiếu schema/drift-guard → validate FAIL. (R7.3, R7.4, R7.5)
- **P9 — Tương thích ngược:** topic không blueprint / blueprint draft → hành vi curriculum-driven cũ giữ
  nguyên (không ép ánh xạ). (R5.4)

## Vòng đời approve (R4) — chi tiết cơ chế

- `status: draft` (khởi tạo R1.5): lệnh `--edit` sửa areas tự do, transaction-FULL.
- `--approve`: đọc blueprint, chạy `_check_blueprint` (KHÔNG cần phủ vì phủ là quan hệ với curriculum; approve
  chỉ kiểm cấu trúc khung nội tại — R4.2/R4.6). Nếu PASS → set `status=approved`, ghi transaction. Nếu FAIL →
  SessionError, giữ draft (R4.6).
- Khi approved: `--edit` thường bị TỪ CHỐI (R4.3). Chỉ `--amend --confirm` (cờ xác nhận tường minh) mới sửa
  được → transaction-FULL, re-validate, rollback nếu FAIL (R4.4).
- Mọi đổi status/nội dung ghi qua transaction → transaction log lưu vết (R4.5).

## Testing Strategy

1. **RED-first** mỗi mã E-BP-* (test đỏ trước khi code kiểm — R6.2).
2. Sau mỗi thay đổi: **full suite** + `validate --scope full` PASS trên vault ship.
3. **Tất định**: bơm `--at` cố định; monkeypatch os.walk order (tiền lệ DEC-032) khẳng định thứ tự lỗi ổn
   định (R6.4).
4. **Overlay test**: blueprint+curriculum+area_refs trong transaction-FULL không false-positive (đề phòng
   lớp DEC-073).
5. **E2E**: `blueprint(draft) → edit → approve → curriculum(area_refs phủ đủ) → validate PASS → next-lesson`;
   và ca âm: approve rồi tạo curriculum THIẾU phủ → validate FAIL E-BP-AREA-UNCOVERED + không teachable.
6. **Backward-compat**: vault có curriculum KHÔNG blueprint → PASS y như trước (P9); `test_shipped_vault_clean`
   vẫn xanh.
7. **Drift-guard**: `MODEL_BY_SCHEMA` +1; `validation_rules.md` error_codes +7 (coverage 2 chiều);
   `commands.md`/router đồng bộ lệnh mới.

## Kế hoạch change-request (thứ tự áp — §12, pending → owner duyệt → áp)

- **CR-0011** — schema `blueprint` mới (model `Blueprint`+`MandatoryArea` + `schemas/blueprint.schema.md` +
  drift-guard + `_SCHEMA_MODELS` + `_SYSTEM_DATA_NAMES`). Không bump VERSION (schema_version per-file=1,
  additive; tiền lệ CR-0007/DEV-006).
- **CR-0012** — mở rộng schema `curriculum`: thêm `CurriculumPoint.area_refs` (optional, default `[]`, tương
  thích ngược). Cập nhật `curriculum.schema.md` + drift-guard.
- **CR-0013** — lệnh mới vào registry `commands.md` + router (`blueprint` + các cờ `--edit/--approve/
  --amend`; curriculum nhận `area_refs`). Drift-guard registry↔CLI↔router.
- **CR-0014** — mở rộng spec gốc `PROMPT_LEARNING_SYSTEM.md` (§3.5 thêm Topic_Blueprint + Blueprint_Validator
  + 7 mã E-BP-* + vòng đời approve). Áp SAU khi code XANH (spec phản ánh cái kiểm-được — tiền lệ CR-0009).

Mỗi CR: `pending/` → owner "Duyệt" → áp + `changelog.md` + ghi DEC vào `decisions/`.

## Rủi ro & giảm thiểu

- **Mở rộng schema curriculum (`area_refs`) đụng feature đã hoàn tất:** rủi ro hồi quy. Giảm thiểu: field
  optional default `[]`; chạy TOÀN BỘ suite curriculum cũ sau khi thêm; RED-first ca mới.
- **Hiểu sai "phủ" khi draft:** rõ ràng hóa QĐ-2 (chỉ ép khi approved) + test P9 backward-compat.
- **Class D over-claim:** KHÔNG thêm mã cho "đủ tầm chuyên gia"; tài liệu nói thẳng (R3.7).
- **Blueprint approved bị sửa lén:** chỉ `--amend --confirm` sửa được; transaction log lưu vết (R4.5).
