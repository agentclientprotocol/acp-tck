"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_subagent_controls.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

import pytest

from .._expectations import _SUBAGENT_CANCEL_IDS
from .._runner import _run_cli, _table_statuses


_CHILD_STOP_K = "test_subagent_controls"


def _child_stop_statuses(fixture: str, timeout: str = "1") -> tuple[dict[str, str], str]:
    """Run only `test_subagent_controls.py` against `fixture` with the `__hang__` cancel prompt,
    which is what makes the cancellable child appear."""
    result = _run_cli(fixture, k=_CHILD_STOP_K, cancel_prompt="__hang__", timeout=timeout)
    statuses = _table_statuses(result.stdout)
    return {r: statuses.get(r) for r in sorted(_SUBAGENT_CANCEL_IDS)}, result.stdout


def test_cancellable_child_passes_the_child_cancel_rows():
    """`cancellable_subagent.py` advertises `capabilities.cancel` on a running child, stops it on
    `session/cancel` for it (idle/cancelled on the parent snapshot) and leaves the parent and the
    sibling running: both rows PASS."""
    statuses, stdout = _child_stop_statuses("cancellable_subagent.py")
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
def test_subagent_cancel_prompt_drives_the_child_cancel_turn(
    cancel_prompt, subagent_cancel_prompt, expected
):
    """The child-cancel turn sends `--subagent-cancel-prompt`, or `--cancel-prompt` when unset:
    `cancellable_subagent.py` shows a cancellable child only for `__hang__`."""
    result = _run_cli(
        "cancellable_subagent.py",
        k=_CHILD_STOP_K,
        cancel_prompt=cancel_prompt,
        subagent_cancel_prompt=subagent_cancel_prompt,
    )
    statuses = _table_statuses(result.stdout)
    for req_id in sorted(_SUBAGENT_CANCEL_IDS):
        assert statuses[req_id] == expected, f"{req_id}:\n{result.stdout}"


def test_subagent_prompt_does_not_drive_the_child_cancel_turn():
    """`--subagent-prompt __hang__` is not the child-cancel prompt: the rows SKIP."""
    result = _run_cli("cancellable_subagent.py", k=_CHILD_STOP_K, subagent_prompt="__hang__")
    statuses = _table_statuses(result.stdout)
    for req_id in sorted(_SUBAGENT_CANCEL_IDS):
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"


def test_child_that_ends_first_leaves_the_child_cancel_rows_nothing_to_judge():
    """`child_ends_before_cancel.py`'s child finishes (`end_turn`) as the cancel arrives: a cancel
    racing with ended work is not judged, so both rows SKIP and nothing FAILs."""
    statuses, stdout = _child_stop_statuses("child_ends_before_cancel.py")
    assert set(statuses.values()) == {"SKIPPED"}, stdout
    assert "FAIL" not in set(_table_statuses(stdout).values()), stdout


def test_child_that_asks_after_the_parent_turn_ended_is_still_answered():
    """`child_asks_after_turn_ends.py` ends the parent's turn on the child's cancel and only then
    asks permission for the child's work, confirming `cancelled` only if the TCK answers it
    `cancelled` (the child was cancelled). The request is read after the turn ended: both rows
    PASS, so it was answered, and answered `cancelled` and not allowed."""
    statuses, stdout = _child_stop_statuses("child_asks_after_turn_ends.py")
    assert set(statuses.values()) == {"PASS"}, stdout


def test_child_that_ignores_cancel_and_ends_later_fails_the_confirmation_row():
    """`child_ignores_cancel_then_ends.py` reports `end_turn` about 1.5 s after the cancel, past the
    race window (`--timeout 4`: 0.5 s) but inside the wait for the confirmation. It is no
    cancel racing with ended work, so `-016` FAILs, and `-017` is still judged and PASSes."""
    statuses, stdout = _child_stop_statuses("child_ignores_cancel_then_ends.py", timeout="4")
    assert statuses == {"ACP-SUBAGENT-016": "FAIL", "ACP-SUBAGENT-017": "PASS"}, stdout


def test_child_stop_that_also_stops_a_sibling_is_recorded_not_judged(tmp_path):
    """The per-child `cancel` capability does not prevent the Agent from cancelling its own
    delegated work (`subagents.mdx:447`), which is indistinguishable from a leaked cancel, so
    `child_cancel_stops_sibling_too.py` PASSes both rows and the sibling is only recorded."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "child_cancel_stops_sibling_too.py",
        k=_CHILD_STOP_K,
        cancel_prompt="__hang__",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-016"] == statuses["ACP-SUBAGENT-017"] == "PASS", result.stdout
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    (test,) = by_id["ACP-SUBAGENT-017"]["tests"]
    assert test["properties"]["acp_tck_cancelled_siblings"].endswith("-child-b"), test


def test_child_that_reports_unknown_after_the_cancel_skips_the_confirmation_row(tmp_path):
    """`child_state_unknown_after_cancel.py` can no longer observe the cancelled child and reports
    `unknown` instead of a confirmation, which the docs allow: the cancellation is not observable,
    so `-016` SKIPs (not FAIL) and `-017`, which judges the parent, still PASSes."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "child_state_unknown_after_cancel.py",
        k=_CHILD_STOP_K,
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
    """`child_unknown_then_cancelled.py` reports `unknown` and then `idle`/`cancelled`: the later
    confirmation decides `-016`, which PASSes."""
    statuses, stdout = _child_stop_statuses("child_unknown_then_cancelled.py")
    assert set(statuses.values()) == {"PASS"}, stdout


def test_child_cancel_rows_skip_without_a_cancellable_child():
    """`exposes_subagent.py` exposes a child that advertises no `cancel`, and `conforming.py` none:
    nothing is cancelled, so both rows SKIP."""
    for fixture in ("exposes_subagent.py", "conforming.py"):
        statuses, stdout = _child_stop_statuses(fixture)
        assert set(statuses.values()) == {"SKIPPED"}, f"{fixture}:\n{stdout}"


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("child_cancel_ignored.py", "ACP-SUBAGENT-016"),
        ("child_cancel_cancels_parent.py", "ACP-SUBAGENT-017"),
    ],
)
def test_child_cancel_defect_fails_its_row_only(fixture: str, failing: str):
    """Each defect trips its own row: a child that ignores its cancel fails the confirmation row
    (`-016`); a cancel that also ends the parent's turn fails `-017`, whose child still confirmed
    its own cancellation."""
    statuses, stdout = _child_stop_statuses(fixture)
    for req_id, status in statuses.items():
        assert status == ("FAIL" if req_id == failing else "PASS"), f"{req_id}:\n{stdout}"
