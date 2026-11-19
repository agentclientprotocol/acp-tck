"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_transport.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._expectations import _CANCEL_IDS, _MANDATORY_IDS
from .._runner import _run_cli, _table_statuses


def test_banner_on_stdout_fails_transport_001_but_passes_transport_002():
    """The banner is plain ASCII -- valid UTF-8 -- so it must FAIL ACP-TRANSPORT-001 (framing)
    but PASS ACP-TRANSPORT-002 (UTF-8), not be misreported as a UTF-8 violation."""
    result = _run_cli("banner_on_stdout.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-TRANSPORT-001") == "FAIL", result.stdout
    assert statuses.get("ACP-TRANSPORT-002") == "PASS", result.stdout
    assert statuses.get("ACP-SCHEMA-001") == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - {"ACP-TRANSPORT-001", "ACP-SCHEMA-001"} - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"

    # The FAILed requirement's own spec text/citation should be visible without opening source:
    # once in the summary table (indented under its id/status row) ...
    assert (
        "Every line the agent writes to stdout is a single valid JSON-RPC 2.0 message." in result.stdout
    ), result.stdout
    assert "transports.mdx:20,21,23" in result.stdout, result.stdout
    # ... and once as its own pytest FAILURES section, next to the traceback/transcript.
    assert "ACP requirement ACP-TRANSPORT-001" in result.stdout, result.stdout
    # A PASSing requirement's text is noise, not signal -- it must not be printed in the table.
    assert "The agent's stdout is valid UTF-8." not in result.stdout, result.stdout


def test_invalid_utf8_fails_transport_002():
    """`invalid_utf8.py` is ACP-TRANSPORT-002's real negative control: a lone undecodable line
    makes ACP-TRANSPORT-002 FAIL."""
    result = _run_cli("invalid_utf8.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-TRANSPORT-002") == "FAIL", result.stdout


def test_garbage_after_response_fails_transport_001():
    """`garbage_after_response.py` writes non-JSON to stdout only after stdin closes -- strictly
    after the last response any test awaits. `close()` must drain and record that line so
    ACP-TRANSPORT-001 catches it instead of reporting a false PASS."""
    result = _run_cli("garbage_after_response.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-TRANSPORT-001") == "FAIL", result.stdout
