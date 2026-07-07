"""P10-agent — START_HERE.md (bootstrap cho AI mới, gốc ai-learning-system) drift-guard.

START_HERE là 'mồi' cho bất kỳ AI/người mới mở folder copy: đọc gì trước, luật cứng, cách chạy. Bản chất
của nó là các POINTER; nếu pointer trỏ file KHÔNG tồn tại (đổi tên/di chuyển) → AI mới theo sẽ CHẾT LẶNG.
Test này khoá: mọi path trong khối 'bootstrap (máy đọc)' PHẢI tồn tại (relative gốc ai-learning-system).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # .../_system
AI_ROOT = ROOT.parent                          # .../ai-learning-system (đơn vị portable)
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

START_HERE = AI_ROOT / "START_HERE.md"


def _bootstrap():
    text = START_HERE.read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "bootstrap (máy đọc)", level=2)["bootstrap"]


def _required_in_unit_pointers(b: dict):
    """Pointer bắt-buộc-tồn-tại: chỉ những cái NẰM TRONG đơn vị portable.

    CỐ Ý loại `spec_ground_truth` (= ../PROMPT_LEARNING_SYSTEM.md) vì spec gốc nằm ở thư
    mục CHA, NGOÀI đơn vị học (DEC-047) — nó không đi theo bản copy portable. Ép nó tồn tại
    sẽ làm MỌI handoff portable hợp lệ đỏ oan (đúng ca HANDOFF_RESULT báo 451/1 trên copy sạch).
    spec_ground_truth được kiểm riêng ở test_spec_ground_truth_is_external_not_required.
    """
    paths = list(b.get("read_order", []))
    for k in ("first_run_check", "setup_lock", "runbook"):
        if b.get(k):
            paths.append(b[k])
    return paths


def test_start_here_exists_nonempty():
    assert START_HERE.is_file(), "thiếu ai-learning-system/START_HERE.md (bootstrap cho AI mới)"
    assert START_HERE.read_text(encoding="utf-8").strip(), "START_HERE.md rỗng"


def test_bootstrap_pointers_all_exist():
    # Chỉ khoá pointer TRONG đơn vị (spec_ground_truth ngoài-đơn-vị kiểm riêng — DEC-047),
    # để test này pass cả trên bản copy portable (thư mục cha không mang spec gốc).
    b = _bootstrap()
    missing = [p for p in _required_in_unit_pointers(b) if not (AI_ROOT / p).exists()]
    assert not missing, f"START_HERE trỏ file KHÔNG tồn tại (pointer TRONG đơn vị): {missing}"


def test_bootstrap_reads_constitution_first():
    # Luật mồi cốt lõi: AI mới PHẢI nạp hiến pháp (system_prompt) trong read_order.
    b = _bootstrap()
    assert any("system_prompt.md" in p for p in b.get("read_order", [])), \
        "read_order PHẢI gồm prompts/system_prompt.md (nạp hiến pháp trước khi hành động)"


def test_portable_copy_no_parent_spec(tmp_path):
    """RED-first: bản copy PORTABLE (thư mục cha KHÔNG có spec gốc) — drift-guard pointer
    PHẢI vẫn pass. spec_ground_truth (../PROMPT_LEARNING_SYSTEM.md) nằm NGOÀI đơn vị học
    (DEC-047) nên KHÔNG được là điều kiện bắt buộc; nếu ép nó tồn tại → mọi handoff portable
    hợp lệ đều đỏ oan (đúng ca AI khác báo trong HANDOFF_RESULT: 451/1)."""
    b = _bootstrap()
    # dựng một 'đơn vị portable' giả trong tmp: tạo MỌI pointer TRONG đơn vị, KHÔNG tạo spec cha.
    for p in _required_in_unit_pointers(b):
        dst = tmp_path / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text("stub", encoding="utf-8")
    assert not (tmp_path.parent / "PROMPT_LEARNING_SYSTEM.md").exists(), \
        "tiền đề test: cha của bản copy portable KHÔNG có spec gốc"
    missing = [p for p in _required_in_unit_pointers(b) if not (tmp_path / p).exists()]
    assert not missing, f"portable copy thiếu pointer TRONG-đơn-vị: {missing}"


def test_spec_ground_truth_is_external_not_required():
    """spec_ground_truth được khai báo là pointer NGOÀI đơn vị (bắt đầu '..') và KHÔNG nằm
    trong tập pointer bắt-buộc-tồn-tại — khớp START_HERE ('thư mục CHA, ngoài đơn vị học')."""
    b = _bootstrap()
    sgt = b.get("spec_ground_truth", "")
    assert sgt.startswith(".."), "spec_ground_truth phải trỏ ra NGOÀI đơn vị (thư mục cha)"
    assert sgt not in _required_in_unit_pointers(b), \
        "spec ngoài-đơn-vị KHÔNG được nằm trong tập pointer bắt-buộc-tồn-tại"
