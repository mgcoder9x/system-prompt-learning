# P00 — Bootstrap & Khóa Môi Trường Tin Cậy

**Mục tiêu:** dựng môi trường tái lập được (lock exact), pin FSRS, để mọi phase sau chạy trên nền xác định.
**Phụ thuộc:** không.
**Giai đoạn MVP:** GĐ1.

## Xây gì (deliverables)

- `_system/pyproject.toml` — khai dependency với range tương thích (spec 16.0A):
  `fsrs==6.3.1`, `pydantic>=2.13,<3`, `PyYAML>=6,<7`, `markdown-it-py>=4,<5`; dev: `pytest`.
- `_system/uv.lock` — sinh bằng `uv lock` (có hash toàn bộ direct + transitive).
- `_system/requirements.txt` — `uv export --format requirements-txt --generate-hashes` (fallback pip).
- `_system/fsrs_config.yaml` — spec 8.3: `fsrs_package_version: "6.3.1"`, **21 weights ghi cứng**,
  `desired_retention`, `learning_steps`, `relearning_steps`, `maximum_interval`, `enable_fuzzing: false`,
  `MASTERED_STABILITY`, `serialization: {round_decimals: 4}`, `fsrs_config_version: 1`.
- `_system/repo_lab/repo_evaluations/{fsrs,pydantic,pyyaml,markdown-it-py,pytest,uv}.md` theo template spec 16.4
  (bắt buộc `uv.md` có `uv_version`).
- `_system/validator/runtime_report.py` — in `python_version`, `uv_version`, exact version 4 package (spec 16.0A).

## INV/mục spec liên quan

16.0, **16.0A** (lock exact, `uv sync --frozen`), 16.4 (repo evaluation), 8.3 (fsrs_config), 20.1–20.2.

## Cách test (Definition of Done)

```text
[ ] uv sync --frozen  → thành công, không tự resolve lại.
[ ] pip install --require-hashes -r requirements.txt trên máy sạch → cùng version.
[ ] pytest phase00: smoke import 4 package; assert fsrs.__version__ khởi đúng 6.3.1.
[ ] Đọc fsrs_config.yaml: đúng 21 weights, enable_fuzzing=False, có fsrs_config_version.
[ ] runtime_report.py in đủ python/uv/package versions.
[ ] Mọi repo_evaluations/*.md tồn tại, có license + exact version + rollback; uv.md có uv_version.
[ ] Nếu có `_system/repo_lab/reference_repos/*` (repo clone tham khảo): MỖI repo phải có evaluation file với
    `role: reference_only`, **full commit SHA** (`reference_commit`), `verified_at`, `refresh_policy: "manual only via change request"` (spec 16.2/16.4). Thiếu → chưa được coi là đã duyệt.
```

## Cạm bẫy

- KHÔNG chạy `uv add`/`uv sync` (thiếu `--frozen`) trong luồng chạy bình thường — chỉ ở bước bootstrap/change request.
- Weights FSRS-6 = **21 số** (không phải 19 của v5). Copy đúng bộ của version pin.
- Ghi `fsrs==6.3.1` exact, không range, để replay quá khứ không lệch (spec 8.3, mỗi version bất biến).
