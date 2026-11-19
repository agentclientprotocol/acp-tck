"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_transport.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_v2_banner_on_stdout_fails_transport_001_and_schema_001_only():
    """`banner_on_stdout.py` prints a human banner line to stdout before behaving like a
    conforming agent -- violates `ACP-TRANSPORT-001` ("every stdout line is a valid ACP
    message"). The banner line also shows up in the full-exchange schema scan
    (`ACP-SCHEMA-001`), which fails the same way `test_initialize.py`'s scan does for any
    non-object line it can't attribute to a method/response. The banner is plain ASCII, so it
    does not additionally violate `ACP-TRANSPORT-002`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "banner_on_stdout.py", protocol_version=2, k="transport or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-001", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_invalid_utf8_fails_transport_001_002_and_schema_001():
    """`invalid_utf8.py` writes one line of invalid UTF-8 bytes to stdout before behaving like a
    conforming agent -- the dedicated negative control for `ACP-TRANSPORT-002`. A line that
    isn't decodable text isn't valid JSON either, so it also fails `ACP-TRANSPORT-001` and the
    full-exchange schema scan (`ACP-SCHEMA-001`), same cascade shape as `banner_on_stdout.py`."""
    result = _run_cli(
        FIXTURES_DIR_V2, "invalid_utf8.py", protocol_version=2, k="transport or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-002", "ACP-TRANSPORT-001", "ACP-SCHEMA-001"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_garbage_after_response_fails_transport_001_and_schema_001_only():
    """`garbage_after_response.py` is conforming for the whole exchange, then -- after stdin
    closes -- writes one line of plain-text (ASCII) garbage to stdout before exiting. Only
    catchable via `AgentProcess.close()`'s post-close stdout drain. Fails `ACP-TRANSPORT-001`
    (the garbage line is not valid JSON) and `ACP-SCHEMA-001` (the drained garbage line is still
    on `agent.transcript` when the schema scan runs after `connected_agent`'s `__aexit__`).
    `ACP-TRANSPORT-002` still PASSes: the garbage is plain ASCII."""
    result = _run_cli(
        FIXTURES_DIR_V2, "garbage_after_response.py", protocol_version=2, k="transport or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-001", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_message_split_across_multiple_lines_fails_transport_203():
    """A JSON-RPC message split over three physical stdout lines must fail the dedicated
    embedded-newline requirement as well as generic framing and schema validation."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "message_split_across_multiple_lines.py",
        protocol_version=2,
        k="transport or initialize",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-TRANSPORT-001", "ACP-TRANSPORT-203", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
