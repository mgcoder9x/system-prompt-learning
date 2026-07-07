# P05 — File IO, Discovery & Ignore Policy

**Mục tiêu:** đọc/ghi an toàn UTF-8, phát hiện file đúng, bỏ qua vùng phi-thẩm-quyền + rác cloud-sync — không để I/O phá tái lập/tiếng Việt.
**Phụ thuộc:** P00.
**Giai đoạn MVP:** GĐ1.

## Xây gì

`_system/validator/io.py`:

- `read_text(path)->str` — luôn `encoding="utf-8"`; decode fail → raise `EIoEncoding` (spec 19, KHÔNG dùng `open()` mặc định vì code page Windows).
- `read_bytes(path)->bytes` — cho OCC/content-hash (spec 10.3, dùng bytes thật).
- `split_frontmatter(text)->(fm:str|None, body:str)` — tách `---` đầu file, `split('---', 2)`; file state phải mở đầu `---`.
- `discover(vault_root)->[paths]` — spec 19 ignore policy:
  bỏ dotdir/dotfile trừ whitelist, bỏ `_scratch/`, `.tx/`, `_system/.cache/`;
  bỏ cloud conflict artifacts theo basename case-insensitive: `*conflict*`, `*conflicted copy*`, `*(*copy*)*`, `*PC-conflicted copy*`.
  **KHÔNG** bỏ path chỉ vì chứa chuỗi `copy` trần (giữ `copywriting`). File bị bỏ vì cloud → thêm `W-IGNORED-CLOUD-CONFLICT`.
- `scan_abspath(text)->bool` — dò `C:\`, `/Users/`, `/home/` (INV-16).

## INV/mục spec liên quan

19 (discovery/encoding/ignore), INV-16 (abspath), INV-20 (bỏ `_scratch`/`.tx`), `E-IO-ENCODING`, `W-IGNORED-CLOUD-CONFLICT`.

## Cách test (`_system/validator/tests/phase05_io/`)

```text
[ ] File tiếng Việt (có đ, dấu) round-trip UTF-8 không vỡ.
[ ] File lưu bằng cp1252/latin-1 → read_text raise EIoEncoding.
[ ] Discovery bỏ: _scratch/x.md, .tx/..., "topic (conflicted copy).md" → có warning W-IGNORED-CLOUD-CONFLICT.
[ ] Discovery GIỮ: topics/copywriting/topic.md (không bị bỏ nhầm vì chữ "copy").
[ ] scan_abspath bắt "d:\\OneDrive\\..." trong 1 file vault → INV-16 fail.
[ ] split_frontmatter: body chứa "---" (thematic break) không bị cắt sai (split tối đa 2 lần).
```

## Cạm bẫy

- Vault hay nằm trong OneDrive/GDrive → file conflict là chuyện thật; ignore phải chính xác, warning phải hiện để không âm thầm bỏ dữ liệu.
- OCC hash dùng **bytes**, không hash text đã decode (spec 10.3) — để độc lập newline/encoding.
