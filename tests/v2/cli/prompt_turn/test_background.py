"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_background.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

import pytest

from .._expectations import _ALL_IDS, _BACKGROUND_SKIP_IDS, _CONFORMING_EXPECTED_SKIPS
from .._runner import (
    FIXTURES_DIR_V2,
    _TOOL_CALL_K,
    _fails,
    _fails_for,
    _full_run,
    _recorded,
    _run_cli,
    _table_statuses,
)


def test_reports_background_work_agent_passes_everything():
    """`reports_background_work.py` is `conforming.py` plus a `background` list on every
    `state_update` and one background tool call per turn, so `_BACKGROUND_SKIP_IDS` PASS. That
    tool call's two `tool_call_update`s also give `ACP-PATCH-204`/`208`/`210`/`211` something to
    judge, so they PASS too; every other id matches `conforming.py`."""
    result = _run_cli(FIXTURES_DIR_V2, "reports_background_work.py", protocol_version=2)
    assert result.returncode == 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS, f"requirement table missing/extra ids: {result.stdout}"
    exercised = _BACKGROUND_SKIP_IDS | {
        "ACP-PATCH-204",
        "ACP-PATCH-208",
        "ACP-PATCH-210",
        "ACP-PATCH-211",
        "ACP-RESUME-217",
        "ACP-INFO-BACKGROUND-201",
    }
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in _CONFORMING_EXPECTED_SKIPS - exercised else "PASS"
        assert status == expected, f"{req_id} is {status}, expected {expected}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


def _background_statuses(fixture: str) -> tuple[dict[str, str], str]:
    """Run only `test_background.py` against `fixture`; the background rows' statuses and stdout."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_background")
    statuses = _table_statuses(result.stdout)
    return {r: statuses.get(r) for r in sorted(_BACKGROUND_SKIP_IDS)}, result.stdout


def test_background_list_dropped_fails_only_state_206():
    """The idle omits `background` after earlier snapshots carried it. With no list on an idle,
    no idle removal is judged, so `ACP-STATE-208` SKIPs."""
    statuses, stdout = _background_statuses("background_list_dropped.py")
    assert statuses == {
        "ACP-STATE-206": "FAIL", "ACP-STATE-207": "PASS", "ACP-STATE-208": "SKIPPED"
    }, stdout


def test_background_unannounced_item_fails_only_state_207():
    statuses, stdout = _background_statuses("background_unannounced_item.py")
    assert statuses == {
        "ACP-STATE-206": "PASS", "ACP-STATE-207": "FAIL", "ACP-STATE-208": "PASS"
    }, stdout


def test_background_removed_unfinished_fails_only_state_208():
    statuses, stdout = _background_statuses("background_removed_unfinished.py")
    assert statuses == {
        "ACP-STATE-206": "PASS", "ACP-STATE-207": "PASS", "ACP-STATE-208": "FAIL"
    }, stdout


def test_finishes_background_after_idle_passes_state_209(tmp_path):
    """The positive control: the background tool call ends after the turn's idle, and the agent
    re-sends the idle with it removed. `ACP-STATE-209` PASSes (judged), next to the rows that
    judge the same traffic."""
    statuses, _by_id, stdout = _full_run("finishes_background_after_idle.py", tmp_path)
    assert _fails(statuses) == set(), stdout
    for req_id in ("ACP-STATE-206", "ACP-STATE-207", "ACP-STATE-208", "ACP-STATE-209"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"


def test_background_end_not_resent_fails_only_state_209(tmp_path):
    """The item finishes after the idle and no snapshot drops it. `ACP-STATE-208` SKIPs: no
    snapshot removed anything, so there is no removal to judge."""
    statuses, _by_id, stdout = _full_run("background_end_not_resent.py", tmp_path)
    assert _fails(statuses) == {"ACP-STATE-209"}, stdout
    assert statuses["ACP-STATE-208"] == "SKIPPED", stdout


def test_starts_background_after_idle_passes_state_210(tmp_path):
    """The positive control: a background tool call starts after the turn's idle and the agent
    re-sends the idle with it listed, then again without it. `ACP-STATE-210` PASSes, and so does
    `ACP-STATE-209` (the item ends while idle and the next snapshot drops it)."""
    statuses, _by_id, stdout = _full_run("starts_background_after_idle.py", tmp_path)
    assert _fails(statuses) == set(), stdout
    for req_id in ("ACP-STATE-206", "ACP-STATE-207", "ACP-STATE-208", "ACP-STATE-209", "ACP-STATE-210"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"


def test_background_start_not_resent_fails_only_state_210(tmp_path):
    """The item is announced after the idle and never listed, and stays live. `ACP-STATE-209`
    SKIPs: no listed item ends while idle."""
    statuses, _by_id, stdout = _full_run("background_start_not_resent.py", tmp_path)
    assert _fails(statuses) == {"ACP-STATE-210"}, stdout
    assert statuses["ACP-STATE-209"] == "SKIPPED", stdout


def test_background_start_resent_without_item_fails_only_state_210(tmp_path):
    """The item is announced after the idle and the next `state_update` is an `idle` whose list
    omits it, the row's main FAIL case. `ACP-STATE-209` SKIPs: no listed item ends while idle."""
    statuses, _by_id, stdout = _full_run("background_start_resent_without_item.py", tmp_path)
    assert _fails(statuses) == {"ACP-STATE-210"}, stdout
    assert statuses["ACP-STATE-209"] == "SKIPPED", stdout


@pytest.mark.parametrize(
    "fixture", ["background_start_then_running.py", "background_start_ends_before_resend.py"]
)
def test_unjudged_background_start_skips_state_210(fixture: str, tmp_path):
    """The false-FAIL guards: the next `state_update` after the idle-time announcement is a
    `running` whose list omits the item (`background_start_then_running.py`), or the item ends
    before any `state_update` follows (`background_start_ends_before_resend.py`). Neither is
    judged, so `ACP-STATE-210` SKIPs and records the item as unjudged instead of FAILing. Only the
    background-work tests run: the stray `running` after the turn's idle can land inside another
    test's resume window."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        fixture,
        protocol_version=2,
        k="test_background",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-STATE-210"] == "SKIPPED", result.stdout
    assert _recorded(by_id, "ACP-STATE-210")["acp_tck_unjudged_background_starts"].startswith(
        "['tool_call:tool-bg-"
    ), result.stdout


def test_background_without_start_while_idle_skips_state_210(tmp_path):
    """The gated case: `finishes_background_after_idle.py` reports lists, but its item is
    announced during the turn, so no item starts while idle and `ACP-STATE-210` SKIPs."""
    statuses, _by_id, stdout = _full_run("finishes_background_after_idle.py", tmp_path)
    assert statuses["ACP-STATE-210"] == "SKIPPED", stdout


def test_lists_tool_call_with_its_terminal_is_recorded_not_failed(tmp_path):
    """The list names a command's tool call and the terminal that tool call references. The rule
    against listing both cannot be judged, so `ACP-INFO-BACKGROUND-201` records the pair."""
    statuses, by_id, stdout = _full_run("lists_tool_call_with_its_terminal.py", tmp_path)
    assert _fails(statuses) == set(), stdout
    assert statuses["ACP-INFO-BACKGROUND-201"] == "PASS", stdout
    recorded = _recorded(by_id, "ACP-INFO-BACKGROUND-201")
    assert "tool-cmd-" in recorded["acp_tck_listed_tool_calls_with_listed_terminal"], recorded


def test_references_background_terminal_records_no_pair(tmp_path):
    """The Codex-style agent lists only the terminal, so the record is empty."""
    statuses, by_id, stdout = _full_run("references_background_terminal.py", tmp_path)
    assert statuses["ACP-INFO-BACKGROUND-201"] == "PASS", stdout
    recorded = _recorded(by_id, "ACP-INFO-BACKGROUND-201")
    assert recorded["acp_tck_listed_tool_calls_with_listed_terminal"] == "[]", recorded


def test_tool_call_referencing_a_listed_terminal_is_live_at_idle():
    """`references_background_terminal.py` is Codex-style: its command's tool call stays
    `in_progress` at the turn-ending idle, and the terminal it references is the one listed in
    `background`. `ACP-PATCH-211` PASSes (it judged a tool call, not a SKIP) next to
    `ACP-STATE-206`/`207`, and nothing FAILs (`ACP-STATE-208` SKIPs: no item is ever removed).
    `leaves_terminal_tool_call_in_progress.py` keeps the FAIL for the same tool call when no list
    names the terminal, and `abandons_tool_call_after_terminal_exit.py` when the terminal exited
    and left the list before the idle."""
    fails, statuses, stdout = _fails_for("references_background_terminal.py", _TOOL_CALL_K)
    assert fails == set(), stdout
    for req_id in ("ACP-PATCH-210", "ACP-PATCH-211", "ACP-STATE-206", "ACP-STATE-207"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"
