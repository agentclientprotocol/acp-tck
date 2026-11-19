"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_session.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails_for, _run_cli, _table_statuses
from ._helpers import _SETUP_K


def test_duplicate_session_id_fails_session_002_only():
    """`duplicate_session_id.py` always returns the same `sessionId` -- fails only the CAPABILITY
    `ACP-SESSION-002`, which alone must still flip the verdict to NOT CONFORMANT."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "duplicate_session_id.py",
        protocol_version=2,
        k="test_session and not capabilities and not config",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SESSION-002"}, result.stdout
    assert statuses.get("ACP-SESSION-001") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_accepts_relative_cwd_fails_session_204_only():
    """Accepting the relative `cwd` FAILs `ACP-SESSION-204` within `-k test_session`;
    `ACP-SESSION-209` SKIPs (nothing was rejected, so no code to judge)."""
    fails, statuses, out = _fails_for("accepts_relative_cwd.py", _SETUP_K)
    assert fails == {"ACP-SESSION-204"}, out
    assert statuses.get("ACP-SESSION-209") == "SKIPPED", out


def test_new_relative_cwd_wrong_code_fails_session_209_advisory_only():
    """`new_relative_cwd_wrong_code.py` rejects with `-32600`: `ACP-SESSION-204` PASSes and the
    ADVISORY `ACP-SESSION-209` FAILs (alone, within `-k test_session`)."""
    fails, statuses, out = _fails_for("new_relative_cwd_wrong_code.py", _SETUP_K)
    assert fails == {"ACP-SESSION-209"}, out
    assert statuses.get("ACP-SESSION-204") == "PASS", out


def test_advertising_acp_mcp_agent_is_not_sent_the_acp_probe():
    """`advertises_acp_mcp.py` accepts an `acp` declaration because it advertises
    `capabilities.session.mcp.acp`; `ACP-MCP-203` skips its `acp` probe and PASSes."""
    fails, statuses, out = _fails_for("advertises_acp_mcp.py", _SETUP_K)
    assert fails == set(), out
    assert statuses.get("ACP-MCP-203") == "PASS", out


def test_permission_before_new_response_fails_session_206_only():
    fails, statuses, out = _fails_for("permission_before_new_response.py", _SETUP_K)
    assert fails == {"ACP-SESSION-206"}, out
    assert statuses.get("ACP-SESSION-207") == "PASS", out


def test_config_notified_before_new_response_fails_session_207_only():
    """The response carries the same `configOptions`, so `ACP-SESSION-208` PASSes."""
    fails, statuses, out = _fails_for("config_notified_before_new_response.py", _SETUP_K)
    assert fails == {"ACP-SESSION-207"}, out
    assert statuses.get("ACP-SESSION-208") == "PASS", out


def test_commands_only_in_early_notification_fails_session_207_and_208():
    fails, _statuses, out = _fails_for("commands_only_in_early_notification.py", _SETUP_K)
    assert fails == {"ACP-SESSION-207", "ACP-SESSION-208"}, out
