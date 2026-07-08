# CR-0015 — /curriculum --set-area-refs: retrofit area_refs cho Curriculum_Point ĐÃ CÓ

```yaml
id: cr-0015
title: "Thêm chế độ cờ /curriculum --set-area-refs <cp-id> --area-refs <json> để GẮN/SỬA area_refs cho điểm học đã tồn tại (mở luồng curriculum-first → áp khung về sau)"
status: approved
date_opened: 2026-07-08
date_decided: 2026-07-08
related: [NOTE-039 (giới hạn workflow), TRD-008 (quyết định B), DEC-074/075 (blueprint), CR-0012 (area_refs schema), CR-0010/DEC-069 (tiền lệ chế độ cờ --insert-at)]
recommendation: "Owner đã chọn phương án B (TRD-008). Áp SAU khi code+test XANH (spec phản ánh cái kiểm-được — tiền lệ CR-0009/0014)."
```

## 1. Ghi yêu cầu (§12 bước 1)

Phát hiện NOTE-039: nếu một topic đã có `curriculum.md` teachable KHÔNG mang `area_refs`, thì về sau KHÔNG
áp được một `blueprint.md` approved lên nó (E-BP-POINT-OUTSIDE + E-BP-AREA-UNCOVERED) VÀ không có lệnh nào
gắn `area_refs` cho điểm học đã có (`cmd_curriculum` từ chối khi curriculum tồn tại; `cmd_curriculum_insert`
chỉ THÊM điểm mới). Chỉ đi được luồng blueprint-first. Owner (TRD-008) chọn **phương án B**: bổ sung năng
lực retrofit để đi được cả luồng curriculum-first → áp-khung-về-sau.

## 2. Phân tích (§12 bước 2) — grounded trên code THẬT (đã đọc phiên này)

- **Bề mặt lệnh:** theo tiền lệ DEC-069 (`--insert-at`), KHÔNG thêm tên lệnh mới (giữ `CLI_COMMANDS` bất
  biến → 3 drift-guard registry/router/huong_dan KHÔNG đỏ). Thêm CỜ vào subcommand `curriculum` đã có.
- **Cổng phủ là teachable-gate (DEC-075):** khi blueprint còn `draft`, coverage (AREA-UNCOVERED/POINT-OUTSIDE)
  KHÔNG bị ép → cho phép retrofit TỪNG điểm một dưới blueprint draft, mỗi bước transaction-FULL vẫn PASS
  (chỉ E-CURR-* + E-BP structural/ref áp). Sau khi mọi điểm đã gắn đủ → `/blueprint --approve` → coverage
  bật, phủ đủ → approved. Đây là luồng đúng, KHÔNG brick vault.
- **Toàn vẹn tham chiếu:** `area_refs[i]` phải trỏ Mandatory_Area tồn tại → E-BP-AREA-REF-BROKEN đã ép sẵn
  (áp cả draft). Nên retrofit gán id sai vẫn bị transaction ABORT (an toàn).
- **Robustness:** dùng `_load_curriculum_validated` (DEC-071) → curriculum.md sửa-tay-hỏng ra E-SCHEMA sạch,
  KHÔNG crash.
- **KHÔNG đổi schema:** `CurriculumPoint.area_refs` đã có từ CR-0012. Chỉ thêm LỆNH ghi vào field sẵn có.

## 3. Đề xuất thiết kế (§12 bước 3) — VALID trước khi code

### 3.1. Bề mặt lệnh (parser — trong khối `elif name == "curriculum"`)
```
sp.add_argument("--set-area-refs", dest="set_area_refs", default=None,
                help="(RETROFIT CR-0015) cp-id của điểm cần gắn/sửa area_refs")
sp.add_argument("--area-refs", dest="area_refs", default=None,
                help='(RETROFIT CR-0015) JSON list id Mandatory_Area, vd ["ma-001","ma-002"]')
```

### 3.2. Dispatch (khối `elif args.command == "curriculum"`) — nhánh ĐẦU
```
if args.set_area_refs is not None:                 # CR-0015 retrofit
    if args.area_refs is None:
        raise SessionError("chế độ --set-area-refs cần --area-refs (JSON list id mảng)")
    committed, rep = cmd_curriculum_set_area_refs(Path(args.vault), Path(args.system),
                                                  args.topic, args.set_area_refs, args.area_refs, at)
elif args.insert_at is not None:                   # CR-0010 chèn
    ...
else:                                              # DỰNG mới
    ...
```

### 3.3. Backend `cmd_curriculum_set_area_refs(vault, system, topic_id, point_id, area_refs_json, at)`
1. `_recover_first(vault)`; validate `topic_id` (không rỗng, không '/').
2. `cpath = topics/<topic>/curriculum.md`; thiếu → `SessionError` ("chưa có curriculum — dùng /curriculum dựng trước").
3. Parse `area_refs_json` → PHẢI là **list các str** (sai → `SessionError`). List RỖNG hợp lệ (cho phép xoá ánh xạ).
4. `cur_raw, cur_body = _load_curriculum_validated(cpath)` (E-SCHEMA sạch nếu hỏng — DEC-071).
5. Tìm `pt` trong `cur_raw["points"]` có `id == point_id`; không thấy → `SessionError` ("point <id> không tồn tại"), KHÔNG ghi bộ phận.
6. `pt["area_refs"] = list(parsed)` — **ngữ nghĩa REPLACE** (đặt cả danh sách, không append: tất định, idempotent, cho phép sửa/xoá).
7. `cur_raw["updated"] = today` (theo utc_offset).
8. `writes = [TX.Write(<curriculum rel>, _dump_state(cur_raw, cur_body), expected_read_hash=content_hash(cpath))]`.
9. `return _run_tx(vault, system, writes, now=at)` — **transaction-FULL**: validator gate E-CURR-* + E-BP-*
   (nếu blueprint approved+teachable → coverage re-check; E-BP-AREA-REF-BROKEN áp cả draft) trước commit;
   sai → rollback, curriculum KHÔNG đổi.

### 3.4. Vì sao FULL (không LIGHT)
`area_refs` tác động E-BP-AREA-REF-BROKEN + coverage — các kiểm này nằm trong `_check_blueprint` (gọi trong
`_validate_topic`, thuộc full-validate). LIGHT sẽ KHÔNG gate được → phải FULL (đồng nhất cmd_curriculum_insert).

### 3.5. Vì sao REPLACE (không APPEND)
REPLACE cho phép: (a) gắn mới, (b) sửa sai, (c) xoá (list rỗng). APPEND không xoá được + dễ sinh trùng. Tất
định + khớp cách `cmd_curriculum` nhận area_refs nguyên khối.

## 4. Rủi ro (§12 bước 4)

- **Thấp.** Không đổi schema, không thêm tên lệnh, không mã lỗi mới. Chỉ thêm 1 backend + 2 cờ + dispatch.
- **Edge (khai báo trung thực):** nếu blueprint ĐÃ approved + curriculum teachable + chưa phủ (CHỈ tới được
  bằng sửa-tay file, vì approve qua lệnh đã đòi phủ đủ) → validate FULL đang FAIL → mọi transaction (kể cả
  set-area-refs) ABORT tới khi phủ đủ. Cách xử lý: retrofit dưới blueprint DRAFT (luồng chuẩn); trạng thái
  sửa-tay-hỏng thì đưa blueprint về draft trước rồi retrofit. Ghi rõ trong DEC + HUONG_DAN.
- **Backward-compat:** tuyệt đối (chỉ thêm nhánh cờ mới; mọi luồng /curriculum cũ không đổi).

## 5. Kịch bản test (§12 — RED-first, kỳ vọng FAIL trước khi hiện thực)

File mới `validator/tests/phase10/test_session_curriculum_setarearefs.py`:
1. `test_set_area_refs_updates_point` — set cp-001 `["ma-001"]` → committed; cp-001.area_refs==["ma-001"]; điểm khác không đổi.
2. `test_set_area_refs_replace_not_append` — cp có `["ma-001"]` → set `["ma-002"]` → ==`["ma-002"]` (thay, không nối).
3. `test_set_area_refs_empty_clears` — set `[]` → area_refs==[] (xoá ánh xạ, hợp lệ).
4. `test_set_area_refs_unknown_point` — cp-999 → `SessionError`; curriculum KHÔNG đổi (so content_hash).
5. `test_set_area_refs_bad_json` — không phải list / phần tử non-str → `SessionError`.
6. `test_set_area_refs_no_curriculum` — topic chưa có curriculum.md → `SessionError`.
7. `test_set_area_refs_corrupt_curriculum` — curriculum.md sửa-tay-hỏng (points sai kiểu) → E-SCHEMA sạch, KHÔNG crash (DEC-071 class).

File mới `validator/tests/phase12/test_e2e_retrofit_blueprint.py` (test CHỨNG MINH NOTE-039 được giải):
8. `test_retrofit_curriculum_then_approve` — dựng curriculum teachable 2 điểm KHÔNG area_refs + blueprint DRAFT 2 mandatory area → (approve lúc này sẽ FAIL vì chưa phủ) → 2× set-area-refs phủ đủ → `/blueprint --approve` COMMITTED + validate --scope full PASS + next-lesson chạy. Chứng minh luồng curriculum-first→áp-khung đi được.

Teeth: mỗi test kỳ-vọng-lỗi sẽ FAIL nếu backend chưa tồn tại (AttributeError) → RED trước, GREEN sau khi hiện thực.

## 6. Tài liệu sẽ cập nhật (áp SAU khi code XANH)

commands.md (annotate chế độ /curriculum --set-area-refs) + HUONG_DAN.md (luồng retrofit) + spec §3.6/§11A
(một dòng --set-area-refs, v2.8 — KHÔNG bump vì thuần thêm lệnh) + changelog CR-0015 + DEC-076 (hiện thực) +
đóng TRD-008 (chọn B, đã làm) + NOTE-039 status→resolved. `_system/VERSION` GIỮ =1.

## 7. Quyết định (§12 bước 6–7)

`pending` — chờ owner **DUYỆT THIẾT KẾ**. Khi duyệt: move approved + RED-first theo §5 + verify + commit +
áp tài liệu §6.
