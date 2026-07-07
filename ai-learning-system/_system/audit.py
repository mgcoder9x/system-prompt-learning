"""audit.py — Báo cáo CHỈ-ĐỌC 'folder này đã được làm gì' (dùng khi ai đó gửi bạn vault của họ).

Chạy (từ _system/, cần .venv):
    .venv\\Scripts\\python audit.py --vault ..\\learning_vault [--at 2026-07-02T17:00:00+07:00] [--json]

Gộp: (1) VERDICT toàn-vẹn = chạy validator FULL (PASS/FAIL + mã lỗi); (2) topics/lessons + status;
(3) tiến độ ôn (mastery_state + due_date) + số due; (4) open_gaps; (5) LỊCH SỬ hoạt động (đọc
transaction_log.md — lệnh nào đã ghi, khi nào). KHÔNG ghi gì, không transaction. Robust: vault hỏng →
BÁO CÁO (integrity FAIL + phần đọc-được), KHÔNG crash.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "validator"))

import validate as V   # noqa: E402
import session as S    # noqa: E402


def _safe(fn, default):
    try:
        return fn()
    except Exception as e:                       # audit KHÔNG được crash vì file hỏng
        return default if not callable(default) else default(e)


def _parse_activity(vault: Path) -> list[dict]:
    """Đọc transaction_log.md → list entry {tx, state, at, writes[], tombstones[]}. Vắng → []."""
    log = Path(vault) / "transaction_log.md"
    if not log.is_file():
        return []
    text = _safe(lambda: log.read_text(encoding="utf-8"), "")
    entries = []
    cur = None
    for line in text.splitlines():
        m = re.match(r"^## tx (\S+) — (\S+) @ (.*)$", line.strip())
        if m:
            cur = {"tx": m.group(1), "state": m.group(2), "at": m.group(3).strip(),
                   "writes": [], "tombstones": []}
            entries.append(cur)
        elif cur is not None:
            s = line.strip()
            mw = re.match(r"^- (write|delete): (\S+)", s)
            if mw:
                cur["writes"].append(f"{mw.group(1)}: {mw.group(2)}")
            elif s.startswith("- tombstone:"):
                cur["tombstones"].append(s[len("- tombstone:"):].strip())
    return entries


def _topics_report(vault: Path) -> list[dict]:
    """Duyệt topics/ → mỗi topic: lessons (id+status) + review_items (mastery/due) + open_gaps.
    Robust: file hỏng → đánh dấu 'unreadable', không crash."""
    out = []
    tdir = Path(vault) / "topics"
    if not tdir.is_dir():
        return out
    for td in sorted(p for p in tdir.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        topic = {"topic": td.name, "lessons": [], "unreadable": []}
        ldir = td / "lessons"
        if ldir.is_dir():
            for ld in sorted(p for p in ldir.iterdir() if p.is_dir()):
                lp = ld / "lesson_state.md"
                if not lp.is_file():
                    continue
                raw = _safe(lambda: S._load_raw(lp)[0], None)
                if not isinstance(raw, dict):
                    topic["unreadable"].append(f"{td.name}/{ld.name}/lesson_state.md")
                    continue
                items = [{"item_id": rv.get("id"),
                          "mastery_state": rv.get("mastery_state"),
                          "due_date": str((rv.get("card") or {}).get("due_date"))}
                         for rv in (raw.get("review_items") or []) if isinstance(rv, dict)]
                gaps = [{"gap_id": g.get("id"), "desc": g.get("desc")}
                        for g in (raw.get("open_gaps") or []) if isinstance(g, dict)]
                topic["lessons"].append({
                    "lesson_id": raw.get("lesson_id", f"{td.name}/{ld.name}"),
                    "status": raw.get("status"), "review_items": items, "open_gaps": gaps,
                })
        out.append(topic)
    return out


def audit(vault, system, now=None) -> dict:
    """Báo cáo CHỈ-ĐỌC (dict). now=None → đồng hồ thật (cho verdict INV-05/lịch); bơm để tất định."""
    vault, system = Path(vault), Path(system)
    now = now or datetime.now(timezone.utc)

    rep = V.Report()
    _safe(lambda: V.validate_full_semantic(system, vault, rep, now=now), None)
    integrity = {"pass": rep.ok(), "errors": list(rep.errors), "warnings": list(rep.warnings)}

    vs = _safe(lambda: S._load_raw(vault / "vault_state.md")[0], {})
    current = {"topic": vs.get("current_topic") if isinstance(vs, dict) else None,
               "lesson": vs.get("current_lesson") if isinstance(vs, dict) else None}

    topics = _topics_report(vault)
    gaps = _safe(lambda: S.cmd_gaps(vault, system), [])
    due = _safe(lambda: S.cmd_status(vault, system, now).get("due_today", None), None)
    activity = _parse_activity(vault)

    n_lessons = sum(len(t["lessons"]) for t in topics)
    n_items = sum(len(l["review_items"]) for t in topics for l in t["lessons"])
    return {
        "integrity": integrity,
        "current": current,
        "topics": topics,
        "open_gaps": gaps,
        "due_today": due,
        "activity": activity,
        "summary": {"n_topics": len(topics), "n_lessons": n_lessons,
                    "n_review_items": n_items, "n_open_gaps": len(gaps),
                    "n_transactions": len(activity)},
    }


def _print(rep: dict) -> None:
    I = rep["integrity"]
    print("=== AUDIT — folder này đã được làm gì ===\n")
    print(f"[TOÀN VẸN] validator FULL: {'PASS' if I['pass'] else 'FAIL'}"
          + ("" if I["pass"] else f"  ({len(I['errors'])} lỗi)"))
    for e in I["errors"]:
        print(f"    - {e.get('error_code')}: {e.get('file')} — {e.get('message')}")
    c = rep["current"]
    print(f"\n[HIỆN TẠI] topic={c['topic']}  lesson={c['lesson']}  due_hôm_nay={rep['due_today']}")
    s = rep["summary"]
    print(f"[TỔNG] topics={s['n_topics']} lessons={s['n_lessons']} review_items={s['n_review_items']} "
          f"open_gaps={s['n_open_gaps']} transactions={s['n_transactions']}")
    print("\n[TOPICS]")
    for t in rep["topics"]:
        print(f"  • {t['topic']}")
        for l in t["lessons"]:
            rv = ", ".join(f"{i['item_id']}:{i['mastery_state']}(due {i['due_date']})"
                           for i in l["review_items"]) or "—"
            print(f"      - {l['lesson_id']} [{l['status']}]  review: {rv}"
                  + (f"  gaps: {[g['gap_id'] for g in l['open_gaps']]}" if l["open_gaps"] else ""))
        for u in t.get("unreadable", []):
            print(f"      - !! KHÔNG ĐỌC ĐƯỢC: {u}")
    print("\n[LỊCH SỬ HOẠT ĐỘNG] (transaction_log.md)")
    if not rep["activity"]:
        print("  (chưa có giao dịch nào ghi log)")
    for a in rep["activity"]:
        print(f"  • tx {a['tx']} [{a['state']}] @ {a['at']}")
        for w in a["writes"]:
            print(f"      {w}")
        for tb in a["tombstones"]:
            print(f"      tombstone: {tb}")


def main(argv=None) -> int:
    import argparse, json
    ap = argparse.ArgumentParser(description="Audit CHỈ-ĐỌC một learning vault.")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--system", default=str(_HERE))
    ap.add_argument("--at", default=None, help="ISO-8601 aware (vd 2026-07-02T17:00:00+07:00) — audit tất định")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    now = None
    if args.at:
        try:
            now = datetime.fromisoformat(args.at)
            if now.tzinfo is None:
                raise ValueError("--at phải kèm offset (aware)")
        except ValueError as e:
            print(f"[E-ARG] --at không hợp lệ: {e}")
            return 2
    rep = audit(Path(args.vault), Path(args.system), now=now)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2, default=str))
    else:
        _print(rep)
    return 0 if rep["integrity"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
