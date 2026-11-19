"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_subagents.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import pytest

from .._expectations import (
    _ALL_IDS,
    _CANCEL_IDS,
    _CAPABILITY_GATED_IDS,
    _INFORMATIONAL_IDS,
    _SUBAGENT_IDS,
    _SUBAGENT_PROBE_IDS,
    _SUBAGENT_STATE_IDS,
)
from .._runner import _output_fail_ids, _run_cli, _table_statuses


_SUBAGENT_K = "test_subagents or test_client_capabilities"
"""The subagent rows plus `ACP-CLIENTCAP-007` (the default connection, which never advertises
`subagents`), so a fixture that sends child traffic only to a client that asked for it is
shown to stay clean there."""


def test_exposes_subagent_passes_everything():
    """`exposes_subagent.py` sends subagent traffic only to a client that advertised `subagents`:
    an announced child with nested child, both views of a `session_message`, a streamed follow-up,
    `session` content, a child permission request, the parent-reported work state and a child chunk
    after the turn. It stays silent on the default connection, so `ACP-CLIENTCAP-007` PASSes, and
    it advertises nothing else, so the outcome is `conforming.py`'s except that every
    `_SUBAGENT_IDS` row PASSes instead of SKIPping."""
    result = _run_cli("exposes_subagent.py")
    assert result.returncode == 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert set(statuses) == _ALL_IDS | _INFORMATIONAL_IDS, (
        f"requirement table missing/extra ids: {result.stdout}"
    )
    skip_ids = (_CANCEL_IDS | _CAPABILITY_GATED_IDS) - _SUBAGENT_IDS - _SUBAGENT_STATE_IDS
    for req_id, status in statuses.items():
        expected = "SKIPPED" if req_id in skip_ids else "PASS"
        assert status == expected, f"{req_id} is {status}, expected {expected}:\n{result.stdout}"
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout


@pytest.mark.parametrize("fixture", ["replays_subagent_history.py", "replays_historical_addresses.py"])
def test_replays_subagent_history_passes_every_subagent_row(fixture):
    """`replays_subagent_history.py` advertises `loadSession` and, on `session/load` to a client that
    advertised `subagents`, replays its announcements and child updates before the response: the
    replay is judged on its own terms and every subagent row PASSes. `replays_historical_addresses.py`
    also replays a `session_message` participant and a `session` reference that name a session
    nothing announced: historical addresses, not judged."""
    result = _run_cli(fixture, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    for req_id in _SUBAGENT_IDS | {"ACP-CLIENTCAP-007"}:
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"


def test_exposes_subagent_full_passes_the_child_probe_rows_non_vacuously():
    """`exposes_subagent_full.py` advertises `loadSession`, `list`, `close` and `delete`, answers
    every request naming an announced child `-32602` and never lists a child: every subagent row,
    the probe rows and the state row PASS (none SKIPs). `replays_subagent_history.py` advertises
    only `loadSession`, so the `session/load` probe is all there is: `-018` PASSes, `-019` and
    `ACP-LIST-004` SKIP. `exposes_subagent.py` advertises none of them: all three SKIP, `-020`
    PASSes."""
    expected = {
        "exposes_subagent_full.py": dict.fromkeys(_SUBAGENT_PROBE_IDS, "PASS"),
        "replays_subagent_history.py": {
            "ACP-SUBAGENT-018": "PASS",
            "ACP-SUBAGENT-019": "SKIPPED",
            "ACP-LIST-004": "SKIPPED",
        },
        "exposes_subagent.py": dict.fromkeys(_SUBAGENT_PROBE_IDS, "SKIPPED"),
    }
    for fixture, probe_statuses in expected.items():
        result = _run_cli(fixture, k=_SUBAGENT_K)
        statuses = _table_statuses(result.stdout)
        assert _output_fail_ids(result.stdout) == set(), f"{fixture}:\n{result.stdout}"
        for req_id in _SUBAGENT_IDS | _SUBAGENT_STATE_IDS | {"ACP-CLIENTCAP-007"}:
            assert statuses[req_id] == "PASS", f"{fixture} {req_id}:\n{result.stdout}"
        for req_id, status in probe_statuses.items():
            assert statuses[req_id] == status, f"{fixture} {req_id}:\n{result.stdout}"


def test_subagent_prompt_reaches_the_subagents_turn():
    """`--subagent-prompt __subagent__` is the text the subagents connection sends, so
    `exposes_subagent_on_request.py` exposes its child there and every subagent row PASSes."""
    result = _run_cli("exposes_subagent_on_request.py", k=_SUBAGENT_K, subagent_prompt="__subagent__")
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    for req_id in _SUBAGENT_IDS | {"ACP-CLIENTCAP-007"}:
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"cancel_prompt": "__subagent__"},
        {"subagent_cancel_prompt": "__subagent__"},
    ],
    ids=["default", "cancel_prompt", "subagent_cancel_prompt"],
)
def test_subagents_turn_keeps_its_built_in_text_without_subagent_prompt(options):
    """Without `--subagent-prompt` the subagents turn sends the built-in text, whatever the
    cancel prompts say, so a fixture that exposes a child only for `__subagent__` shows none."""
    result = _run_cli("exposes_subagent_on_request.py", k="test_subagents", **options)
    statuses = _table_statuses(result.stdout)
    for req_id in _SUBAGENT_IDS:
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"
    assert _output_fail_ids(result.stdout) == set(), result.stdout


def test_subagent_rows_skip_without_a_child():
    """`conforming.py` exposes no child even to a client that advertised `subagents`, so every row
    SKIPs rather than PASSing vacuously."""
    result = _run_cli("conforming.py", k="test_subagents")
    statuses = _table_statuses(result.stdout)
    for req_id in _SUBAGENT_IDS:
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"
    assert _output_fail_ids(result.stdout) == set(), result.stdout


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        # Announcement ordering, over requests (incl. `fs/*`), `session_message` participants,
        # traffic after the turn and replay on `session/load`.
        ("unannounced_child_update.py", "ACP-SUBAGENT-001"),
        ("child_permission_before_announce.py", "ACP-SUBAGENT-001"),
        # unadvertised too, so `ACP-CLIENTCAP-001` (which judges this connection) FAILs as well
        ("child_fs_request_before_announce.py", {"ACP-SUBAGENT-001", "ACP-CLIENTCAP-001"}),
        ("child_fs_request_after_announce.py", "ACP-CLIENTCAP-001"),
        ("session_message_unknown_participant.py", "ACP-SUBAGENT-001"),
        ("child_update_after_turn_unannounced.py", "ACP-SUBAGENT-001"),
        ("replays_unannounced_child.py", "ACP-SUBAGENT-001"),
        ("replays_child_without_announcement.py", "ACP-SUBAGENT-001"),
        # the rule applies again on every load: traffic after the load response is judged against
        # what the load announced, not the turn's announcements
        ("child_traffic_after_load_unannounced.py", "ACP-SUBAGENT-001"),
        # `session` content references are not child traffic
        ("session_content_unknown_session.py", "ACP-SUBAGENT-002"),
        ("session_content_unknown_in_permission.py", "ACP-SUBAGENT-002"),
        # association integrity and directories
        ("self_parented_subagent.py", "ACP-SUBAGENT-003"),
        ("subagent_reuses_session_id.py", "ACP-SUBAGENT-004"),
        ("reparents_subagent.py", "ACP-SUBAGENT-005"),
        ("relative_subagent_cwd.py", "ACP-SUBAGENT-006"),
        # `session_message` consistency
        ("session_message_same_participants.py", "ACP-SUBAGENT-007"),
        ("session_message_foreign_outer_session.py", "ACP-SUBAGENT-008"),
        ("session_message_mismatched_views.py", "ACP-SUBAGENT-009"),
        # schema validity of the subagent shapes, including the `state` snapshot
        ("malformed_subagent_directories.py", "ACP-SUBAGENT-015"),
        ("malformed_subagent_state.py", "ACP-SUBAGENT-015"),
        # the SHOULDs (ADVISORY)
        ("child_task_as_user_message.py", "ACP-SUBAGENT-011"),
        ("child_task_after_output.py", "ACP-SUBAGENT-012"),
        ("session_message_without_participants.py", "ACP-SUBAGENT-012"),
        ("session_message_chunk_before_participants.py", "ACP-SUBAGENT-013"),
        ("child_select_with_choices.py", "ACP-SUBAGENT-014"),
        # the child-session probes (after the judged transcript), listing and reported states
        ("child_close_wrong_code.py", "ACP-SUBAGENT-018"),
        ("child_close_succeeds.py", "ACP-SUBAGENT-019"),
        ("lists_child_session.py", "ACP-LIST-004"),
        ("child_custom_state.py", "ACP-SUBAGENT-020"),
    ],
)
def test_subagent_violators_fail_exactly_their_row(fixture, failing):
    """Each violator is `exposes_subagent.py` with one defect, sent only to a client that
    advertised `subagents`: exactly the intended row(s) FAIL, and `ACP-CLIENTCAP-007` PASSes (the
    default connection never sees subagent traffic). The ADVISORY ones leave the verdict alone."""
    result = _run_cli(fixture, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    expected = {failing} if isinstance(failing, str) else failing
    assert _output_fail_ids(result.stdout) == expected, f"{fixture}:\n{result.stdout}"
    assert statuses["ACP-CLIENTCAP-007"] == "PASS", result.stdout


def test_subagent_rows_are_judged_on_the_turn_when_the_load_never_answers():
    """`session/load` is never answered, so the connection has no replay to judge. That is
    `ACP-LOAD-001`'s finding: every subagent row is still judged on the turn's traffic and PASSes,
    none FAILs for the missing answer."""
    result = _run_cli("subagents_load_never_answers.py", k="test_subagents")
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    for req_id in _SUBAGENT_IDS:
        assert statuses[req_id] == "PASS", f"{req_id}:\n{result.stdout}"


def test_invalid_tool_call_status_fails_the_turn_schema_rows_not_subagent_015():
    """Every tool call of `invalid_tool_call_status.py` has an invalid `status`, the spawn tool call
    that carries a `session` item included. Only the rows that validate a turn's updates FAIL
    (`ACP-PROMPT-002`, and `ACP-SCHEMA-001` over the basic exchange): `ACP-SUBAGENT-015`
    validates the `session` item, not the tool call carrying it."""
    result = _run_cli("invalid_tool_call_status.py")
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == {"ACP-PROMPT-002", "ACP-SCHEMA-001"}, result.stdout
    assert statuses["ACP-SUBAGENT-015"] == "PASS", result.stdout


def test_incoming_task_without_a_sender_passes_subagent_012():
    """`child_task_without_sender.py` tells the child its task as an incoming `session_message`
    that omits `senderSessionId` (the agent has no evidence of the sender and does not assume the
    parent): the task is reported, so `ACP-SUBAGENT-012` PASSes and nothing FAILs."""
    result = _run_cli("child_task_without_sender.py", k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    assert statuses["ACP-SUBAGENT-012"] == "PASS", result.stdout
    assert statuses["ACP-SUBAGENT-011"] == "PASS", result.stdout


def test_user_message_task_gives_subagent_012_nothing_to_judge():
    """The child's task came as a `user_message_chunk`: `ACP-SUBAGENT-011` FAILs it, and `-012`
    SKIPs instead of PASSing a child it did not judge."""
    result = _run_cli("child_task_as_user_message.py", k="test_subagents")
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-011"] == "FAIL", result.stdout
    assert statuses["ACP-SUBAGENT-012"] == "SKIPPED", result.stdout


def test_session_message_rows_skip_when_they_judge_nothing():
    """A `session_message` that names no participant and no view leaves `ACP-SUBAGENT-007..009`
    nothing to judge: each SKIPs, none PASSes vacuously."""
    result = _run_cli("session_message_without_participants.py", k="test_subagents")
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-SUBAGENT-007", "ACP-SUBAGENT-008", "ACP-SUBAGENT-009"):
        assert statuses[req_id] == "SKIPPED", result.stdout
    assert statuses["ACP-SUBAGENT-001"] == "PASS", result.stdout


def test_malformed_subagent_directories_fail_015_not_006():
    """A non-string `cwd` and a non-array `additionalDirectories` are schema defects: only
    `ACP-SUBAGENT-015` FAILs, and `ACP-SUBAGENT-006` judges the later well-typed values instead."""
    result = _run_cli("malformed_subagent_directories.py", k="test_subagents")
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-015"] == "FAIL", result.stdout
    assert statuses["ACP-SUBAGENT-006"] == "PASS", result.stdout
