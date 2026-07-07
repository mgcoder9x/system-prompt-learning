# Schema — `exam_results` (tính năng curriculum-driven-learning, CR-0007)

> **Chân lý schema nằm ở `validator/models.py` (class `ExamResults`, strict).** File này là bản mô tả
> người-đọc + hợp đồng máy-đọc `schema_fields`, được test `phase10/test_schemas_consistency.py` giữ
> khớp CHÍNH XÁC tập field của model.

Front-matter có cấu trúc của `topics/<topic>/exam_results.md` — **bản ghi chấm bài thực hành**. Bài nộp
(`Exam_Submission`) có thể là CODE nên nằm NGOÀI vault (`ai-learning-system/exam/...`); file này chỉ lưu
METADATA chấm (không chứa code) và trỏ tới bài nộp bằng đường dẫn tương đối (INV-16). `schema: exam_results`.
`strict=True, extra="forbid"`.

Ranh giới: `verdict` là nhận xét **Class D** (người/AI đánh giá — KHÔNG phải chân lý máy). Máy chỉ đảm bảo
(Class A) ref-integrity: mỗi bản ghi trỏ `submission`/`target` tồn tại (`E-EXAM-REF-BROKEN`, Task 8).

## Field (bám `models.py`)

| Field (khóa document) | Bắt buộc | Kiểu | Ý nghĩa |
|---|---|---|---|
| `schema` | ✓ | literal `"exam_results"` | định danh schema (alias của `schema_name`) |
| `schema_version` | ✓ | int | phiên bản schema (INV-19) |
| `topic_id` | ✓ | str | topic sở hữu |
| `results` | – | list[ExamResult] | `{submission_id: ex-*, ref, target, graded_at: date, verdict}` (mặc định `[]`) |

`ExamResult` (nested): `submission_id`(ex-*), `ref`(str, tương đối tới bài nộp ngoài vault), `target`(str,
topic hoặc curriculum_point), `graded_at`(date), `verdict`(str, nhận xét Class D).

### schema_fields (máy đọc)

```yaml
schema_fields:
  model: ExamResults
  document_key: exam_results
  required: [schema, schema_version, topic_id]
  optional: [results]
```
