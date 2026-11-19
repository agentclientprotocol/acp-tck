"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_subagent_controls.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

import pytest

from .._expectations import _CHILD_CONTROL_IDS
from .._runner import FIXTURES_DIR_V2, _fails, _run_cli, _table_statuses


def _child_control_statuses(fixture: str, timeout: str = "1") -> tuple[dict[str, str], str]:
    """Run only `test_subagent_controls.py` against `fixture` with the `__hang__` cancel prompt,
    which is what makes the cancellable children appear."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        fixture,
        protocol_version=2,
        k="test_subagent_controls",
        cancel_prompt="__hang__",
        timeout=timeout,
    )
    statuses = _table_statuses(result.stdout)
    return {r: statuses.get(r) for r in sorted(_CHILD_CONTROL_IDS)}, result.stdout


def test_cancellable_children_pass_the_child_control_rows():
    """`cancellable_subagent.py` runs two children on a `__hang__` turn: one advertises
    `capabilities.cancel` and stops on `session/cancel` for it alone, the other advertises nothing
    but has a tool call and a terminal that advertise `cancel`, which are cancelled with the child's
    `sessionId` and leave it running; cancelling the parent then stops it. All five rows PASS."""
    statuses, stdout = _child_control_statuses("cancellable_subagent.py")
    assert set(statuses.values()) == {"PASS"}, stdout


@pytest.mark.parametrize(
    ("cancel_prompt", "subagent_cancel_prompt", "expected"),
    [
        (None, "__hang__", "PASS"),
        ("__hang__", None, "PASS"),
        ("something else", "__hang__", "PASS"),
        ("__hang__", "something else", "SKIPPED"),
    ],
    ids=["subagent-only", "falls-back-to-cancel-prompt", "overrides-cancel-prompt", "replaces-cancel-prompt"],
)
def test_subagent_cancel_prompt_drives_the_child_control_turn(
    cancel_prompt, subagent_cancel_prompt, expected
):
    """The child-cancel turn sends `--subagent-cancel-prompt`, or `--cancel-prompt` when unset:
    `cancellable_subagent.py` shows cancellable children only for `__hang__`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "cancellable_subagent.py",
        protocol_version=2,
        k="test_subagent_controls",
        cancel_prompt=cancel_prompt,
        subagent_cancel_prompt=subagent_cancel_prompt,
    )
    statuses = _table_statuses(result.stdout)
    for req_id in sorted(_CHILD_CONTROL_IDS):
        assert statuses[req_id] == expected, f"{req_id}:\n{result.stdout}"


def test_subagent_prompt_does_not_drive_the_child_control_turn():
    """`--subagent-prompt __hang__` is not the child-cancel prompt: the rows SKIP."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "cancellable_subagent.py",
        protocol_version=2,
        k="test_subagent_controls",
        subagent_prompt="__hang__",
    )
    statuses = _table_statuses(result.stdout)
    for req_id in sorted(_CHILD_CONTROL_IDS):
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"


def test_child_that_ends_first_leaves_the_child_cancel_rows_nothing_to_judge():
    """`child_ends_before_cancel.py`'s cancellable child finishes (`end_turn`) as the TCK's
    requests arrive, so the `session/cancel` for it finds no running work: a cancel racing with
    ended work is not judged. `-016` and `-017` SKIP, nothing FAILs, and the rest still PASS."""
    statuses, stdout = _child_control_statuses("child_ends_before_cancel.py")
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in ("ACP-SUBAGENT-016", "ACP-SUBAGENT-017") else "PASS"
        assert status == expected, f"{req_id}:\n{stdout}"


def test_child_that_reports_unknown_after_the_cancel_skips_the_confirmation_row(tmp_path):
    """`child_state_unknown_after_cancel.py` can no longer observe the cancelled child and reports
    `unknown` instead of a confirmation, which the docs allow (`subagents.mdx:401`): the
    cancellation is not observable, so `-016` SKIPs (not FAIL) and `-017`, which judges the
    parent, still PASSes."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "child_state_unknown_after_cancel.py",
        protocol_version=2,
        k="test_subagent_controls",
        cancel_prompt="__hang__",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-016"] == "SKIPPED", result.stdout
    assert statuses["ACP-SUBAGENT-017"] == "PASS", result.stdout
    assert "FAIL" not in set(statuses.values()), result.stdout
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    (test,) = by_id["ACP-SUBAGENT-016"]["tests"]
    assert "not observable" in test["message"], test


def test_child_that_reports_unknown_and_then_cancelled_still_confirms():
    """`child_unknown_then_cancelled.py` reports `unknown` and then `idle`/`cancelled` on its own
    session: the later confirmation decides `-016`, which PASSes."""
    statuses, stdout = _child_control_statuses("child_unknown_then_cancelled.py")
    assert set(statuses.values()) == {"PASS"}, stdout


def test_child_cancel_confirmed_only_by_the_mirror_fails_the_confirmation_row():
    """`child_cancel_confirmed_by_mirror_only.py` reports `idle`/`cancelled` only on the parent's
    `subagent_update.state`. The docs name the child's own `state_update` as the confirmation and
    make the mirror a SHOULD (`subagents.mdx:330,400`), so `-016` FAILs and the rest PASS."""
    statuses, stdout = _child_control_statuses("child_cancel_confirmed_by_mirror_only.py")
    for req_id, status in statuses.items():
        assert status == ("FAIL" if req_id == "ACP-SUBAGENT-016" else "PASS"), f"{req_id}:\n{stdout}"


def test_child_that_ignores_cancel_and_ends_later_fails_the_confirmation_row():
    """`child_ignores_cancel_then_ends.py` reports `end_turn` about 1.5 s after the cancel, past the
    race window (`--timeout 4`: 0.5 s) but inside the wait for the confirmation. It is no cancel
    racing with ended work, so `-016` FAILs, `-017` is still judged and PASSes, and so do the
    rest."""
    statuses, stdout = _child_control_statuses("child_ignores_cancel_then_ends.py", timeout="4")
    for req_id, status in statuses.items():
        assert status == ("FAIL" if req_id == "ACP-SUBAGENT-016" else "PASS"), f"{req_id}:\n{stdout}"


def test_item_request_still_in_flight_when_the_cascade_ends_is_judged_not_raced():
    """`child_items_cancellable_at_cascade_end.py` announces its first cancellable child tool call
    and terminal right before the parent's `idle`, so the TCK's requests for them are still
    unanswered when the cascade ends. The TCK waits for the answers instead of reporting the items
    as already final: both item rows PASS (a SKIP would hide a missing response)."""
    statuses, stdout = _child_control_statuses("child_items_cancellable_at_cascade_end.py")
    assert set(statuses.values()) == {"PASS"}, stdout


def test_background_child_announced_after_the_last_snapshot_is_not_judged():
    """`announces_background_child_after_snapshot.py` adds a third child, announced after the
    parent's last `state_update` (no list names it yet, and re-sending the state is only a SHOULD)
    and left running when the parent is cancelled, as background work may be. It cannot be told from
    foreground work, so `-202` is judged on the other two children only and PASSes, as do all the
    rows."""
    statuses, stdout = _child_control_statuses("announces_background_child_after_snapshot.py", timeout="2")
    assert set(statuses.values()) == {"PASS"}, stdout


def test_child_that_asks_after_the_parent_turn_ended_is_still_answered():
    """`child_asks_after_turn_ends.py` ends the parent's turn on the child's cancel and only then
    asks permission for the child's work, confirming `cancelled` only if the TCK answers it
    `cancelled` (the child was cancelled). The request is read after the turn ended: `-016` and
    `-017` PASS, so it was answered, and answered `cancelled` and not allowed. No descendant is left
    for the parent's cascade (`-202` SKIPs)."""
    statuses, stdout = _child_control_statuses("child_asks_after_turn_ends.py", timeout="2")
    for req_id, status in statuses.items():
        assert status == ("SKIPPED" if req_id == "ACP-SUBAGENT-202" else "PASS"), f"{req_id}:\n{stdout}"


def test_child_stop_that_also_stops_a_sibling_is_recorded_not_judged(tmp_path):
    """The per-child `cancel` capability does not prevent the Agent from cancelling its own
    delegated work (`subagents.mdx:398`), which is indistinguishable from a leaked cancel, so
    `child_cancel_stops_sibling_too.py` PASSes `-016`/`-017` and the sibling is only recorded.
    Nothing is left running for the parent's cascade (`-202` SKIPs)."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "child_cancel_stops_sibling_too.py",
        protocol_version=2,
        k="test_subagent_controls",
        cancel_prompt="__hang__",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    for req_id in sorted(_CHILD_CONTROL_IDS):
        expected = "SKIPPED" if req_id == "ACP-SUBAGENT-202" else "PASS"
        assert statuses[req_id] == expected, f"{req_id}:\n{result.stdout}"
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    (test,) = by_id["ACP-SUBAGENT-017"]["tests"]
    assert test["properties"]["acp_tck_cancelled_siblings"].endswith("-child-b"), test


def test_child_control_rows_skip_without_a_cancellable_child():
    """`exposes_subagent.py` exposes a child that advertises no `cancel` and ends with the turn,
    `conforming_full.py` none: nothing cancellable is running, so every row SKIPs."""
    for fixture in ("exposes_subagent.py", "conforming_full.py"):
        statuses, stdout = _child_control_statuses(fixture)
        assert set(statuses.values()) == {"SKIPPED"}, f"{fixture}:\n{stdout}"


@pytest.mark.parametrize(
    ("fixture", "failing", "skipped"),
    [
        ("child_cancel_ignored.py", "ACP-SUBAGENT-016", set()),
        ("child_cancel_cancels_parent.py", "ACP-SUBAGENT-017", {"ACP-SUBAGENT-202"}),
        ("parent_cancel_leaves_child_running.py", "ACP-SUBAGENT-202", set()),
        ("child_tool_call_cancel_errors.py", "ACP-TOOLCANCEL-203", set()),
        ("child_terminal_cancel_never_exits.py", "ACP-TERMCANCEL-203", set()),
    ],
)
def test_child_control_defect_fails_its_row_only(fixture: str, failing: str, skipped: set[str]):
    """Each defect trips its own row: a child that ignores its cancel fails `-016`; a cancel that
    also ends the parent's turn fails `-017` (the parent's turn is over before the TCK cancels it,
    so `-202` SKIPs); a parent cancel that leaves the child it waits on running fails `-202`; a
    child's item whose cancel errors, or is accepted but never confirmed, fails its item row.
    Every other row PASSes, except where the same defect left it nothing to judge."""
    statuses, stdout = _child_control_statuses(fixture)
    for req_id, status in statuses.items():
        expected = "FAIL" if req_id == failing else "SKIPPED" if req_id in skipped else "PASS"
        assert status == expected, f"{req_id}:\n{stdout}"


def _withdrawal_statuses(fixture: str) -> tuple[dict[str, str], str]:
    """`_child_control_statuses` plus `ACP-SUBAGENT-204`, judged over the same driven turn."""
    result = _run_cli(
        FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_subagent_controls", cancel_prompt="__hang__"
    )
    statuses = _table_statuses(result.stdout)
    return {r: statuses.get(r) for r in sorted(_CHILD_CONTROL_IDS | {"ACP-SUBAGENT-204"})}, result.stdout


def test_stopped_children_withdraw_their_held_permission_requests():
    """`cancellable_subagent_asks.py`'s children each ask for permission; the TCK holds the
    requests, and each child withdraws its own when it is stopped (child A by its cancel, child B by
    the parent's cascade): `ACP-SUBAGENT-204` PASSes, as do the child control rows."""
    statuses, stdout = _withdrawal_statuses("cancellable_subagent_asks.py")
    assert set(statuses.values()) == {"PASS"}, stdout


def test_withdrawal_row_skips_without_a_held_child_request():
    """`cancellable_subagent.py`'s children never ask for permission: nothing is held, so
    `ACP-SUBAGENT-204` SKIPs while the child control rows PASS."""
    statuses, stdout = _withdrawal_statuses("cancellable_subagent.py")
    for req_id, status in statuses.items():
        assert status == ("SKIPPED" if req_id == "ACP-SUBAGENT-204" else "PASS"), f"{req_id}:\n{stdout}"


@pytest.mark.parametrize(
    "fixture", ["child_cancel_keeps_permission_open.py", "child_cancel_waits_for_permission.py"]
)
def test_withdrawal_defects_fail_subagent_204_only(fixture):
    """A stopped child that leaves its request open, or one that stops only once the TCK answers
    its held request at `timeout / 2` (it waited for it), FAILs `ACP-SUBAGENT-204`. The waiting
    child still confirms in time, so `ACP-SUBAGENT-016` and the other child control rows PASS."""
    statuses, stdout = _withdrawal_statuses(fixture)
    for req_id, status in statuses.items():
        assert status == ("FAIL" if req_id == "ACP-SUBAGENT-204" else "PASS"), f"{req_id}:\n{stdout}"


def test_close_keeps_child_permission_open_fails_subagent_203_only():
    """`session/close` is answered while the child's permission requests are still pending and
    unwithdrawn: only `ACP-SUBAGENT-203` FAILs, over the whole run."""
    result = _run_cli(FIXTURES_DIR_V2, "close_keeps_child_permission_open.py", protocol_version=2)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-SUBAGENT-203"}, result.stdout
    assert statuses["ACP-CLOSE-205"] == "SKIPPED", result.stdout
