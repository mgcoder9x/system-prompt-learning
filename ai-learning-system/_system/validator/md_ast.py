"""P04a — Markdown AST core (spec mục 19, 5.5, 14A).

Dò cấu trúc thân Markdown bằng AST markdown-it-py (KHÔNG regex trên prose).
Quy tắc "fence yaml đầu tiên trước heading kế cùng/cao cấp" (spec 19) để chịu prose chen giữa.
Heading nằm trong fenced code block KHÔNG bị nhận là heading thật (markdown-it lo việc này).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import yaml
from markdown_it import MarkdownIt

_MD = MarkdownIt("commonmark")

_RE_QUESTION = re.compile(r"^Question\s+(\S+)$")
_RE_EVIDENCE = re.compile(r"^Evidence\s+(ev-\S+)$")
_EVIDENCE_FIELDS = {"axis", "timestamp", "quote", "ai_assessment"}


@dataclass
class Heading:
    level: int
    text: str
    idx: int  # vị trí token heading_open


def parse(md: str):
    return _MD.parse(md)


def _hlevel(tok) -> int:
    return int(tok.tag[1:])  # 'h4' -> 4


def find_headings(tokens) -> list[Heading]:
    out = []
    for i, t in enumerate(tokens):
        if t.type == "heading_open":
            text = tokens[i + 1].content.strip()
            out.append(Heading(_hlevel(t), text, i))
    return out


def _section_bounds(tokens, headings: list[Heading], h: Heading) -> int:
    """Trả token index kết thúc section của heading h = heading kế cùng/cao cấp; hết file thì len(tokens)."""
    for hh in headings:
        if hh.idx > h.idx and hh.level <= h.level:
            return hh.idx
    return len(tokens)


def first_yaml_fence(tokens, start: int, end: int):
    """Fence info=yaml ĐẦU TIÊN trong (start, end); parse safe_load. None nếu không có."""
    for i in range(start + 1, end):
        t = tokens[i]
        if t.type == "fence" and (t.info or "").strip().lower() in ("yaml", "yml"):
            return yaml.safe_load(t.content)
    return None


def extract_questions(md: str) -> tuple[list[str], list[str]]:
    """Trả (qids, errors). qid từ heading '#### Question <qid>'. Bắt trùng qid."""
    headings = find_headings(parse(md))
    qids, errors, seen = [], [], set()
    for h in headings:
        m = _RE_QUESTION.match(h.text)
        if not m:
            continue
        qid = m.group(1)
        if qid in seen:
            errors.append(f"E-DUP-QID: trùng Question '{qid}'")
        seen.add(qid)
        qids.append(qid)
    return qids, errors


def check_evidence_block_syntax(md: str) -> list[str]:
    """LIGHT: kiểm cú pháp evidence block. Trả list lỗi (rỗng = OK)."""
    tokens = parse(md)
    headings = find_headings(tokens)
    errors, seen = [], set()
    for h in headings:
        m = _RE_EVIDENCE.match(h.text)
        if not m:
            continue
        evid = m.group(1)
        if h.level != 4:
            errors.append(f"E-EVIDENCE-LEVEL: '{h.text}' phải là heading cấp 4 (####)")
        if evid in seen:
            errors.append(f"E-DUP-EVIDENCE: trùng evidence id '{evid}'")
        seen.add(evid)
        end = _section_bounds(tokens, headings, h)
        data = first_yaml_fence(tokens, h.idx, end)
        if data is None:
            errors.append(f"E-EVIDENCE-NOYAML: '{evid}' thiếu fenced ```yaml``` liền sau")
            continue
        missing = _EVIDENCE_FIELDS - set(data)
        if missing:
            errors.append(f"E-EVIDENCE-FIELD: '{evid}' thiếu field {sorted(missing)}")
    return errors


def extract_yaml_under_heading(md: str, heading_text: str, level: int | None = None):
    """Generic: yaml fence đầu tiên dưới heading khớp text (dùng cho ## Claims — P04b)."""
    tokens = parse(md)
    headings = find_headings(tokens)
    for h in headings:
        if h.text == heading_text and (level is None or h.level == level):
            end = _section_bounds(tokens, headings, h)
            return first_yaml_fence(tokens, h.idx, end)
    return None


def has_heading(md: str, text: str) -> bool:
    return any(h.text == text for h in find_headings(parse(md)))


# ========================================================================
# P04b — SEMANTIC (claims / evidence / answer-block) — GĐ2
# Tầng TRÍCH thuần: không áp luật lớp, không normalize (dành cho P07b).
# ========================================================================
_RE_ANSWER = re.compile(r"^Bạn trả lời\s+(\S+)$")


def extract_claims(md: str) -> list[dict]:
    """Mọi claim dưới '## Claims' (spec 5.5): fenced ```yaml``` có key 'claims:'.
    Trả list dict THÔ (P07b áp luật lớp INV-12/13/14/15). Không section / không yaml /
    thiếu key 'claims' / claims không phải list → []."""
    data = extract_yaml_under_heading(md, "Claims", level=2)
    if not isinstance(data, dict):
        return []
    claims = data.get("claims")
    return [c for c in claims if isinstance(c, dict)] if isinstance(claims, list) else []


def extract_evidence(md: str) -> list[dict]:
    """Mọi '#### Evidence <ev-id>' + fenced ```yaml``` liền sau (spec 5.5).
    Trả list dict kèm 'id' (+ axis/timestamp/quote/ai_assessment nếu có)."""
    tokens = parse(md)
    headings = find_headings(tokens)
    out = []
    for h in headings:
        m = _RE_EVIDENCE.match(h.text)
        if not m or h.level != 4:
            continue
        end = _section_bounds(tokens, headings, h)
        data = first_yaml_fence(tokens, h.idx, end)
        ev = {"id": m.group(1)}
        if isinstance(data, dict):
            ev.update(data)
        out.append(ev)
    return out


def _section_text(md_lines: list[str], tokens, headings: list[Heading], h: Heading) -> str:
    """Text THÔ (verbatim nguồn) giữa heading h và heading kế cùng/cao cấp, dùng token.map."""
    end_idx = _section_bounds(tokens, headings, h)
    hmap = tokens[h.idx].map
    start_line = hmap[1] if hmap else 0
    if end_idx < len(tokens) and tokens[end_idx].map:
        end_line = tokens[end_idx].map[0]
    else:
        end_line = len(md_lines)
    return "".join(md_lines[start_line:end_line])


def extract_answer_blocks(md: str) -> dict:
    """Map qid → text THÔ dưới '#### Bạn trả lời <qid>' (transcript verbatim cho INV-22b).
    Block rỗng → '' (không crash). P07b tự normalize_for_match cả quote lẫn transcript (spec 9.6)."""
    tokens = parse(md)
    headings = find_headings(tokens)
    md_lines = md.splitlines(keepends=True)
    out = {}
    for h in headings:
        m = _RE_ANSWER.match(h.text)
        if not m or h.level != 4:
            continue
        out[m.group(1)] = _section_text(md_lines, tokens, headings, h)
    return out


def count_draft_claims(md_texts) -> int:
    """Đếm claim status='draft' trong các file (topic.md + lesson_notes.md của topic).
    Nuôi view has_draft_knowledge (INV-26). Chỉ đếm trong vùng '## Claims'."""
    n = 0
    for md in md_texts:
        for c in extract_claims(md):
            if c.get("status") == "draft":
                n += 1
    return n


def find_claims_fences(md: str) -> list[tuple[str, int]]:
    """Cho MỖI fenced ```yaml``` có key 'claims:', trả (heading_chi_phối_text, level).
    heading chi phối = heading gần nhất phía TRƯỚC fence; ('', 0) nếu không có heading trước nó.
    Dùng cho INV-23 (phát hiện claim đặt ngoài '## Claims')."""
    tokens = parse(md)
    headings = find_headings(tokens)
    out = []
    for i, t in enumerate(tokens):
        if t.type != "fence" or (t.info or "").strip().lower() not in ("yaml", "yml"):
            continue
        try:
            data = yaml.safe_load(t.content)
        except yaml.YAMLError:
            continue
        if not (isinstance(data, dict) and "claims" in data):
            continue
        gov = None
        for h in headings:
            if h.idx < i:
                gov = h
            else:
                break
        out.append((gov.text, gov.level) if gov else ("", 0))
    return out


def extract_section_text(md: str, heading_text: str, level: int | None = None) -> str | None:
    """Text thô dưới heading khớp (đến heading kế cùng/cao cấp). None nếu không thấy heading."""
    tokens = parse(md)
    headings = find_headings(tokens)
    md_lines = md.splitlines(keepends=True)
    for h in headings:
        if h.text == heading_text and (level is None or h.level == level):
            return _section_text(md_lines, tokens, headings, h)
    return None
