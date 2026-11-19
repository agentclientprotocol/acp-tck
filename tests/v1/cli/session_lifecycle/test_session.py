"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_session.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._expectations import _CANCEL_IDS, _MANDATORY_IDS
from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_duplicate_session_id_fails_session_002_only():
    result = _run_cli("duplicate_session_id.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-SESSION-002") == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - {"ACP-SESSION-002"} - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_rejects_mcp_servers_fails_session_003_only():
    """`rejects_mcp_servers.py` errors on any non-empty `mcpServers`; ACP-SESSION-004 SKIPs on
    the failed prerequisite rather than double-reporting it."""
    result = _run_cli("rejects_mcp_servers.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-SESSION-003"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-SESSION-004") == "SKIPPED", result.stdout


def test_ignores_mcp_servers_fails_advisory_session_004_only():
    """`ignores_mcp_servers.py` accepts but never launches stdio MCP servers -- an ADVISORY
    (SHOULD) failure, so the run stays CONFORMANT."""
    result = _run_cli("ignores_mcp_servers.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _output_fail_ids(result.stdout) == {"ACP-SESSION-004"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-SESSION-003") == "PASS", result.stdout


def test_leaks_mcp_env_fixtures_fail_session_006_only_advisory():
    """One fixture per leak channel (`_meta` on stdout, stderr, the stub's command line). The
    leak is a SHOULD NOT, so the run stays CONFORMANT, and the stub still connects."""
    for fixture in ("leaks_mcp_env_meta.py", "leaks_mcp_env_stderr.py", "leaks_mcp_env_argv.py"):
        result = _run_cli(fixture)
        assert result.returncode == 0, f"{fixture}:\n{result.stdout}{result.stderr}"
        assert "VERDICT: CONFORMANT" in result.stdout, f"{fixture}:\n{result.stdout}"
        assert _output_fail_ids(result.stdout) == {"ACP-SESSION-006"}, f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        assert statuses.get("ACP-SESSION-004") == "PASS", f"{fixture}:\n{result.stdout}"
