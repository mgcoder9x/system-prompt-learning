"""P12 — Nghiệm thu HANDOFF KHÔNG-TRẠNG-THÁI (cross-session) TẤT ĐỊNH (spec 20.12–13, §11B/11B.2).

Lời hứa cốt lõi: trạng thái 'tự mô tả' → một phiên AI khác (máy/context khác) tiếp quản CHỈ từ file,
KHÔNG hỏi lại từ đầu. Đây là bản AUTO-TEST được của mục P12 DoD 'stateless handoff' (phần AI-dạy-thật
tách riêng, bán-thủ-công). Vì cmd_status/cmd_resume là hàm ĐỌC-FILE THUẦN nên 'phiên 2' được mô phỏng
trung thực bằng lời gọi MỚI trên vault đã COPY sang path tuyệt đối KHÁC (giả lập máy khác).

Có RĂNG (chống hồi quy): nếu next_action không được persist / open_session không hiện / state không
sống sót khi đổi path → test đỏ. Không AI, không ngẫu nhiên, không phụ thuộc đồng hồ (now=AT cố định).
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)  # >= created demo (2026-06-30); cố định → tất định
LS_REL = "topics/docker/lessons/lesson-001/lesson_state.md"


def _session1_leaves_open(tmp_path) -> Path:
    """Phiên 1: mở vault, /resume trên current_lesson → MỞ phiên (open_session), KHÔNG /done.
    Trả path vault phiên-1 (đã ghi open_session vào file)."""
    v = tmp_path / "machineA" / "learning_vault"
    v.parent.mkdir(parents=True)
    shutil.copytree(REAL_VAULT, v)
    committed, _rep, _info = S.cmd_resume(v, ROOT, AT)
    assert committed, "phiên 1: /resume phải commit (mở phiên)"
    # xác nhận open_session ĐÃ vào FILE (không chỉ trong bộ nhớ)
    assert (S._load_raw(v / "vault_state.md")[0].get("open_session") or {}).get("lesson_id") \
        == "docker/lesson-001"
    return v


def _handoff_to_new_path(vault_a: Path, tmp_path) -> Path:
    """Giả lập 'máy khác': copy vault sang path tuyệt đối KHÁC HẲN. Không mang theo gì ngoài file."""
    vault_b = tmp_path / "machineB" / "vault_copy"
    vault_b.parent.mkdir(parents=True)
    shutil.copytree(vault_a, vault_b)
    assert str(vault_b) != str(vault_a)
    return vault_b


def test_stateless_handoff_recovers_full_context(tmp_path):
    va = _session1_leaves_open(tmp_path)
    vb = _handoff_to_new_path(va, tmp_path)  # ← phiên 2 chỉ có file ở path mới

    # next_action THẬT trong file (đọc lại để so, KHÔNG hardcode giòn)
    expected_next = S._load_raw(vb / LS_REL)[0].get("next_action")
    assert expected_next and "Socrates" in expected_next, "demo phải có next_action self-describing"

    # ---- PHIÊN 2 (đọc nguội, path mới) ----
    st = S.cmd_status(vb, ROOT, AT)
    assert st["current_topic"] == "docker"
    assert st["current_lesson"] == "docker/lesson-001"
    assert st["unclosed_session"] is True, "phiên 2 phải thấy cảnh báo phiên chưa /done (§11B.2)"
    assert st["open_session_lesson"] == "docker/lesson-001"

    committed, _rep, info = S.cmd_resume(vb, ROOT, AT)
    assert committed
    assert info["current_lesson"] == "docker/lesson-001"
    assert info["status"] == "in_progress"
    # ĐÚNG chỗ dở: next_action khôi phục KHỚP HỆT file → 'không hỏi lại từ đầu'
    assert info["next_action"] == expected_next


def test_handoff_vault_still_valid_on_new_path(tmp_path):
    # Portability + tính hợp lệ sau khi đổi path (INV-16 + toàn vẹn): validator FULL vẫn PASS.
    va = _session1_leaves_open(tmp_path)
    vb = _handoff_to_new_path(va, tmp_path)
    rep = V.Report()
    V.validate_full_semantic(ROOT, vb, rep, now=AT)
    assert rep.ok(), f"vault sau handoff phải FULL PASS: {rep.errors}"


def test_session2_status_is_deterministic(tmp_path):
    # Hai lần đọc nguội liên tiếp (phiên 2) → kết quả GIỐNG HỆT (không phụ thuộc trạng thái ẩn/đồng hồ).
    va = _session1_leaves_open(tmp_path)
    vb = _handoff_to_new_path(va, tmp_path)
    assert S.cmd_status(vb, ROOT, AT) == S.cmd_status(vb, ROOT, AT)
