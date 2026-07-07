"""P02 — Canonical hash & chuẩn hoá (spec mục 4, 9.6).

Ranh giới trách nhiệm (v2.6):
- normalize_yaml_object: chạy TRƯỚC pydantic; GIỮ type (date vẫn date). Không stringify.
- canonical_hash: stringify date→"YYYY-MM-DD" CHỈ ngay trước dump JSON (qua _to_jsonable). Cấm float thô.
- normalize_for_match: chuẩn hoá HÌNH THỨC cho INV-22b; KHÔNG lowercase/bỏ dấu.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import date, datetime

from markdown_it import MarkdownIt

_MD = MarkdownIt("commonmark")  # cần rule emphasis/code để strip delimiter đúng


# ---- canonical hash -----------------------------------------------------
class ECanonicalFloat(TypeError):
    """Miền băm không được chứa float thô (spec mục 4)."""


def _to_jsonable(obj):
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        raise ECanonicalFloat(f"float thô trong miền băm: {obj!r} — phải stringify cố định trước")
    if isinstance(obj, datetime):
        return obj.astimezone().strftime("%Y-%m-%dT%H:%M:%SZ") if obj.tzinfo else obj.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, date):
        return obj.isoformat()  # "YYYY-MM-DD"
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def canonical_json(data) -> str:
    return json.dumps(_to_jsonable(data), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(data) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


# ---- normalize YAML object (front-matter + fenced yaml) ----------------
def normalize_yaml_object(raw: dict, str_fields: set[str] | None = None) -> dict:
    """Hoà giải implicit typing của YAML về đúng type schema, KHÔNG lossy-coerce.

    str_fields: các key mà schema muốn STRING (vd 'due_at_utc', 'ref') — nếu YAML lỡ
    ép thành bool/int/date thì đưa về str để pydantic strict không vấp oan; nhưng
    KHÔNG tự ép "2"->2 hay ngược lại cho field số.
    """
    str_fields = str_fields or set()

    def norm(k, v):
        if k in str_fields and isinstance(v, (bool, int, float, date, datetime)):
            # YAML implicit-typed nhưng schema muốn str → stringify hình thức
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, date):
                return v.isoformat()
            return str(v)
        if isinstance(v, dict):
            return {kk: norm(kk, vv) for kk, vv in v.items()}
        if isinstance(v, list):
            return [norm(k, vv) for vv in v]
        return v

    return {k: norm(k, v) for k, v in raw.items()}


# ---- normalize for match (INV-22b, spec 9.6) ---------------------------
_QUOTE_MAP = {
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',  # “ ” „ ‟
    "\u2018": "'", "\u2019": "'",                                    # ‘ ’
    "\u2013": "-", "\u2014": "-",                                    # – —
}


def _strip_md_inline(s: str) -> str:
    """Bỏ delimiter định dạng inline (bold/italic/code-span) nhưng GIỮ text.
    Dùng AST inline token thay vì regex, để không nuốt _ trong __init__, C++, a_b."""
    tokens = _MD.parseInline(s)
    out = []

    def walk(children):
        for t in children:
            if t.type in ("text", "code_inline"):
                out.append(t.content)
            elif t.type == "softbreak" or t.type == "hardbreak":
                out.append(" ")
            elif getattr(t, "children", None):
                walk(t.children)
            # các token *_open/*_close (em, strong, s) → bỏ delimiter, không thêm gì
    for tok in tokens:
        if getattr(tok, "children", None):
            walk(tok.children)
        elif tok.type in ("text", "code_inline"):
            out.append(tok.content)
    return "".join(out)


def normalize_for_match(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = "".join(_QUOTE_MAP.get(ch, ch) for ch in s)
    s = _strip_md_inline(s)
    s = " ".join(s.split())  # gộp whitespace → 1 space, trim
    return s
