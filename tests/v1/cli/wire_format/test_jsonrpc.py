"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_jsonrpc.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import pytest

from .._expectations import _CANCEL_IDS, _MANDATORY_IDS
from .._runner import _fail_ids, _run_cli, _table_statuses


def test_wrong_id_echo_fails_id_dependent_requirements():
    """`wrong_id_echo.py` mangles every response id, which breaks id-correlated waits (used by
    almost every test's setup, not only the id-echo test itself) -- so nearly everything times
    out and fails. This is expected: a broken id-echo genuinely makes the agent unusable.

    Scoped to `jsonrpc`: an unscoped run against this fixture means *every* test in the suite
    times out waiting for an id-correlated response before failing, which costs far longer for
    a fact this one id already demonstrates -- narrowing to the id-echo tests themselves keeps
    the same assertion true in a fraction of the time."""
    result = _run_cli("wrong_id_echo.py", k="jsonrpc", startup_timeout="1")  # initialize never matches
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-JSONRPC-001") == "FAIL", result.stdout


def test_answers_notifications_fails_jsonrpc_003_only():
    result = _run_cli("answers_notifications.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-JSONRPC-003") == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - {"ACP-JSONRPC-003"} - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_pushes_status_and_answers_notifications_fails_jsonrpc_003_only():
    """`pushes_status_and_answers_notifications.py` pushes the same status notification, then
    also replies to the notification. The leading notification must not hide the reply behind
    it."""
    result = _run_cli("pushes_status_and_answers_notifications.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-003"}, result.stdout


def test_unknown_method_no_error_only_fails_the_advisory_requirement():
    """An ADVISORY-only failure must not affect the verdict: exit code 0, `VERDICT: CONFORMANT`,
    even though ACP-JSONRPC-004 itself FAILs."""
    result = _run_cli("unknown_method_no_error.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-JSONRPC-004") == "FAIL", result.stdout
    for req_id in _CANCEL_IDS | {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "SKIPPED", f"{req_id} should SKIP (unexercised):\n{result.stdout}"
    for req_id in _MANDATORY_IDS - _CANCEL_IDS - {"ACP-AUTH-003"}:
        assert statuses.get(req_id) == "PASS", f"{req_id} should still PASS:\n{result.stdout}"


def test_answers_custom_notifications_fails_jsonrpc_003_only():
    """`answers_custom_notifications.py` replies to `_`-prefixed notifications; the connection
    stays usable, so ACP-EXT-002 still PASSes."""
    result = _run_cli("answers_custom_notifications.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-JSONRPC-003"}, result.stdout
    assert statuses.get("ACP-EXT-002") == "PASS", result.stdout


@pytest.mark.parametrize(
    "fixture", ["answers_mcp_notification.py", "answers_malformed_mcp_notification.py"]
)
def test_answers_mcp_notification_fails_jsonrpc_003_only(fixture: str):
    """Each fixture advertises `mcpCapabilities.acp` and replies to one `mcp/message` probe only
    (`answers_mcp_notification.py` the well-formed one, `answers_malformed_mcp_notification.py`
    the one missing `requestId`/`method`); the other probes stay silent, so that probe alone fails
    ACP-JSONRPC-003 and each probe is pinned."""
    result = _run_cli(fixture, k="test_jsonrpc")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-JSONRPC-003"}, result.stdout
    assert statuses.get("ACP-JSONRPC-006") == "PASS", result.stdout


def test_answers_cancel_request_fails_jsonrpc_003_only():
    """`answers_cancel_request.py` replies to `$/cancel_request`; the connection stays usable,
    so ACP-JSONRPC-006 still PASSes."""
    result = _run_cli("answers_cancel_request.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-JSONRPC-003"}, result.stdout
    assert statuses.get("ACP-JSONRPC-006") == "PASS", result.stdout


def test_cancel_request_wrong_error_fails_jsonrpc_007_only():
    """`cancel_request_wrong_error.py` answers a `$/cancel_request`-cancelled prompt with
    `-32603`. `--cancel-prompt __hang__` keeps the prompt in flight, so ACP-CANCEL-001/002 are
    exercised too and PASS."""
    result = _run_cli("cancel_request_wrong_error.py", cancel_prompt="__hang__")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-JSONRPC-007"}, result.stdout
    assert statuses.get("ACP-CANCEL-001") == "PASS", result.stdout
