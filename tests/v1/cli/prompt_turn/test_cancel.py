"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_cancel.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_asks_permission_closable_agent_also_exercises_cancelled_outcome():
    """Same fixture as above, driven through `test_cancel.py` instead: its permission request
    also arrives after `session/cancel` fires (same post-update-peek delay), so `run_prompt`
    answers it `{"outcome": {"outcome": "cancelled"}}` -- the one branch of `run_prompt`'s
    permission-answering logic that `asks_permission.py` alone never exercises."""
    result = _run_cli(
        "asks_permission_closable.py", timeout="5", k="cancel", cancel_prompt="__hang__"
    )
    # Exit code not asserted: a `-k`-scoped run necessarily leaves every MANDATORY requirement
    # NOT_TESTED, which by itself forces a non-conformant (nonzero) verdict regardless of these
    # two ids' own status (see `test_load_returns_null_fails_load_003_advisory_only`).
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CANCEL-001") == "PASS", f"expected PASS:\n{result.stdout}"
    assert statuses.get("ACP-CANCEL-002") == "PASS", f"expected PASS:\n{result.stdout}"


def test_hangs_until_cancel_agent_passes_cancel_requirements():
    """`hangs_until_cancel.py` withholds its response on *every* prompt until `session/cancel`
    arrives, which is deliberately incompatible with the non-cancelling prompt tests
    (ACP-PROMPT-*, ACP-SCHEMA-001, ACP-TRANSPORT-*) -- those would time out waiting for a
    response the fixture never sends unprompted. This self-test scopes the run to the cancel
    tests with `-k`, which is the only way to exercise this fixture meaningfully.

    The overall exit code is *not* asserted here: the exit code reflects the four-status
    verdict over the whole registry, and a `-k`-scoped run necessarily leaves every
    other MANDATORY requirement NOT_TESTED (counted as a verdict failure by design) -- that says
    nothing about whether *this* fixture's cancel handling is correct, which is what this test
    checks via the per-requirement table."""
    result = _run_cli("hangs_until_cancel.py", k="cancel")

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CANCEL-001") == "PASS", result.stdout + result.stderr
    assert statuses.get("ACP-CANCEL-002") == "PASS", result.stdout + result.stderr


def test_cancel_returns_error_fails_cancel_001():
    """`cancel_returns_error.py` resolves a cancelled turn with a JSON-RPC error instead of a
    successful `cancelled` result. Scoped with `-k "cancel"` for the same reason as the
    `hangs_until_cancel.py` self-test above (the fixture hangs on every prompt)."""
    result = _run_cli("cancel_returns_error.py", k="cancel")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CANCEL-001") == "FAIL", result.stdout


def test_cancel_wrong_stop_reason_fails_cancel_001_only():
    """`cancel_wrong_stop_reason.py` resolves a cancelled turn successfully but with
    `stopReason: "end_turn"` instead of `"cancelled"` -- ACP-CANCEL-001 FAILs, but ACP-CANCEL-002
    (no update after the response) is unaffected and still PASSes. Scoped with `-k "cancel"` for
    the same reason as the `hangs_until_cancel.py` self-test above. Uses a longer `--timeout`
    since the fixture deliberately sleeps 1.2s after `session/cancel` before answering, to stay
    outside the TCK's 1.0s "was this actually exercised" race window (see the fixture's
    docstring)."""
    result = _run_cli("cancel_wrong_stop_reason.py", k="cancel", timeout="5")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CANCEL-001") == "FAIL", result.stdout
    assert statuses.get("ACP-CANCEL-002") == "PASS", result.stdout


def test_update_after_response_fails_cancel_002_only():
    """`update_after_response.py` correctly resolves a cancelled turn with `stopReason:
    "cancelled"` (ACP-CANCEL-001 PASSes) but then sends one more `session/update` afterwards,
    which ACP-CANCEL-002 catches. Scoped with `-k "cancel"` for the same reason as the
    `hangs_until_cancel.py` self-test above."""
    result = _run_cli("update_after_response.py", k="cancel")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CANCEL-001") == "PASS", result.stdout
    assert statuses.get("ACP-CANCEL-002") == "FAIL", result.stdout


def test_late_state_updates_pass_cancel_002_and_load_002():
    """`late_state_updates.py` sends `session_info_update` after each prompt response (including
    a cancelled one) and `available_commands_update` after each load response. Those kinds are
    allowed outside a turn, so ACP-CANCEL-002/LOAD-002 PASS and the run stays CONFORMANT."""
    result = _run_cli("late_state_updates.py", cancel_prompt="__hang__")
    assert result.returncode == 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    for req_id in ("ACP-CANCEL-001", "ACP-CANCEL-002", "ACP-LOAD-001", "ACP-LOAD-002"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"
