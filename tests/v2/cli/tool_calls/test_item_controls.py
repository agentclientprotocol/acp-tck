"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_item_controls.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

import pytest

from .._expectations import (
    _ITEM_CANCEL_IDS,
    _REPEAT_CANCEL_IDS,
    _STALE_CANCEL_IDS,
    _UNCANCELLABLE_CANCEL_IDS,
    _UNKNOWN_CANCEL_IDS,
)
from .._runner import FIXTURES_DIR_V2, _run_cli, _table_statuses


def _item_cancel_run(
    fixture: str, tmp_path, *, cancel_prompt: str | None = "__hang__", timeout: str = "1"
) -> tuple[dict[str, str], dict[str, dict], str]:
    """Run only `test_item_controls.py` against `fixture` (by default with the `__hang__` cancel
    prompt, which is what makes a fixture's `cancellable_work` items appear): the item-cancel rows'
    statuses, every row's report entry by id, and stdout."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        fixture,
        protocol_version=2,
        k="test_item_controls",
        cancel_prompt=cancel_prompt,
        timeout=timeout,
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    return {r: statuses.get(r) for r in sorted(_ITEM_CANCEL_IDS)}, by_id, result.stdout


def _item_cancel_statuses(fixture: str, tmp_path) -> tuple[dict[str, str], str]:
    statuses, _by_id, stdout = _item_cancel_run(fixture, tmp_path)
    return statuses, stdout


def _skip_message(by_id: dict[str, dict], req_id: str) -> str:
    (test,) = by_id[req_id]["tests"]
    return test["message"]


def test_cancellable_items_pass_the_cancel_rows(tmp_path):
    """`conforming_full.py` advertises `capabilities.cancel` on a tool call and a terminal that
    stay open on a `__hang__` turn and implements both cancel methods. It stops advertising `cancel`
    once they are final, so no already-final request is made: `-201/202` PASS, `-204/205` SKIP.
    It answers an unknown id, and its live items that advertise no `cancel`, `-32602`: `-206-209`
    PASS. It answers a repeat request for the cancelled items `-32602` too, so `-210/211` PASS."""
    statuses, stdout = _item_cancel_statuses("conforming_full.py", tmp_path)
    for req_id, status in statuses.items():
        assert status == ("SKIPPED" if req_id in _STALE_CANCEL_IDS else "PASS"), f"{req_id}:\n{stdout}"


def test_agent_that_keeps_advertising_cancel_gets_a_further_request(tmp_path):
    """`keeps_cancel_after_final.py` leaves `cancel` advertised on its final items (an
    `ACP-PATCH-212` finding) and answers the further requests `-32602`, as tool-calls.mdx:459,605
    say: the twelve rows up to `-207` PASS (the unknown-id requests get `-32602` too). It has no
    live item without `cancel`, so the not-cancellable rows SKIP although the gate holds."""
    statuses, by_id, stdout = _item_cancel_run("keeps_cancel_after_final.py", tmp_path)
    for req_id, status in statuses.items():
        skipped = _UNCANCELLABLE_CANCEL_IDS | _REPEAT_CANCEL_IDS
        assert status == ("SKIPPED" if req_id in skipped else "PASS"), f"{req_id}:\n{stdout}"
    for req_id in ("ACP-TOOLCANCEL-208", "ACP-TERMCANCEL-208"):
        assert "was live without advertising capabilities.cancel" in _skip_message(by_id, req_id), (
            f"{req_id}:\n{stdout}"
        )
    # The confirmed items still advertise `cancel`, so the already-final request is their repeat.
    for req_id in ("ACP-TOOLCANCEL-210", "ACP-TERMCANCEL-210"):
        assert "still advertises capabilities.cancel" in _skip_message(by_id, req_id), f"{req_id}:\n{stdout}"


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "accepts_cancel_for_final_tool_call.py",
            {"ACP-TOOLCANCEL-204": "FAIL", "ACP-TOOLCANCEL-205": "SKIPPED"},
        ),
        (
            "accepts_cancel_for_exited_terminal.py",
            {"ACP-TERMCANCEL-204": "FAIL", "ACP-TERMCANCEL-205": "SKIPPED"},
        ),
        ("final_tool_call_cancel_wrong_code.py", {"ACP-TOOLCANCEL-205": "FAIL"}),
        ("exited_terminal_cancel_wrong_code.py", {"ACP-TERMCANCEL-205": "FAIL"}),
    ],
)
def test_already_final_cancel_defect_fails_its_row_only(fixture: str, expected: dict[str, str], tmp_path):
    """An accepted request for an already-final item fails `-204` (and leaves the code row nothing
    to judge); a rejection with the wrong code fails only the ADVISORY `-205`. The other kind of
    item, and the happy-path rows, still PASS; nothing is live without `cancel`, so `-208/209`
    SKIP."""
    statuses, stdout = _item_cancel_statuses(fixture, tmp_path)
    for req_id, status in statuses.items():
        default = "SKIPPED" if req_id in _UNCANCELLABLE_CANCEL_IDS | _REPEAT_CANCEL_IDS else "PASS"
        assert status == expected.get(req_id, default), f"{req_id}:\n{stdout}"


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "repeat_tool_cancel_accepted.py",
            {"ACP-TOOLCANCEL-210": "FAIL", "ACP-TOOLCANCEL-211": "SKIPPED"},
        ),
        (
            "repeat_terminal_cancel_accepted.py",
            {"ACP-TERMCANCEL-210": "FAIL", "ACP-TERMCANCEL-211": "SKIPPED"},
        ),
    ],
)
def test_accepted_repeat_cancel_fails_its_row_only(fixture: str, expected: dict[str, str], tmp_path):
    """A request sent again for an item whose cancel was accepted and which is final, with
    `capabilities` cleared, is answered with a result: fails `-210` (and leaves the code row
    nothing to judge). The other kind of item and the happy-path rows still PASS (the repeat rows
    of `conforming_full.py` PASS, so the other kind's `-210/211` do too), and the already-final
    rows SKIP: nothing is final while still advertising `cancel`."""
    statuses, stdout = _item_cancel_statuses(fixture, tmp_path)
    for req_id, status in statuses.items():
        default = "SKIPPED" if req_id in _STALE_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS else "PASS"
        assert status == expected.get(req_id, default), f"{req_id}:\n{stdout}"


def test_items_that_finish_first_leave_the_cancel_rows_nothing_to_judge(tmp_path):
    """`completes_before_cancel.py` reports its cancellable items already final, so nothing may
    be cancelled and a `-32602` would be right: every row SKIPs and nothing FAILs. The items did
    advertise `cancel`, so the unknown-id requests are sent whether or not the driver saw them
    live, and `-206/207` PASS."""
    statuses, stdout = _item_cancel_statuses("completes_before_cancel.py", tmp_path)
    for req_id, status in statuses.items():
        assert status == ("PASS" if req_id in _UNKNOWN_CANCEL_IDS else "SKIPPED"), f"{req_id}:\n{stdout}"
    assert "FAIL" not in {s for s in _table_statuses(stdout).values()}, stdout


@pytest.mark.parametrize(
    "fixture",
    [
        "races_cancel_with_completion.py",
        "withdraws_cancel_on_request.py",
        "finalizes_after_rejecting_cancel.py",
    ],
)
def test_legitimate_invalid_params_is_not_a_rejection(fixture: str, tmp_path):
    """A `-32602` is the documented answer for an item that is already final or not cancellable
    (tool-calls.mdx:459,605). It is not judged when the item's final update came first
    (`races_cancel_with_completion.py`), arrives right after it
    (`finalizes_after_rejecting_cancel.py`), or the agent stopped advertising `cancel`
    (`withdraws_cancel_on_request.py`). Every row SKIPs for the `raced` reason, never for "nothing
    advertised", and nothing FAILs. The unknown-id rows are judged apart from the race and PASS.
    `withdraws_cancel_on_request.py` leaves its items live without `cancel`, but the TCK already
    sent them the main request, so the not-cancellable request does not repeat it and `-208/209`
    SKIP too."""
    statuses, by_id, stdout = _item_cancel_run(fixture, tmp_path)
    for req_id, status in statuses.items():
        assert status == ("PASS" if req_id in _UNKNOWN_CANCEL_IDS else "SKIPPED"), f"{req_id}:\n{stdout}"
    for req_id in ("ACP-TOOLCANCEL-201", "ACP-TERMCANCEL-201"):
        assert "had stopped advertising it" in _skip_message(by_id, req_id), f"{req_id}:\n{stdout}"
    if fixture == "withdraws_cancel_on_request.py":
        for req_id in ("ACP-TOOLCANCEL-208", "ACP-TERMCANCEL-208"):
            assert "had already been sent the main" in _skip_message(by_id, req_id), f"{req_id}:\n{stdout}"


def test_missing_cancel_methods_are_not_hidden_by_the_race_excuse(tmp_path):
    """`cancel_missing_after_completion.py` answers `tool_call/cancel` and `terminal/cancel`
    `-32601` after its items finished. Only `-32602` is the documented answer for an already-final
    item, so the race excuse does not apply: both acceptance rows FAIL, their confirmation rows
    SKIP. The unknown-id requests get the same `-32601`: rejected (`-206` PASS), but with the wrong
    code, so the ADVISORY `-207` rows FAIL."""
    statuses, stdout = _item_cancel_statuses("cancel_missing_after_completion.py", tmp_path)
    expected = {
        "ACP-TOOLCANCEL-201": "FAIL",
        "ACP-TERMCANCEL-201": "FAIL",
        "ACP-TOOLCANCEL-206": "PASS",
        "ACP-TERMCANCEL-206": "PASS",
        "ACP-TOOLCANCEL-207": "FAIL",
        "ACP-TERMCANCEL-207": "FAIL",
    }
    for req_id, status in statuses.items():
        assert status == expected.get(req_id, "SKIPPED"), f"{req_id}:\n{stdout}"


def test_background_item_cancel_is_confirmed_after_a_permission_request_is_answered(tmp_path):
    """`confirms_cancel_after_permission_answer.py` announces a cancellable background tool call
    after the turn's idle and asks permission before it confirms the cancel. The TCK still reads
    after the idle and answers that request, so the confirmation arrives: `-201/202` for the tool
    call PASS, nothing FAILs, and the terminal rows SKIP."""
    statuses, _by_id, stdout = _item_cancel_run(
        "confirms_cancel_after_permission_answer.py", tmp_path, cancel_prompt=None
    )
    assert statuses["ACP-TOOLCANCEL-201"] == "PASS", stdout
    assert statuses["ACP-TOOLCANCEL-202"] == "PASS", stdout
    assert "FAIL" not in set(statuses.values()), stdout


def test_long_streaming_turn_does_not_fail_the_cancel_rows(tmp_path):
    """`streams_long_turn.py` streams message chunks for about 4 s and advertises nothing
    cancellable. With `--timeout 1` the turn outlasts the per-response timeout, which the TCK's own
    overall deadline once reported as the agent's failure on every row: now every row SKIPs and
    nothing FAILs. Nothing advertised `cancel`, so no unknown-id request was sent either."""
    statuses, by_id, stdout = _item_cancel_run("streams_long_turn.py", tmp_path, cancel_prompt=None)
    assert set(statuses.values()) == {"SKIPPED"}, stdout
    for req_id in ("ACP-TOOLCANCEL-206", "ACP-TERMCANCEL-206"):
        assert "advertised capabilities.cancel during the driven turn" in _skip_message(by_id, req_id), (
            f"{req_id}:\n{stdout}"
        )


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "accepts_cancel_for_unknown_tool_call.py",
            {"ACP-TOOLCANCEL-206": "FAIL", "ACP-TOOLCANCEL-207": "SKIPPED"},
        ),
        (
            "accepts_cancel_for_unknown_terminal.py",
            {"ACP-TERMCANCEL-206": "FAIL", "ACP-TERMCANCEL-207": "SKIPPED"},
        ),
        ("unknown_tool_call_cancel_wrong_code.py", {"ACP-TOOLCANCEL-207": "FAIL"}),
        ("unknown_terminal_cancel_wrong_code.py", {"ACP-TERMCANCEL-207": "FAIL"}),
    ],
)
def test_unknown_id_cancel_defect_fails_its_row_only(fixture: str, expected: dict[str, str], tmp_path):
    """A result for an id no update announced fails `-206` (and leaves the code row nothing to
    judge); a rejection with the wrong code fails only the ADVISORY `-207`. The other kind of item
    and the happy-path rows still PASS, and the already-final rows SKIP (these items stop
    advertising `cancel`), as do the not-cancellable rows (nothing is live without `cancel`)."""
    statuses, stdout = _item_cancel_statuses(fixture, tmp_path)
    for req_id, status in statuses.items():
        default = "SKIPPED" if req_id in _STALE_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS else "PASS"
        assert status == expected.get(req_id, default), f"{req_id}:\n{stdout}"


# A kind whose main request was not accepted and confirmed leaves its repeat rows nothing to judge.
_NO_TOOL_REPEAT = {"ACP-TOOLCANCEL-210": "SKIPPED", "ACP-TOOLCANCEL-211": "SKIPPED"}
_NO_TERM_REPEAT = {"ACP-TERMCANCEL-210": "SKIPPED", "ACP-TERMCANCEL-211": "SKIPPED"}


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "tool_call_cancel_errors.py",
            {"ACP-TOOLCANCEL-201": "FAIL", "ACP-TOOLCANCEL-202": "SKIPPED", **_NO_TOOL_REPEAT},
        ),
        ("tool_call_cancel_never_final.py", {"ACP-TOOLCANCEL-202": "FAIL", **_NO_TOOL_REPEAT}),
        (
            "terminal_cancel_errors.py",
            {"ACP-TERMCANCEL-201": "FAIL", "ACP-TERMCANCEL-202": "SKIPPED", **_NO_TERM_REPEAT},
        ),
        ("terminal_cancel_never_exits.py", {"ACP-TERMCANCEL-202": "FAIL", **_NO_TERM_REPEAT}),
    ],
)
def test_item_cancel_defect_fails_its_row_only(fixture: str, expected: dict[str, str], tmp_path):
    """Each defect trips its own row: an error for an advertised, running item (`-32603`, or a
    `-32602` for a terminal that neither exits nor stops advertising `cancel`) fails the
    acceptance row (and leaves the confirmation row nothing to judge); an accepted cancel with no
    final update fails the confirmation row. The other kind of item still PASSes, and the
    already-final rows SKIP (these items stop advertising `cancel`), as do the not-cancellable rows
    (nothing is live without `cancel`)."""
    statuses, stdout = _item_cancel_statuses(fixture, tmp_path)
    for req_id, status in statuses.items():
        default = "SKIPPED" if req_id in _STALE_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS else "PASS"
        assert status == expected.get(req_id, default), f"{req_id}:\n{stdout}"


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        (
            "accepts_cancel_for_uncancellable_tool_call.py",
            {"ACP-TOOLCANCEL-208": "FAIL", "ACP-TOOLCANCEL-209": "SKIPPED"},
        ),
        (
            "accepts_cancel_for_uncancellable_terminal.py",
            {"ACP-TERMCANCEL-208": "FAIL", "ACP-TERMCANCEL-209": "SKIPPED"},
        ),
        ("uncancellable_tool_call_cancel_wrong_code.py", {"ACP-TOOLCANCEL-209": "FAIL"}),
        ("uncancellable_terminal_cancel_wrong_code.py", {"ACP-TERMCANCEL-209": "FAIL"}),
        # The item finishes before the `-32602` response: still the right answer, no false FAIL.
        ("uncancellable_finishes_first.py", {}),
    ],
)
def test_uncancellable_cancel_defect_fails_its_row_only(fixture: str, expected: dict[str, str], tmp_path):
    """A result for a live item that advertises no `cancel` fails `-208` (and leaves the code row
    nothing to judge); a rejection with the wrong code fails only the ADVISORY `-209`. The other
    kind of item and the happy-path rows still PASS, and the already-final rows SKIP (these items
    stop advertising `cancel`)."""
    statuses, stdout = _item_cancel_statuses(fixture, tmp_path)
    for req_id, status in statuses.items():
        default = "SKIPPED" if req_id in _STALE_CANCEL_IDS else "PASS"
        assert status == expected.get(req_id, default), f"{req_id}:\n{stdout}"


def test_item_that_becomes_cancellable_as_the_request_crosses_is_a_race(tmp_path):
    """`uncancellable_becomes_cancellable.py` advertises `cancel` on its not-cancellable items when
    the request arrives (the tool call before the response, the terminal just after it) and accepts.
    The result is legitimate, so `-208` SKIPs for the race rather than FAILing, `-209` SKIPs, and
    the other rows are judged as for `conforming_full.py`."""
    statuses, by_id, stdout = _item_cancel_run("uncancellable_becomes_cancellable.py", tmp_path)
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in _STALE_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS else "PASS"
        assert status == expected, f"{req_id}:\n{stdout}"
    for req_id in ("ACP-TOOLCANCEL-208", "ACP-TERMCANCEL-208"):
        assert "started advertising capabilities.cancel as" in _skip_message(by_id, req_id), (
            f"{req_id}:\n{stdout}"
        )


def test_main_request_does_not_repeat_the_not_cancellable_request(tmp_path):
    """`rejects_repeat_cancel_while_cancelling.py` advertises `cancel` on its not-cancellable items
    when the request for them arrives, accepts, and answers a repeat request for them `-32602`
    while they stay live and advertised; then it starts a new cancellable item. The main request
    goes to the new item, not to the one the not-cancellable request already went to, so `-201/202`
    PASS rather than judging the TCK's own repeat request, `-208/209` SKIP for the race, and
    nothing FAILs."""
    statuses, by_id, stdout = _item_cancel_run("rejects_repeat_cancel_while_cancelling.py", tmp_path)
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in _STALE_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS else "PASS"
        assert status == expected, f"{req_id}:\n{stdout}"
    for req_id in ("ACP-TOOLCANCEL-208", "ACP-TERMCANCEL-208"):
        assert "started advertising capabilities.cancel as" in _skip_message(by_id, req_id), (
            f"{req_id}:\n{stdout}"
        )


def test_main_request_skips_when_every_live_item_was_already_probed(tmp_path):
    """`rejects_repeat_cancel_without_replacement.py` is `rejects_repeat_cancel_while_cancelling.py`
    without the new cancellable item. The only live item that advertises `cancel` is the one the
    not-cancellable request already went to, which the main request does not repeat: `-201/202`
    SKIP and say so, not that nothing advertised `cancel`. Nothing FAILs."""
    statuses, by_id, stdout = _item_cancel_run("rejects_repeat_cancel_without_replacement.py", tmp_path)
    for req_id, status in statuses.items():
        expected = "PASS" if req_id in _UNKNOWN_CANCEL_IDS else "SKIPPED"
        assert status == expected, f"{req_id}:\n{stdout}"
    for req_id in (
        "ACP-TOOLCANCEL-201",
        "ACP-TOOLCANCEL-202",
        "ACP-TERMCANCEL-201",
        "ACP-TERMCANCEL-202",
    ):
        message = _skip_message(by_id, req_id)
        assert "had already been sent a further cancel request" in message, f"{req_id}:\n{stdout}"
        assert "no tool call advertised" not in message, f"{req_id}:\n{stdout}"


def test_not_cancellable_request_does_not_repeat_the_main_request(tmp_path):
    """`cancel_never_final_accepts_repeat.py` accepts the main request, stops advertising `cancel`
    and gives no final update in time, and would accept a repeat request too. The cancelled item is
    then live without `cancel`, but the not-cancellable request does not go to it, so the one defect
    fails `-202` only: `-208/209` SKIP for want of a target."""
    statuses, by_id, stdout = _item_cancel_run("cancel_never_final_accepts_repeat.py", tmp_path)
    expected = {"ACP-TOOLCANCEL-202": "FAIL", "ACP-TERMCANCEL-202": "FAIL"}
    for req_id, status in statuses.items():
        skipped = _STALE_CANCEL_IDS | _UNCANCELLABLE_CANCEL_IDS | _REPEAT_CANCEL_IDS
        default = "SKIPPED" if req_id in skipped else "PASS"
        assert status == expected.get(req_id, default), f"{req_id}:\n{stdout}"
    for req_id in ("ACP-TOOLCANCEL-208", "ACP-TERMCANCEL-208"):
        message = _skip_message(by_id, req_id)
        assert "had already been sent the main" in message, f"{req_id}:\n{stdout}"
        assert "which this row does not repeat" in message, f"{req_id}:\n{stdout}"


def test_uncancellable_items_are_not_probed_without_the_gate(tmp_path):
    """`uncancellable_work_only.py` keeps a tool call and a terminal live without `cancel` but
    never advertises `cancel`, so it may not implement either method (error.mdx:44): no request is
    sent, every row SKIPs, and `-208` names the gate."""
    statuses, by_id, stdout = _item_cancel_run("uncancellable_work_only.py", tmp_path)
    assert set(statuses.values()) == {"SKIPPED"}, stdout
    for req_id in ("ACP-TOOLCANCEL-208", "ACP-TERMCANCEL-208"):
        assert "advertised capabilities.cancel during the driven turn" in _skip_message(by_id, req_id), (
            f"{req_id}:\n{stdout}"
        )
