"""P01.0 SPIKE — khảo sát API thật của fsrs 6.3.1 để chốt chiến lược determinism (A/B).
Chạy: .venv\\Scripts\\python.exe validator\\spike_fsrs.py
"""
from __future__ import annotations
import inspect
import json
from datetime import datetime, timezone, timedelta

import fsrs

print("=" * 70)
print("fsrs version:", getattr(fsrs, "__version__", "?"))
print("public names:", [n for n in dir(fsrs) if not n.startswith("_")])
print("=" * 70)

from fsrs import Scheduler, Card, Rating  # type: ignore

# Q: Scheduler signature + default parameters (số weights?)
sig = inspect.signature(Scheduler.__init__)
print("\n[Q3] Scheduler.__init__ params:")
for name, p in sig.parameters.items():
    print(f"   {name} = {p.default!r}")
sch = Scheduler()
params = getattr(sch, "parameters", None)
print("   default parameters len:", len(params) if params is not None else "n/a")
print("   default parameters:", params)

# Q4: Card mới — state, stability, difficulty khởi tạo?
print("\n[Q4] Card mới tạo:")
c = Card()
print("   attrs:", {k: v for k, v in vars(c).items()})
print("   state repr:", repr(c.state), "| type:", type(c.state).__name__)
print("   stability:", c.stability, "| difficulty:", c.difficulty)

# Q3(serialize): to_dict / from_dict ?
print("\n[Q3b] serialize:", [m for m in dir(c) if "dict" in m.lower() or "json" in m.lower()])

# Rating enum
print("\n[Rating] members:", {r.name: r.value for r in Rating})

# Q1: review_card trả về gì? due có sẵn không?
print("\n[Q1] review_card:")
print("   signature:", inspect.signature(sch.review_card))
now = datetime(2026, 6, 30, 13, 0, 0, tzinfo=timezone.utc)
new_card, review_log = sch.review_card(c, Rating.Good, now)
print("   returns type:", type(new_card).__name__, ",", type(review_log).__name__)
print("   new_card.due:", new_card.due, "| type:", type(new_card.due).__name__)
print("   new_card.stability:", new_card.stability)
print("   new_card.difficulty:", new_card.difficulty)
print("   new_card.state:", repr(new_card.state))
print("   new_card.step:", getattr(new_card, "step", "n/a"))
print("   review_log fields:", {k: v for k, v in vars(review_log).items()})

# Q2: có formula/hàm tính interval từ stability public không?
print("\n[Q2] Scheduler public methods:", [m for m in dir(sch) if not m.startswith("_")])
print("   Card public methods:", [m for m in dir(new_card) if not m.startswith("_")])

# Q5: review_datetime phải UTC-aware? thử naive
print("\n[Q5] thử naive datetime (không tz):")
try:
    sch.review_card(Card(), Rating.Good, datetime(2026, 6, 30, 13, 0, 0))
    print("   -> KHÔNG raise (chấp nhận naive)")
except Exception as e:
    print("   -> RAISE:", type(e).__name__, str(e)[:120])

print("\nthử local tz (+07:00):")
try:
    sch.review_card(Card(), Rating.Good, datetime(2026, 6, 30, 20, 0, 0, tzinfo=timezone(timedelta(hours=7))))
    print("   -> KHÔNG raise (chấp nhận aware non-UTC)")
except Exception as e:
    print("   -> RAISE:", type(e).__name__, str(e)[:120])

# DETERMINISM: cùng input → cùng due? (fuzzing default?)
print("\n[DET] enable_fuzzing default:", getattr(sch, "enable_fuzzing", "n/a"))
c1, _ = Scheduler(enable_fuzzing=False).review_card(Card(), Rating.Good, now)
c2, _ = Scheduler(enable_fuzzing=False).review_card(Card(), Rating.Good, now)
print("   two runs due equal:", c1.due == c2.due, "|", c1.due, c2.due)
print("   two runs stability equal:", c1.stability == c2.stability)

# serialize round-trip
if hasattr(new_card, "to_dict"):
    d = new_card.to_dict()
    print("\n[serialize] to_dict:", json.dumps(d, default=str)[:300])
    rt = Card.from_dict(d)
    print("   from_dict OK; due match:", rt.due == new_card.due)
