"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_permission.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

import pytest

from .._runner import (
    FIXTURES_DIR_V2,
    _PERMISSION_FLOW_K,
    _TOOL_CALL_K,
    _fails,
    _fails_for,
    _run_cli,
    _table_statuses,
)


def test_asks_permission_fixture_passes_perm_201_but_skips_promptcap():
    """`asks_permission.py` isolates `ACP-PERM-201` from `conforming_full.py`'s broader
    capability set: it asks for permission on every turn but advertises no prompt-content
    capabilities at all, so `ACP-PERM-201` PASSes while `ACP-PROMPTCAP-001/002/003` still SKIP
    ("not advertised").

    Perf note: scoped with `-k` to `test_permission.py` (owns `ACP-PERM-201`) plus
    `test_prompt_capabilities.py` (owns `ACP-PROMPTCAP-001/002/003`) -- everything else is
    deselected (`NOT_TESTED`) rather than re-verified here. The exit code/overall verdict text
    are not asserted for the same reason as `test_calls_custom_method_passes_everything_it_can`
    above: `-k` scoping necessarily leaves every other MANDATORY id `NOT_TESTED`, which flips the
    verdict to NOT CONFORMANT by design regardless of how the exercised ids actually behave."""
    result = _run_cli(
        FIXTURES_DIR_V2, "asks_permission.py", protocol_version=2, k="test_permission or prompt_capabilities"
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert statuses.get("ACP-PERM-201") == "PASS", result.stdout
    for req_id in ("ACP-PROMPTCAP-001", "ACP-PROMPTCAP-002", "ACP-PROMPTCAP-003"):
        assert statuses.get(req_id) == "SKIPPED", result.stdout


def test_permission_flow_positive_controls_fail_nothing():
    """`asks_permission.py` (`requires_action` -> `running` -> `idle`), `requires_action_then_idle.py`
    (`requires_action` -> `idle`, no resume) and `starts_blocked.py` (`requires_action` first, no
    preliminary `running`) are all legal traces, and each idles `cancelled` when cancelled while
    blocked on its held permission request (`ACP-CANCEL-209`)."""
    for fixture in ("asks_permission.py", "requires_action_then_idle.py", "starts_blocked.py"):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_PERMISSION_FLOW_K)
        statuses = _table_statuses(result.stdout)
        assert _fails(statuses) == set(), f"{fixture}:\n{result.stdout}"
        for req_id in (
            "ACP-STATE-201",
            "ACP-STATE-202",
            "ACP-STATE-205",
            "ACP-PATCH-209",
            "ACP-PERM-201",
            "ACP-CANCEL-209",
            "ACP-CANCEL-213",
            "ACP-CLOSE-205",
        ):
            assert statuses[req_id] == "PASS", f"{fixture} {req_id}:\n{result.stdout}"


@pytest.mark.parametrize(
    ("fixture", "failing_id"),
    [
        ("duplicate_permission_option_id.py", "ACP-PERM-202"),
        ("permission_command_relative_cwd.py", "ACP-PERM-202"),
        ("proceeds_after_cancelled_permission.py", "ACP-PERM-203"),
        ("perm_unknown_option_is_approval.py", "ACP-PERM-002"),
        ("perm_unknown_outcome_is_approval.py", "ACP-PERM-204"),
        ("tool_call_chunk_first.py", "ACP-PATCH-208"),
        ("permission_without_requires_action.py", "ACP-PATCH-209"),
        ("tool_call_reopens_after_final.py", "ACP-PATCH-210"),
        ("leaves_tool_call_in_progress.py", "ACP-PATCH-211"),
        ("leaves_terminal_tool_call_in_progress.py", "ACP-PATCH-211"),
        ("abandons_tool_call_after_terminal_exit.py", "ACP-PATCH-211"),
        ("advertises_cancel_after_final.py", "ACP-PATCH-212"),
        ("relative_diff_path.py", "ACP-PATCH-213"),
        ("git_patch_ab_prefix.py", "ACP-PATCH-214"),
        ("git_patch_email_envelope.py", "ACP-PATCH-215"),
        ("output_after_exit.py", "ACP-PATCH-216"),
    ],
)
def test_tool_call_defect_fails_its_row_only(fixture: str, failing_id: str):
    """Each tool-call defect fixture trips exactly its own row (see its docstring)."""
    fails, statuses, stdout = _fails_for(fixture, _TOOL_CALL_K)
    assert fails == {failing_id}, stdout
    if fixture in (
        "proceeds_after_cancelled_permission.py",
        "perm_unknown_option_is_approval.py",
        "perm_unknown_outcome_is_approval.py",
    ):
        # The three "not approved" rows judge one turn shape each, so the others still PASS.
        for req_id in {"ACP-PERM-203", "ACP-PERM-002", "ACP-PERM-204"} - {failing_id}:
            assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"
    if fixture == "permission_without_requires_action.py":
        # No `requires_action` at all: cancelling while blocked is still judged (no state gate).
        assert statuses["ACP-CANCEL-209"] == "PASS", stdout
        assert statuses["ACP-CANCEL-213"] == "PASS", stdout


def test_only_reject_always_offered_is_never_selected(tmp_path):
    """`perm_only_reject_always.py` offers only `reject_always`. The default `allow` policy
    sends `session/cancel` and answers `cancelled` instead of selecting it (recorded as the
    test's fallback note), and the agent stays conformant within this scope."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "perm_only_reject_always.py",
        protocol_version=2,
        k=_TOOL_CALL_K,
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-PERM-201"] == "PASS", result.stdout
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    (perm_201,) = by_id["ACP-PERM-201"]["tests"]
    assert perm_201["properties"].get("acp_tck_permission_fallback") == (
        "agent offered no allow_once, allow_always or reject_once option"
    ), perm_201
