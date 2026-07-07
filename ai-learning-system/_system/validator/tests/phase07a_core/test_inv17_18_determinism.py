"""P07a — INV-17/18: thứ tự lỗi E-MIX-* phải TẤT ĐỊNH cross-machine (§0/§1 determinism + INV-16 portable).

Bản chất: _check_no_code_in_vault / _check_no_data_in_system duyệt bằng os.walk — os.walk trả file theo
thứ tự FILESYSTEM (khác nhau giữa máy/OS). Nhiều vi phạm ⇒ thứ tự lỗi (⇒ report) LỆCH giữa máy, phá
'report giống hệt'. Cả codebase còn lại đã sorted(); hai hàm này phải đồng nhất.

Có RĂNG: monkeypatch os.walk trả filenames thứ tự ĐẢO trong CÙNG một thư mục → hàm phải tự sort
(sorted(filenames)) ⇒ lỗi ra theo path sorted. Không sort (bug) ⇒ lỗi theo thứ tự đảo ⇒ đỏ. Không phụ
thuộc filesystem thật. Test cô lập THỨ TỰ FILE trong 1 dir (tách khỏi thứ tự duyệt dir).

Bổ sung: 1 test trên cây tmp THẬT (2 dir + nhiều file cấm) assert report sorted — khoá guarantee đầy đủ
(dirnames.sort() cho descent + sorted(filenames)); trên máy này đủ để phát hiện hồi quy thô.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import validate as V  # noqa: E402


def test_no_code_file_order_sorted_within_dir(monkeypatch):
    base = Path("vaultroot")
    fake = [(str(base), ["okdir"], ["zebra.py", "mango.py", "alpha.py"])]  # thứ tự đảo, cùng 1 dir
    monkeypatch.setattr(V.os, "walk", lambda root: iter(fake))
    rep = V.Report()
    V._check_no_code_in_vault(base, rep)
    files = [e["file"] for e in rep.errors]
    assert files == ["alpha.py", "mango.py", "zebra.py"], f"E-MIX-CODE phải sorted trong dir: {files}"


def test_no_data_file_order_sorted_within_dir(monkeypatch):
    base = Path("sysroot")
    fake = [(str(base), [], ["topic_state.md", "sources.md", "lesson_state.md"])]  # thứ tự đảo
    monkeypatch.setattr(V.os, "walk", lambda root: iter(fake))
    rep = V.Report()
    V._check_no_data_in_system(base, rep)
    files = [e["file"] for e in rep.errors]
    assert files == ["lesson_state.md", "sources.md", "topic_state.md"], f"E-MIX-DATA phải sorted: {files}"


def test_no_code_real_tree_report_fully_sorted(tmp_path):
    # Cây THẬT: 2 thư mục con, mỗi cái 1 file cấm + file cấm ở gốc → report phải sorted hoàn toàn.
    (tmp_path / "vault_state.md").write_text("---\nschema: vault_state\n---\n", encoding="utf-8")
    (tmp_path / "zeta").mkdir(); (tmp_path / "zeta" / "z.py").write_text("x", encoding="utf-8")
    (tmp_path / "alpha").mkdir(); (tmp_path / "alpha" / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "run.js").write_text("x", encoding="utf-8")
    rep = V.Report()
    V._check_no_code_in_vault(tmp_path, rep)
    files = [e["file"] for e in rep.errors]
    # os.walk top-down + dirnames.sort() + sorted(filenames) ⇒ thứ tự TẤT ĐỊNH (không theo FS):
    # gốc trước (run.js; vault_state.md KHÔNG cấm) → rồi dir con sorted: alpha/ → zeta/
    assert files == ["run.js", "alpha/a.py", "zeta/z.py"], \
        f"thứ tự E-MIX-CODE phải là DFS tất định (gốc→con sorted), gặp: {files}"
