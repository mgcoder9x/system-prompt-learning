"""P10-agent — router_prompt.md khớp registry lệnh (commands.md) + 7 intent spec 11 (chống trôi).

- commands trong router == tập lệnh trong commands.md (backends) — single-source registry.
- intents trong router == đúng 7 intent spec 11 (mã hoá tại đây như chân lý spec, giống cách
  test_commands_registry mã hoá tập lệnh spec 11A.3).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import md_ast as A  # noqa: E402

# 7 intent spec mục 11 (nguồn: PROMPT_LEARNING_SYSTEM.md §11)
SPEC_INTENTS = {"new_topic", "lesson", "side_question", "review",
                "source_ingestion", "system_change", "unclear"}


def _router():
    text = (ROOT / "prompts" / "router_prompt.md").read_text(encoding="utf-8")
    return A.extract_yaml_under_heading(text, "router (máy đọc)", level=3)["router"]


def _registry_commands():
    text = (ROOT / "commands.md").read_text(encoding="utf-8")
    return set(A.extract_yaml_under_heading(text, "backends (máy đọc)", level=2)["backends"])


def test_router_commands_match_registry():
    router_cmds = set(_router()["commands"])
    reg = _registry_commands()
    assert router_cmds == reg, f"router-thừa={sorted(router_cmds - reg)}, registry-thiếu-ở-router={sorted(reg - router_cmds)}"


def test_router_intents_match_spec():
    intents = set(_router()["intents"])
    assert intents == SPEC_INTENTS, f"router-thừa={sorted(intents - SPEC_INTENTS)}, spec-thiếu-ở-router={sorted(SPEC_INTENTS - intents)}"


def test_all_prompt_files_present_nonempty():
    for name in ("system_prompt.md", "router_prompt.md", "system_change_prompt.md"):
        p = ROOT / "prompts" / name
        assert p.is_file(), f"thiếu prompts/{name}"
        assert p.read_text(encoding="utf-8").strip(), f"prompts/{name} rỗng"
