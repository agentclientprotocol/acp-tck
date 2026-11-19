"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_prompt_capabilities.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails, _fails_for, _run_cli, _table_statuses


def test_rejects_image_when_advertised_fails_promptcap_001_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "rejects_image_when_advertised.py", protocol_version=2, k="prompt_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-PROMPTCAP-001"}, result.stdout
    assert statuses.get("ACP-PROMPTCAP-002") == "PASS", result.stdout
    assert statuses.get("ACP-PROMPTCAP-003") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_accepts_unknown_skill_fails_promptcap_202_only():
    """`accepts_unknown_skill.py` advertises `prompt.skill` and accepts a `skill` block naming no
    skill. `ACP-PROMPTCAP-201`'s `skill` case SKIPs (advertised)."""
    fails, statuses, out = _fails_for("accepts_unknown_skill.py", "test_prompt_capabilities")
    assert fails == {"ACP-PROMPTCAP-202"}, out
    assert statuses.get("ACP-PROMPTCAP-201") == "PASS", out


def test_conforming_full_passes_promptcap_202_and_conforming_skips_it():
    scope = "test_prompt_capabilities"
    full = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=scope).stdout)
    assert full["ACP-PROMPTCAP-202"] == "PASS", full
    plain = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k=scope).stdout)
    assert plain["ACP-PROMPTCAP-202"] == "SKIPPED", plain
    assert plain["ACP-PROMPTCAP-201"] == "PASS", plain


def test_accepts_unadvertised_content_fails_promptcap_201_only():
    """`accepts_unadvertised_content.py` advertises no prompt capability but accepts `image`,
    `audio` and `resource` blocks; the unknown `_tck_unknown` block is still rejected, so
    `ACP-PROMPT-211` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "accepts_unadvertised_content.py", protocol_version=2, k="test_prompt"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPTCAP-201"}, result.stdout
    assert statuses.get("ACP-PROMPT-211") == "PASS", result.stdout
