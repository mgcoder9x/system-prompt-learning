"""P10 driver — cmd_source: nạp nguồn status=raw (spec 15/5.3), transaction-LIGHT.

Golden: tạo sources.md nếu thiếu; id src-NNN tăng dần; status=raw; kind sai → validator LIGHT chặn
(không commit); topic không tồn tại → E-DRIVER; sau khi thêm raw source vault vẫn FULL-validate PASS.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]  # .../_system
sys.path.insert(0, str(ROOT / "validator"))

import session as S   # noqa: E402
import validate as V  # noqa: E402

REAL_VAULT = ROOT / "validator" / "tests" / "fixtures" / "demo_vault"
AT = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)


def _fresh(tmp_path) -> Path:
    v = tmp_path / "vault"
    shutil.copytree(REAL_VAULT, v)
    return v


def _full_ok(vault) -> bool:
    rep = V.Report()
    V.validate_full_semantic(ROOT, vault, rep, now=AT)
    return rep.ok()


def test_source_creates_sources_md_when_absent(tmp_path):
    v = _fresh(tmp_path)
    assert not (v / "topics/docker/sources.md").exists()  # demo docker chưa có sources.md
    committed, rep, sid = S.cmd_source(v, ROOT, "docker", "https://docs.docker.com", "link", AT,
                                       scope="lesson 1")
    assert committed, rep.errors
    assert sid == "src-001"
    src_raw = S._load_raw(v / "topics/docker/sources.md")[0]
    assert src_raw["schema"] == "sources" and src_raw["topic_id"] == "docker"
    s0 = src_raw["sources"][0]
    assert s0["id"] == "src-001" and s0["status"] == "raw" and s0["kind"] == "link"
    assert _full_ok(v), "vault sau /source raw phải vẫn FULL-validate PASS (để /done sau được)"


def test_source_id_increments(tmp_path):
    v = _fresh(tmp_path)
    _, _, id1 = S.cmd_source(v, ROOT, "docker", "ref-a", "doc", AT)
    _, _, id2 = S.cmd_source(v, ROOT, "docker", "ref-b", "note", AT)
    assert id1 == "src-001" and id2 == "src-002"
    src_raw = S._load_raw(v / "topics/docker/sources.md")[0]
    assert [s["id"] for s in src_raw["sources"]] == ["src-001", "src-002"]


def test_source_invalid_kind_rejected(tmp_path):
    v = _fresh(tmp_path)
    committed, rep, _sid = S.cmd_source(v, ROOT, "docker", "ref", "khong-hop-le", AT)
    assert not committed  # kind ngoài enum → validator LIGHT E-SCHEMA, KHÔNG commit
    assert any(e["error_code"] == "E-SCHEMA" for e in rep.errors)
    # file thật không đổi (transaction abort)
    assert not (v / "topics/docker/sources.md").exists()


def test_source_unknown_topic_raises(tmp_path):
    v = _fresh(tmp_path)
    with pytest.raises(S.SessionError):
        S.cmd_source(v, ROOT, "khong-ton-tai", "ref", "doc", AT)


def test_source_in_cli_commands():
    assert "source" in S.CLI_COMMANDS and hasattr(S, "cmd_source")
