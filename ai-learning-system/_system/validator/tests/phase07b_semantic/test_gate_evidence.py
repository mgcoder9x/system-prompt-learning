"""P07b-1 tests — semantic: cổng 'đã hiểu' + evidence + verbatim (spec 9.3, INV-07/22/22b).

Cách ly từng mã lỗi (E-GATE-FAIL / E-ASSESS-NOEVIDENCE / E-ASSESS-FAKEQUOTE) + dung sai
verbatim (normalize_for_match) + end-to-end trên vault demo thật.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V   # noqa: E402
import models as M     # noqa: E402

SYSTEM = ROOT
VAULT_SRC = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"

FULL_SCORES = {"concept": 2, "explain": 2, "apply": 2, "critique": 1, "teachback": 2}


def _mk_lesson(status, scores):
    mastery = {ax: {"score": scores.get(ax, 0), "evidence": []} for ax in M.AXES}
    return M.LessonState(**{
        "schema": "lesson_state", "schema_version": 1,
        "lesson_id": "docker/lesson-001", "title": "t", "status": status,
        "created": date(2026, 6, 30), "updated": date(2026, 6, 30),
        "objective": "o", "mastery": mastery,
    })


def _ev(evid, axis, quote):
    return f"#### Evidence {evid}\n\n```yaml\naxis: {axis}\ntimestamp: 2026-06-30\nquote: \"{quote}\"\nai_assessment: \"ok\"\n```\n"


def _lesson_md(answer_text, *evs):
    head = f"# L\n\n## Sessions\n\n#### Bạn trả lời q1\n{answer_text}\n\n"
    return head + "\n".join(evs)


def _run(tmp_path, lesson, md_text):
    (tmp_path / "lesson.md").write_text(md_text, encoding="utf-8")
    rep = V.Report()
    V._check_gate_and_evidence(lesson, tmp_path, tmp_path, rep)
    return [e["error_code"] for e in rep.errors]


# ---- 1. learned hợp lệ: đủ điểm + đủ evidence + quote ⊆ transcript ----
def test_valid_learned_passes(tmp_path):
    transcript = ("Container chia sẻ kernel host. Nó khác máy ảo ở chỗ không ảo hoá phần cứng. "
                  "Dùng docker run để chạy. Nhược điểm là cách ly yếu hơn VM. "
                  "Giải thích lại: container gói tiến trình và phụ thuộc.")
    md = _lesson_md(
        transcript,
        _ev("ev-c", "concept", "Container chia sẻ kernel host."),
        _ev("ev-e", "explain", "Nó khác máy ảo ở chỗ không ảo hoá phần cứng."),
        _ev("ev-a", "apply", "Dùng docker run để chạy."),
        _ev("ev-cr", "critique", "Nhược điểm là cách ly yếu hơn VM."),
        _ev("ev-t", "teachback", "container gói tiến trình và phụ thuộc."),
    )
    codes = _run(tmp_path, _mk_lesson("learned", FULL_SCORES), md)
    assert codes == [], codes


# ---- 2. E-GATE-FAIL: learned nhưng concept dưới ngưỡng ----------------
def test_gate_fail_low_score(tmp_path):
    transcript = ("Nó khác máy ảo ở chỗ không ảo hoá phần cứng. Dùng docker run để chạy. "
                  "Nhược điểm là cách ly yếu hơn VM. container gói tiến trình và phụ thuộc.")
    md = _lesson_md(
        transcript,
        _ev("ev-e", "explain", "Nó khác máy ảo ở chỗ không ảo hoá phần cứng."),
        _ev("ev-a", "apply", "Dùng docker run để chạy."),
        _ev("ev-cr", "critique", "Nhược điểm là cách ly yếu hơn VM."),
        _ev("ev-t", "teachback", "container gói tiến trình và phụ thuộc."),
    )
    scores = dict(FULL_SCORES, concept=1)  # < ngưỡng 2
    codes = _run(tmp_path, _mk_lesson("learned", scores), md)
    assert "E-GATE-FAIL" in codes
    assert "E-ASSESS-NOEVIDENCE" not in codes  # concept<ngưỡng nên không đòi evidence concept


# ---- 3. E-ASSESS-NOEVIDENCE: trục đạt ngưỡng nhưng thiếu evidence ------
def test_no_evidence(tmp_path):
    md = _lesson_md("một câu trả lời bất kỳ")  # không có evidence block nào
    codes = _run(tmp_path, _mk_lesson("in_progress", {"concept": 2}), md)
    assert "E-ASSESS-NOEVIDENCE" in codes


# ---- 4. E-ASSESS-FAKEQUOTE: quote không có trong transcript -----------
def test_fake_quote(tmp_path):
    md = _lesson_md(
        "người học nói điều khác hẳn",
        _ev("ev-c", "concept", "Câu này AI tự bịa không có trong transcript."),
    )
    codes = _run(tmp_path, _mk_lesson("in_progress", {"concept": 2}), md)
    assert "E-ASSESS-FAKEQUOTE" in codes
    assert "E-ASSESS-NOEVIDENCE" not in codes  # evidence CÓ tồn tại (quote non-empty)


# ---- 5. dung sai verbatim: markdown + nháy cong + thừa space vẫn khớp -
def test_verbatim_tolerance(tmp_path):
    transcript = "Container chia sẻ kernel host nên nhẹ hơn máy ảo."
    # quote có **bold**, nháy cong, và khoảng trắng dư — normalize_for_match phải tha
    md = _lesson_md(
        transcript,
        _ev("ev-c", "concept", "Container chia sẻ **kernel**    host nên nhẹ hơn máy ảo."),
    )
    codes = _run(tmp_path, _mk_lesson("in_progress", {"concept": 2}), md)
    assert "E-ASSESS-FAKEQUOTE" not in codes, codes


# ---- 6. end-to-end: validate_full_semantic trên vault demo → PASS -----
def test_demo_vault_full_semantic_passes():
    rep = V.Report()
    V.validate_full_semantic(SYSTEM, VAULT_SRC, rep, now=datetime(2026, 7, 1, tzinfo=timezone.utc))
    assert rep.ok(), rep.errors
