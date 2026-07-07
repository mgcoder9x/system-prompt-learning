# Teaching Rules — Rubric 5 trục, cổng "đã hiểu", hợp đồng bằng chứng (spec 9)

Nguồn sự thật cho **đánh giá năng lực**. Đổi ngưỡng cổng PHẢI qua change request.
Khối máy-đọc-được `learned_gate` được test kiểm khớp `validate._GATE`.
Yêu cầu spec 9.5: mỗi trục ≥ 3 ví dụ neo (anchored examples) phủ mốc 1/2/3.

## 9.1. Năm trục

`concept` (hiểu khái niệm), `explain` (giải thích bằng lời thường), `apply` (áp dụng),
`critique` (phản biện / nhận lỗi sai), `teachback` (dạy lại).

## 9.2. Mô tả mức mỗi trục (0..3)

**concept**
```text
0: Không nêu được khái niệm là gì.
1: Nêu tên nhưng lẫn với khái niệm khác.
2: Nêu đúng bản chất, còn thiếu ranh giới/điều kiện.
3: Nêu đúng bản chất + phân biệt với khái niệm lân cận.
```
**explain**
```text
0: Không diễn đạt lại được, chỉ lặp từ khóa.
1: Diễn đạt được nhưng sai hoặc thiếu ý lõi.
2: Diễn đạt đúng ý lõi bằng lời thường, còn vài chỗ lúng túng.
3: Diễn đạt rõ ràng, có ví dụ riêng, không cần nhìn tài liệu.
```
**apply**
```text
0: Không áp dụng được vào tình huống nào.
1: Áp dụng sai hoặc chỉ chép lại ví dụ mẫu.
2: Áp dụng đúng vào tình huống quen thuộc.
3: Áp dụng đúng vào tình huống mới, tự chọn cách phù hợp.
```
**critique**
```text
0: Không nhận ra điểm sai/giới hạn nào.
1: Nhận ra có vấn đề nhưng chỉ sai chỗ được nhắc.
2: Tự chỉ ra một giới hạn/đánh đổi hợp lý.
3: Phản biện nhiều mặt, nêu điều kiện đúng/sai rõ ràng.
```
**teachback**
```text
0: Không dạy lại được.
1: Dạy lại rời rạc, người nghe khó theo.
2: Dạy lại mạch lạc ý chính cho người mới.
3: Dạy lại có cấu trúc + ví dụ + lường trước chỗ dễ nhầm.
```

## 9.3. Cổng "đã hiểu" (learned_gate)

`status: learned` chỉ khi mọi trục đạt ngưỡng VÀ mỗi trục đạt ngưỡng có ≥1 evidence verbatim (INV-07/22/22b).

### learned_gate (máy đọc)

```yaml
learned_gate:
  concept: 2
  explain: 2
  apply: 2
  critique: 1
  teachback: 2
```

## 9.5. Ví dụ neo (anchored examples) — giảm lệch chấm

### anchored_examples (máy đọc)

```yaml
anchored_examples:
  concept:
    - {answer: "Container là tiến trình bị cô lập, chia sẻ kernel host.", grade: 3, reason: "đúng bản chất + phân biệt VM"}
    - {answer: "Container là máy ảo nhẹ.", grade: 1, reason: "lẫn với VM"}
    - {answer: "Là cách đóng gói phần mềm để chạy giống nhau mọi nơi.", grade: 2, reason: "đúng ý, thiếu ranh giới kernel"}
  explain:
    - {answer: "Nó gói app + phụ thuộc nên máy nào cũng chạy như nhau.", grade: 2, reason: "đúng ý lõi, lời thường"}
    - {answer: "Dùng Docker cho tiện.", grade: 0, reason: "lặp từ khóa, không diễn đạt"}
    - {answer: "Như hộp cơm mang đi: đồ ăn + dụng cụ gói sẵn, nấu chung một bếp.", grade: 3, reason: "ví dụ riêng rõ ràng"}
  apply:
    - {answer: "Viết Dockerfile FROM python, COPY code, CMD chạy app.", grade: 2, reason: "áp dụng tình huống quen"}
    - {answer: "Copy nguyên ví dụ trong tài liệu, không đổi gì.", grade: 1, reason: "chép mẫu"}
    - {answer: "Đóng gói app cũ có phụ thuộc lạ bằng multi-stage build để giảm size.", grade: 3, reason: "tình huống mới, tự chọn cách"}
  critique:
    - {answer: "Container cách ly yếu hơn VM vì chung kernel — không hợp workload cần cô lập cứng.", grade: 3, reason: "phản biện nhiều mặt"}
    - {answer: "Container không có nhược điểm gì.", grade: 0, reason: "không nhận ra giới hạn"}
    - {answer: "Chắc là kém an toàn hơn tí.", grade: 2, reason: "chỉ ra một đánh đổi hợp lý"}
  teachback:
    - {answer: "Giải thích mạch lạc container cho người mới, kèm ví dụ hộp cơm.", grade: 2, reason: "mạch lạc ý chính"}
    - {answer: "Nói lộn xộn, nhảy giữa các ý.", grade: 1, reason: "rời rạc"}
    - {answer: "Dạy có cấu trúc + ví dụ + cảnh báo chỗ hay nhầm container vs VM.", grade: 3, reason: "cấu trúc + lường trước nhầm"}
```

## Hợp đồng bằng chứng (spec 9.3, INV-22/22b)

- Mỗi trục đạt ngưỡng phải có ≥1 `#### Evidence <ev-id>` trong `lesson.md`, `axis` khớp, `quote` không rỗng.
- `quote` phải là chuỗi con **verbatim** của transcript `#### Bạn trả lời <qid>` (sau `normalize_for_match`, spec 9.6).
- AI KHÔNG được bịa câu trả lời rồi nhét vào evidence (`E-ASSESS-FAKEQUOTE`).


## Lộ trình topic (CR-0005)

Khi mở một topic (`/learn`), AI lập **lộ trình các điểm cần học** trong `topic.md › ## Lộ trình`:
mỗi điểm một bullet `- [todo|doing|done] <điểm cần học>`; cập nhật trạng thái khi dạy tiến triển.
Đây là **guidance** (kế-hoạch-mềm), KHÔNG phải INV cứng — không bị validator ép khớp lessons.
KHÔNG đặt claim trong `## Lộ trình` (claim chỉ ở `## Claims`, INV-23). `## Knowledge Map` chỉ chứa
claim `status: confirmed` (INV-26). topic.md được `/learn` tạo sẵn khung hai section này.
