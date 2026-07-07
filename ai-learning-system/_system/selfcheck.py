"""First-run self-check — CHẠY NGAY sau khi copy folder để biết bản sao có nguyên vẹn + cần làm gì.

Chạy bằng Python HỆ THỐNG (>=3.10), KHÔNG cần .venv:
    python _system/selfcheck.py
Chỉ dùng thư viện chuẩn (không import gì trong _system) → chạy được trên bản sao 'trần'.
Exit 0 = cấu trúc nguyên vẹn; 1 = thiếu file cốt lõi (chưa dùng được).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Các file/thư mục CỐT LÕI phải có (relative gốc ai-learning-system). Thiếu = bản sao hỏng/không đủ.
REQUIRED = [
    "START_HERE.md",
    "learning_vault/vault_state.md",
    "_system/README.md",
    "_system/VERSION",
    "_system/requirements.txt",
    "_system/commands.md",
    "_system/PILOT_RUNBOOK.md",
    "_system/fsrs_config.yaml",
    "_system/prompts/system_prompt.md",
    "_system/prompts/router_prompt.md",
    "_system/prompts/system_change_prompt.md",
    "_system/validator/validate.py",
    "_system/validator/session.py",
    "_system/decisions/index.yaml",
]
REQUIRED_DIRS = ["_system/rules", "_system/validator/tests", "learning_vault/topics"]


def check(ai_root: Path) -> tuple[bool, list[str]]:
    """Kiểm bản sao. Trả (ok, các dòng báo cáo). KHÔNG in — để test gọi được."""
    ai_root = Path(ai_root)
    lines: list[str] = []
    ok = True

    # 1) Python version (khuyến cáo >=3.10; chỉ cảnh báo, không chặn cấu trúc)
    v = sys.version_info
    py_ok = (v.major, v.minor) >= (3, 10)
    lines.append(f"[{'OK' if py_ok else 'CẢNH BÁO'}] Python {v.major}.{v.minor}.{v.micro} "
                 f"({'>=3.10' if py_ok else 'CẦN >=3.10'})")

    # 2) File/thư mục cốt lõi
    for rel in REQUIRED:
        p = ai_root / rel
        good = p.is_file()
        ok = ok and good
        lines.append(f"[{'OK' if good else 'THIẾU'}] {rel}")
    for rel in REQUIRED_DIRS:
        p = ai_root / rel
        good = p.is_dir()
        ok = ok and good
        lines.append(f"[{'OK' if good else 'THIẾU'}] {rel}/ (thư mục)")

    # 3) .venv (thông tin — không chặn; venv phải dựng lại trên máy mới)
    venv_py = ai_root / "_system" / ".venv" / "Scripts" / "python.exe"
    venv_py_nix = ai_root / "_system" / ".venv" / "bin" / "python"
    has_venv = venv_py.is_file() or venv_py_nix.is_file()
    lines.append(f"[{'OK' if has_venv else 'CHƯA'}] _system/.venv "
                 f"({'đã có' if has_venv else 'CHƯA dựng — làm bước tiếp theo #1'})")

    # 4) Hướng dẫn bước tiếp theo
    lines.append("")
    lines.append("BƯỚC TIẾP THEO (từ thư mục _system/):")
    if not has_venv:
        lines.append("  1) python -m venv .venv")
        lines.append("     .venv\\Scripts\\python -m pip install --require-hashes -r requirements.txt")
        lines.append("     .venv\\Scripts\\python -m pip install pytest")
    lines.append("  2) .venv\\Scripts\\python -m pytest validator\\tests -q            # kỳ vọng: all passed")
    lines.append("  3) .venv\\Scripts\\python validator\\validate.py --system . --vault ..\\learning_vault "
                 "--level full --scope full --json   # kỳ vọng: pass:true")
    lines.append("  4) .venv\\Scripts\\python validator\\session.py status --system . --vault ..\\learning_vault")
    lines.append("  → Đọc ../START_HERE.md để biết luật + cách vận hành đầy đủ.")

    lines.append("")
    lines.append(f"KẾT QUẢ CẤU TRÚC: {'NGUYÊN VẸN — sẵn sàng dựng môi trường' if ok else 'THIẾU FILE CỐT LÕI — bản sao KHÔNG đủ'}")
    return ok, lines


def main() -> int:
    ai_root = Path(__file__).resolve().parent.parent  # _system/selfcheck.py → _system → ai-learning-system
    ok, lines = check(ai_root)
    print("=== AI Learning System — First-run Self-Check ===")
    print(f"(gốc: {ai_root})\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
