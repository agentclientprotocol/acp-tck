"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_batch.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._expectations import (
    _ADVISORY_IDS,
    _ALL_IDS,
    _ALWAYS_SKIPPED_IDS,
    _BACKGROUND_OTHER_SKIP_IDS,
    _BACKGROUND_SKIP_IDS,
    _CHILD_CONTROL_IDS,
    _CHILD_REPLAY_WITHDRAWAL_IDS,
    _ITEM_CANCEL_IDS,
    _NO_AUTH_SKIP_IDS,
    _RESUME_BACKGROUND_SKIP_IDS,
    _SESSION_MGMT_EXTRAS_SKIP_IDS,
)
from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def test_crashes_on_batch_fails_only_the_advisory_array_rows():
    """`crashes_on_batch.py` exits the moment it sees any JSON array on stdin -- otherwise fully
    conforming. FAILs the ADVISORY rows whose tests send an array (`ACP-BATCH-209`,
    `ACP-JSONRPC-005`). It never writes an array, so the MANDATORY `ACP-TRANSPORT-001` (which
    shares the probe) PASSes, and the run stays CONFORMANT: the receiver clause of the
    no-batches rule carries no RFC 2119 keyword, so a crash is only an advisory finding."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "crashes_on_batch.py",
        protocol_version=2,
        timeout="2",
        cancel_prompt="__hang__",
    )
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209", "ACP-JSONRPC-005"}, result.stdout
    assert statuses.get("ACP-TRANSPORT-001") == "PASS", result.stdout
    assert all(req_id in _ADVISORY_IDS for req_id in fails), result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_ignores_batch_fails_only_batch_209():
    """`ignores_batch.py` answers `[]` with the single `-32600` object but silently drops every
    non-empty array (the Python SDK 1.0.0 shape). FAILs only the ADVISORY `ACP-BATCH-209`: the
    connection survives (`ACP-JSONRPC-005`) and nothing it writes is an array
    (`ACP-TRANSPORT-001`), so the run stays CONFORMANT."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "ignores_batch.py",
        protocol_version=2,
        timeout="2",
        cancel_prompt="__hang__",
    )
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209"}, result.stdout
    assert statuses.get("ACP-JSONRPC-005") == "PASS", result.stdout
    assert statuses.get("ACP-TRANSPORT-001") == "PASS", result.stdout
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def test_answers_batch_with_array_fails_batch_209_and_transport_001():
    """`answers_batch_with_array.py` keeps the JSON-RPC 2.0 batching ACP v2 removed: it
    dispatches an array's elements and answers with an array. FAILs `ACP-BATCH-209` (elements
    processed) and, because it wrote an array, the MANDATORY `ACP-TRANSPORT-001` -- so the run
    is NOT CONFORMANT. `ACP-JSONRPC-005` PASSes: the connection survives."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "answers_batch_with_array.py",
        protocol_version=2,
        k="test_batch or test_transport or test_jsonrpc",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209", "ACP-TRANSPORT-001"}, result.stdout
    assert statuses.get("ACP-JSONRPC-005") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_v2_pushes_status_and_processes_array_elements_fails_batch_209_only():
    """`pushes_status_and_processes_array_elements.py` pushes the same status notifications, but
    instead of rejecting an array it dispatches the elements and answers each on its own line
    (a push between them). Skipping the pushes must not hide element processing: `ACP-BATCH-209`
    FAILs. Nothing it writes is an array, so `ACP-TRANSPORT-001` PASSes, as do
    `ACP-JSONRPC-001` and `ACP-JSONRPC-005`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "pushes_status_and_processes_array_elements.py",
        protocol_version=2,
        k="test_batch or test_jsonrpc",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-BATCH-209"}, result.stdout
    for req_id in ("ACP-TRANSPORT-001", "ACP-JSONRPC-001", "ACP-JSONRPC-005"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"


def test_v2_emits_batch_updates_fails_transport_001_only():
    """Batching every pair of a turn's own spontaneous `session/update` notifications into
    single JSON-RPC array lines violates `ACP-TRANSPORT-001` (MANDATORY: ACP has no batches) and
    nothing else: `run_prompt` and the other scans still unpack an array line, so every other id
    gets the verdict it would on separate lines. Same shape as `conforming_full.py`'s own
    self-test above -- run with `--cancel-prompt __hang__` so every CAPABILITY-tier
    `ACP-CANCEL-*` id is actually exercised, not just skipped by a race.
    This fixture advertises only the bare `capabilities.session.prompt.*` baseline (no
    session-management extras, no `authMethods`), so `_SESSION_MGMT_EXTRAS_SKIP_IDS`/
    `_NO_AUTH_SKIP_IDS` legitimately SKIP too, exactly as they do for `conforming.py` itself.
    """
    result = _run_cli(
        FIXTURES_DIR_V2, "emits_batch_updates.py", protocol_version=2, cancel_prompt="__hang__"
    )
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    # This fixture never opts into `_send_rich_turn_updates` either, so the tool_call/plan/
    # terminal-dependent ids legitimately SKIP as they do for `conforming.py`/
    # `vendor_stop_reason.py`/`idle_before_running.py` above. Unlike those three, though, this
    # fixture is built on `AsksPermissionAgent` (it asks for permission mid-turn, same as
    # `conforming_full.py`), so the permission-dependent `ACP-ENUM-203`/`ACP-PATCH-209` PASS
    # here rather than SKIP -- only the tool-call rows (`ACP-PATCH-208`/`210..212`, and
    # `ACP-PERM-203`/`204`/`002`, which need a `tool_call` subject) still SKIP.
    _RICH_TURN_SKIP_IDS = {
        "ACP-PATCH-204",
        "ACP-PATCH-205",
        "ACP-PLAN-003",
        "ACP-PATCH-206",
        "ACP-PATCH-207",
        "ACP-PATCH-208",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-PATCH-212",
        "ACP-PATCH-213",
        "ACP-PATCH-214",
        "ACP-PATCH-215",
        "ACP-PATCH-216",
        "ACP-PERM-203",
        "ACP-PERM-002",
        "ACP-PERM-204",
        "ACP-META-203",
        "ACP-META-204",
    }
    # Like `conforming_full.py`: it never rejects a prompt, and `__hang__` preempts the
    # permission request `ACP-CANCEL-209`/`213` and `ACP-CLOSE-205` need pending.
    expected_skips = (
        _ALWAYS_SKIPPED_IDS
        | _SESSION_MGMT_EXTRAS_SKIP_IDS
        | _NO_AUTH_SKIP_IDS
        | _RICH_TURN_SKIP_IDS
        | _BACKGROUND_SKIP_IDS
        | _RESUME_BACKGROUND_SKIP_IDS | _BACKGROUND_OTHER_SKIP_IDS
        | _ITEM_CANCEL_IDS
        | _CHILD_CONTROL_IDS
        | _CHILD_REPLAY_WITHDRAWAL_IDS
        | {
            "ACP-PROMPT-218",  # the fixture keeps no session across processes
            "ACP-PROMPT-207",
            "ACP-PROMPTCAP-201",  # every prompt capability is advertised
            "ACP-SUGGEST-001",  # the fixture sends no suggestion
            "ACP-SUGGEST-002",
            "ACP-SUGGEST-003",
            "ACP-SUGGEST-004",
            "ACP-RESUME-222",  # the fixture sends no request during a resume
            "ACP-CURSOR-001",  # the fixture announces no cursor
            "ACP-CURSOR-002",
            "ACP-CURSOR-003",
            "ACP-CURSOR-004",
            "ACP-OPTIONS-001",
            "ACP-OPTIONS-002",
            "ACP-OPTIONS-003",
            "ACP-OPTIONS-009",
            "ACP-OPTIONS-004",
            "ACP-OPTIONS-005",
            "ACP-OPTIONS-006",
            "ACP-OPTIONS-007",
            "ACP-OPTIONS-008",
            "ACP-OPTIONS-010",
            "ACP-OPTIONS-011",
            "ACP-OPTIONS-201",
            "ACP-CANCEL-209",
            "ACP-CANCEL-213",
            "ACP-CLOSE-205",
            "ACP-ERROR-204",
            "ACP-SUBAGENT-001",  # no subagent exposed
            "ACP-SUBAGENT-002",
            "ACP-SUBAGENT-003",
            "ACP-SUBAGENT-004",
            "ACP-SUBAGENT-005",
            "ACP-SUBAGENT-006",
            "ACP-SUBAGENT-007",
            "ACP-SUBAGENT-008",
            "ACP-SUBAGENT-009",
            "ACP-SUBAGENT-011",
            "ACP-SUBAGENT-012",
            "ACP-SUBAGENT-013",
            "ACP-SUBAGENT-014",
            "ACP-SUBAGENT-201",
            "ACP-SUBAGENT-205",
            "ACP-SUBAGENT-206",
            "ACP-SUBAGENT-207",
            "ACP-SUBAGENT-018",
            "ACP-SUBAGENT-019",
            "ACP-LIST-004",
        }
    )
    for req_id, status in statuses.items():
        if req_id == "ACP-TRANSPORT-001":
            assert status == "FAIL", f"{req_id} is {status}, expected FAIL:\n{result.stdout}"
        elif req_id in expected_skips:
            assert status == "SKIPPED", f"{req_id} is {status}, expected SKIPPED:\n{result.stdout}"
        else:
            assert status == "PASS", (
                f"{req_id} is {status}, expected PASS for emits_batch_updates.py:\n{result.stdout}"
            )
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
