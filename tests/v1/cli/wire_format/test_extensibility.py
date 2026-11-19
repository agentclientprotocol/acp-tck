"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_extensibility.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _fail_ids, _run_cli, _table_statuses


def test_exit_on_malformed_mcp_message_fails_ext_002_only():
    """`exits_on_malformed_mcp_message.py` does not advertise `mcpCapabilities.acp` and exits on an
    `mcp/message` notification missing `requestId`. It sent no reply, so ACP-JSONRPC-003 PASSes;
    the crash on a notification it does not recognize is ACP-EXT-002's finding."""
    result = _run_cli("exits_on_malformed_mcp_message.py", k="test_jsonrpc or test_extensibility")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-EXT-002"}, result.stdout
    assert statuses.get("ACP-JSONRPC-003") == "PASS", result.stdout


def test_acp_advertising_agent_is_not_sent_the_ext_002_mcp_probe():
    """`answers_mcp_notification.py` advertises `mcpCapabilities.acp`, so ACP-EXT-002's `mcp/message`
    probe is skipped for it; the `_tck/notify` probe still PASSes the row."""
    result = _run_cli("answers_mcp_notification.py", k="test_extensibility")
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-EXT-002") == "PASS", result.stdout


def test_exits_on_unknown_notification_fails_ext_002_and_jsonrpc_006_only():
    """`exits_on_unknown_notification.py` dies on `_`/`$/` notifications without replying, so
    ACP-JSONRPC-003 still PASSes: an exit is not a reply."""
    result = _run_cli("exits_on_unknown_notification.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-EXT-002", "ACP-JSONRPC-006"}, result.stdout
    assert statuses.get("ACP-JSONRPC-003") == "PASS", result.stdout


def test_error_with_meta_fails_schema_002_advisory_only():
    """`error_with_meta.py` puts `_meta` on every error object, which `Error` does not define."""
    result = _run_cli("error_with_meta.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-SCHEMA-002"}, result.stdout


def test_silent_on_unknown_method_fails_ext_001_only():
    """`silent_on_unknown_method.py` never answers a `_`-prefixed request. Only ACP-EXT-001 owns
    that defect: ACP-JSONRPC-004 SKIPs and ACP-ERROR-001 judges its remaining sample."""
    result = _run_cli("silent_on_unknown_method.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-EXT-001"}, result.stdout
    assert statuses.get("ACP-ERROR-001") == "PASS", result.stdout
    assert statuses.get("ACP-JSONRPC-004") == "SKIPPED", result.stdout
