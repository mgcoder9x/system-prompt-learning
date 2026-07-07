"""P05 — File IO, discovery, ignore policy (spec mục 19, INV-16/20).

- Luôn đọc/ghi UTF-8 rõ ràng (Windows code page làm vỡ tiếng Việt).
- OCC/content hash dùng bytes thật.
- Bỏ qua _scratch/, .tx/, dotdir, và cloud-conflict artifacts (có warning), KHÔNG bỏ 'copy' trần.
"""
from __future__ import annotations

import re
from pathlib import Path

import hashlib

# INV-16 (E-PORT-ABSPATH): bắt đường dẫn TUYỆT ĐỐI theo MÁY (không portable).
# Ổ đĩa Windows = MỘT chữ cái đứng độc lập trước ':\' hoặc ':/' → negative lookbehind (?<![A-Za-z])
# để KHÔNG bắt oan scheme URL ('https://' có 's:/'); URL là portable, spec 5.3 cho phép ref là URL.
ABSPATH_RE = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]|/Users/|/home/")
_IGNORE_DIRS = {"_scratch", ".tx", ".cache", ".venv", "__pycache__", ".pytest_cache"}
# cloud conflict: cụ thể, KHÔNG bắt 'copy' trần
_CLOUD_PATTERNS = [
    re.compile(r"conflicted copy", re.I),
    re.compile(r"-conflict\b", re.I),
    re.compile(r"\(.*conflicted.*\)", re.I),
    re.compile(r"\(.*'s conflicted copy.*\)", re.I),
    re.compile(r"\(.*copy \d{4}-\d{2}-\d{2}.*\)", re.I),  # "(... copy 2026-06-30 ...)"
]


class EIoEncoding(ValueError):
    def __init__(self, message: str, path: str | None = None):
        super().__init__(message)
        self.path = path


def read_text(path: str | Path) -> str:
    """Đọc UTF-8, BỎ BOM đầu file nếu có (utf-8-sig): editor Windows (Notepad/PowerShell) hay thêm BOM
    (EF BB BF) → nếu giữ, split_frontmatter (startswith '---') báo oan 'thiếu front-matter' và lệch với
    _load_raw. utf-8-sig CHỈ bỏ BOM đầu; byte UTF-8 thật hỏng vẫn raise EIoEncoding (giữ E-IO-ENCODING)."""
    try:
        return Path(path).read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as e:
        raise EIoEncoding(f"E-IO-ENCODING: {path} không đọc được bằng UTF-8: {e}", path=str(path)) from e


def read_bytes(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def content_hash(path: str | Path) -> str | None:
    """sha256 của BYTES THẬT (spec 10.3: OCC/manifest dùng bytes, không mtime, không text-decoded).
    Trả None nếu file không tồn tại (dùng cho file mới: expected_read_hash=null)."""
    p = Path(path)
    if not p.is_file():
        return None
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Tách front-matter YAML ở ĐẦU file. File state phải bắt đầu bằng '---'."""
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)  # ['', fm, body]; body giữ nguyên '---' về sau
    if len(parts) < 3:
        return None, text
    return parts[1], parts[2]


def is_cloud_conflict(name: str) -> bool:
    return any(p.search(name) for p in _CLOUD_PATTERNS)


def scan_abspath(text: str) -> bool:
    return bool(ABSPATH_RE.search(text))


def discover_md(vault_root: str | Path) -> tuple[list[Path], list[str]]:
    """Trả (md_files, warnings). Bỏ vùng phi-thẩm-quyền + cloud conflict (có warning)."""
    root = Path(vault_root)
    md_files, warnings = [], []
    for p in sorted(root.rglob("*.md")):
        parts = set(p.relative_to(root).parts)
        if parts & _IGNORE_DIRS or any(part.startswith(".") for part in p.relative_to(root).parts[:-1]):
            continue
        if is_cloud_conflict(p.name):
            warnings.append(f"W-IGNORED-CLOUD-CONFLICT: bỏ qua {p.relative_to(root)}")
            continue
        md_files.append(p)
    return md_files, warnings
