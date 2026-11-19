"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_jsonrpc.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import pytest

from .._expectations import _ALL_IDS
from .._runner import (
    FIXTURES_DIR_V2,
    _TABLE_ROW_RE,
    _assert_conforming_baseline,
    _fails,
    _run_cli,
    _table_statuses,
)


def _table_notes(output: str) -> dict[str, str]:
    """Parse each summary-table row's trailing `(note)` text (empty if none), keyed by id."""
    notes: dict[str, str] = {}
    for line in output.splitlines():
        match = _TABLE_ROW_RE.match(line)
        if match:
            notes[match.group(1)] = line[match.end():].strip()
    return notes


def test_asks_permission_twice_passes_both_jsonrpc_202_halves():
    """`asks_permission_twice.py` has two permission requests pending at once with distinct ids,
    so the reuse half of `ACP-JSONRPC-202` is observable (two requests held) and PASSes, as does
    the id-type half."""
    result = _run_cli(
        FIXTURES_DIR_V2, "asks_permission_twice.py", protocol_version=2, k="jsonrpc or permission"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-JSONRPC-202"] == "PASS", result.stdout
    assert statuses["ACP-PERM-201"] == "PASS", result.stdout


def test_asks_permission_reused_id_fails_jsonrpc_202_only():
    result = _run_cli(
        FIXTURES_DIR_V2,
        "asks_permission_reused_id.py",
        protocol_version=2,
        k="jsonrpc or permission or cancel",
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-202"}, result.stdout


def test_asks_permission_null_id_fails_jsonrpc_202_and_perm_201_only():
    """A `null` request id is both the `ACP-JSONRPC-202` defect and a schema violation of the
    request itself, which `ACP-PERM-201` validates."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "asks_permission_null_id.py",
        protocol_version=2,
        k="jsonrpc or permission or cancel",
    )
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-202", "ACP-PERM-201"}, result.stdout


def test_v2_wrong_id_echo_fails_id_dependent_requirements():
    """`wrong_id_echo.py` mangles every response id -- violates `ACP-JSONRPC-001`. Breaking id
    correlation for literally every request/response pair in the connection cascades into
    almost every other requirement (each of whose own test can no longer find its own response
    at all, and either FAILs via a mismatched-shape assertion or hits `AgentTimeout`) --
    unscoped, this fixture cascades into nearly every id, which is the intended, correct verdict
    shape for an agent this broken, not a TCK bug -- so this self-test scopes the run to `-k jsonrpc`
    (mirroring v1's own precedent for the identical problem) rather than paying the cost of an
    unscoped run across the whole suite. Scoped, the only requirements actually exercised are
    the six `ACP-JSONRPC-*` ids (001..005, 202) plus `ACP-TRANSPORT-001` (`test_transport.py`'s
    own full-exchange test matches the `-k jsonrpc` substring via its function name) --
    everything else is deselected (`NOT_TESTED`). `ACP-JSONRPC-202` FAILs too: its tests need a
    working `session/new` to elicit requests, and (like `ACP-JSONRPC-003`/`005`) hit the
    unmatched response."""
    result = _run_cli(
        FIXTURES_DIR_V2, "wrong_id_echo.py", protocol_version=2, k="jsonrpc", startup_timeout="1"
    )  # initialize never matches
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {
        "ACP-JSONRPC-001",
        "ACP-JSONRPC-002",
        "ACP-JSONRPC-003",
        "ACP-TRANSPORT-001",
        "ACP-JSONRPC-004",
        "ACP-JSONRPC-005",
        "ACP-JSONRPC-202",
    }, result.stdout
    assert statuses.get("ACP-JSONRPC-001") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-002") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-003") == "FAIL", result.stdout
    assert statuses.get("ACP-TRANSPORT-001") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-004") == "FAIL", result.stdout
    assert statuses.get("ACP-JSONRPC-005") == "FAIL", result.stdout
    for req_id in _ALL_IDS - fails:
        assert statuses.get(req_id) == "NOT_TESTED", (
            f"{req_id} is {statuses.get(req_id)}, expected NOT_TESTED (deselected by -k "
            f"jsonrpc):\n{result.stdout}"
        )
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_answers_notifications_fails_jsonrpc_003_only():
    """`answers_notifications.py` unconditionally replies to the `session/cancel` notification
    with a bogus error response (`{"id": null, "error": ...}`) -- violates `ACP-JSONRPC-003`
    (notifications never receive a response). Nothing else about it is non-conforming; the
    reply's `id: null` is legal on an error, so `ACP-JSONRPC-002` is unaffected."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_notifications.py", protocol_version=2, k="jsonrpc")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-003"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


@pytest.mark.parametrize(
    "fixture", ["answers_mcp_notification.py", "answers_malformed_mcp_notification.py"]
)
def test_v2_answers_mcp_notification_fails_jsonrpc_003_only(fixture: str):
    """Each fixture advertises `capabilities.session.mcp.acp` and replies to one `mcp/message`
    probe only (`answers_mcp_notification.py` the well-formed one,
    `answers_malformed_mcp_notification.py` the one missing `requestId`/`method`); `session/cancel`
    and the other probes stay silent, so that probe alone fails `ACP-JSONRPC-003` and each probe is
    pinned."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="jsonrpc")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-JSONRPC-003"}, result.stdout


def test_v2_pushes_status_notifications_passes_everything():
    """`pushes_status_notifications.py` pushes an unsolicited `_`-prefixed notification right
    after `initialize` and before handling every later message, including ahead of an array's
    rejection. So they land both in the quiet period of `ACP-JSONRPC-003`/`ACP-EXT-002` and
    between a request and its reply (`ACP-BATCH-209`, `ACP-JSONRPC-001`/`005`). A notification
    is not a reply, so the outcome must match `conforming.py`'s exactly -- including the
    INFORMATIONAL probes' recorded behaviour, which must not mistake a push for the reply."""
    result = _run_cli(FIXTURES_DIR_V2, "pushes_status_notifications.py", protocol_version=2)
    _assert_conforming_baseline(result, "pushes_status_notifications.py")

    notes = _table_notes(result.stdout)
    for req_id in ("ACP-INFO-PARSE-001", "ACP-INFO-INVALIDREQ-001"):
        assert notes[req_id].startswith("(silent"), f"{req_id}: {notes[req_id]}"
    for req_id, note in notes.items():
        assert "_fixture/status_update" not in note, f"{req_id}: {note}"


def test_v2_pushes_status_and_answers_notifications_fails_no_reply_rows_only():
    """`pushes_status_and_answers_notifications.py` pushes the same status notification, then
    also replies to the notification. The leading notification must not hide the reply behind
    it: every "a notification gets no response" row still FAILs."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "pushes_status_and_answers_notifications.py",
        protocol_version=2,
        k="test_jsonrpc or test_extensibility",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-003", "ACP-EXT-002", "ACP-EXT-203"}, result.stdout


def test_v2_result_and_error_fails_jsonrpc_002_and_schema_001_only():
    """`result_and_error.py`'s `initialize` response illegally carries both `result` and
    `error` -- violates `ACP-JSONRPC-002` (exactly one of `result`/`error`) and, via the same
    envelope check, `ACP-SCHEMA-001`. `ACP-INIT-001` still PASSes: that check only asserts
    `"result" in msg`, which remains true even though `error` is also illegally present."""
    result = _run_cli(
        FIXTURES_DIR_V2, "result_and_error.py", protocol_version=2, k="jsonrpc or initialize"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-002", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-INIT-001") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_unknown_method_no_error_only_fails_the_advisory_requirement():
    """`unknown_method_no_error.py` replies to unknown methods with an empty success result
    instead of `-32601`. Should only trip the MANDATORY `ACP-JSONRPC-004` (unknown method ->
    `-32601` is a MUST); it does reply, so `ACP-EXT-001` is not tripped. `ACP-BATCH-209`'s probes never
    expect an unknown-method reply, so this fixture does not fail it.
    The exit code/overall verdict text are not asserted here: this run is `-k`-scoped, which
    necessarily leaves every other MANDATORY id NOT_TESTED, and NOT_TESTED MANDATORY ids flip
    the verdict to NOT CONFORMANT by design -- that says nothing about whether *this* fixture's
    behaviour for the ids actually exercised is conforming, which is what the per-id statuses
    below check."""
    result = _run_cli(
        FIXTURES_DIR_V2, "unknown_method_no_error.py", protocol_version=2, k="jsonrpc or batch"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-JSONRPC-004"}, result.stdout
    assert statuses.get("ACP-BATCH-209") == "PASS", result.stdout
