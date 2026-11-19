"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_subagents.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import pytest

from .._expectations import _ADVISORY_IDS
from .._runner import FIXTURES_DIR_V2, _assert_conforming_baseline, _fails, _run_cli, _table_statuses


# Skipped for `conforming.py` but exercised by a fixture whose child asks for permission, whose
# announced child shows up on the wire (a request and a custom session ID are observed) and whose
# spawn tool call carries `session` content (so the tool-call rows see a report). The child's
# requests are still pending when `session/close` arrives, so `ACP-SUBAGENT-203` is judged too.
_SUBAGENT_EXERCISED_IDS = {
    "ACP-SUBAGENT-203",
    "ACP-SUBAGENT-001",
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
    "ACP-PATCH-204",
    "ACP-PATCH-208",
    "ACP-PATCH-210",
    "ACP-PATCH-211",
    "ACP-PERM-201",
    "ACP-PERM-202",
    "ACP-JSONRPC-202",
    "ACP-ENUM-203",
}


_PROMPT_K = "test_prompt and not capabilities"


def test_exposes_subagent_passes_everything():
    """Announced child-session traffic is legal and must not end or start the parent's turn:
    the child's own `running`/`idle`, a `session_message` in both views, a child
    `session/request_permission` after the announcement, and a child chunk after the parent's turn
    ended. Same outcome as `conforming.py`, except that `_SUBAGENT_EXERCISED_IDS` PASS."""
    result = _run_cli(FIXTURES_DIR_V2, "exposes_subagent.py", protocol_version=2)
    _assert_conforming_baseline(result, "exposes_subagent.py", _SUBAGENT_EXERCISED_IDS)


_SUBAGENT_K = f"({_PROMPT_K}) or test_subagents"


def test_unannounced_child_update_fails_prompt_002_and_subagent_001():
    """The child's traffic is unannounced inside the turn, so both rows judge the one defect:
    `ACP-PROMPT-002` (in-turn notifications) and `ACP-SUBAGENT-001` (the whole connection)."""
    result = _run_cli(FIXTURES_DIR_V2, "unannounced_child_update.py", protocol_version=2, k=_SUBAGENT_K)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-002", "ACP-SUBAGENT-001"}, result.stdout


@pytest.mark.parametrize(
    "fixture",
    [
        "child_permission_before_announce.py",
        "session_message_unknown_participant.py",
        "child_update_after_turn_unannounced.py",
    ],
)
def test_unannounced_child_use_outside_prompt_002_fails_subagent_001_only(fixture):
    """A child request, a `session_message` participant and a post-turn child update are not
    in-turn `session/update`s for an unannounced child, so only `ACP-SUBAGENT-001` judges them."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-SUBAGENT-001"}, result.stdout
    assert statuses["ACP-PROMPT-002"] == "PASS", result.stdout


def test_subagent_rows_skip_without_a_child():
    """`conforming.py` never uses a session ID the client did not create, nor `session` content."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k="test_subagents")
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-001"] == "SKIPPED", result.stdout
    for number in (*range(2, 10), *range(11, 15), 201):
        assert statuses[f"ACP-SUBAGENT-{number:03}"] == "SKIPPED", result.stdout


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("self_parented_subagent.py", "ACP-SUBAGENT-003"),
        ("subagent_reuses_session_id.py", "ACP-SUBAGENT-004"),
        ("reparents_subagent.py", "ACP-SUBAGENT-005"),
        ("relative_subagent_cwd.py", "ACP-SUBAGENT-006"),
    ],
)
def test_subagent_association_violations_fail_one_row_only(fixture, failing):
    """Each association defect is announced on a known session and is schema-valid (`AbsolutePath`
    is a bare string), so `ACP-PROMPT-002`, `ACP-SUBAGENT-001` and `-002` PASS and the disjoint
    association rows `ACP-SUBAGENT-003..006` FAIL only the intended one."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {failing}, result.stdout
    for req_id in ("ACP-PROMPT-002", "ACP-SUBAGENT-001", "ACP-SUBAGENT-002"):
        assert statuses[req_id] == "PASS", result.stdout


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("session_message_same_participants.py", "ACP-SUBAGENT-007"),
        ("session_message_foreign_outer_session.py", "ACP-SUBAGENT-008"),
        ("session_message_mismatched_views.py", "ACP-SUBAGENT-009"),
    ],
)
def test_session_message_inconsistencies_fail_one_row_only(fixture, failing):
    """Each `session_message` defect names only announced sessions on a known session and is
    schema-valid, so `ACP-PROMPT-002`, `ACP-SUBAGENT-001` and the other `session_message` rows
    PASS and only the intended one of `ACP-SUBAGENT-007..009` FAILs."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {failing}, result.stdout
    for req_id in ("ACP-PROMPT-002", "ACP-SUBAGENT-001", "ACP-SUBAGENT-002"):
        assert statuses[req_id] == "PASS", result.stdout


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("unmirrored_child_state.py", "ACP-SUBAGENT-201"),
        ("child_task_as_user_message.py", "ACP-SUBAGENT-011"),
        ("child_task_after_output.py", "ACP-SUBAGENT-012"),
        ("session_message_chunk_before_participants.py", "ACP-SUBAGENT-013"),
        ("child_select_with_choices.py", "ACP-SUBAGENT-014"),
        ("child_idle_without_stop_reason.py", "ACP-SUBAGENT-207"),
    ],
)
def test_subagent_should_violations_fail_one_advisory_row_only(fixture, failing):
    """Each defect is schema-valid and announced, so the MUST rows PASS and only the intended one of
    `ACP-SUBAGENT-011..014` and `-201` (all ADVISORY) FAILs. An ADVISORY FAIL does not change the verdict, so
    the row outcome, not the exit code, is what is asserted."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {failing}, result.stdout
    assert failing in _ADVISORY_IDS
    # `-009` is left out: a violator may leave no pair of linked views to judge, and it SKIPs then
    for req_id in ("ACP-PROMPT-002", *(f"ACP-SUBAGENT-00{n}" for n in range(1, 9))):
        assert statuses[req_id] == "PASS", result.stdout


_CHILD_PROBE_IDS = {"ACP-SUBAGENT-018", "ACP-SUBAGENT-019", "ACP-LIST-004"}


@pytest.mark.parametrize(
    "fixture", ["exposes_subagent.py", "exposes_subagent_full.py", "replays_subagent_history.py"]
)
def test_child_probe_and_ordering_rows_pass_non_vacuously(fixture):
    """The announced child answers every request naming it (`session/resume`, `session/close`, and
    `session/delete` when advertised) with `-32602`, is never listed, its ID is not handed to a later
    `session/new`, and both copies of its state transitions precede the next one: every subagent row,
    `ACP-SUBAGENT-018`, `-019`, `-205` and `ACP-LIST-004` included, PASSes (none SKIPs)."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    for req_id in _SUBAGENT_ROW_IDS:
        assert statuses[req_id] == "PASS", f"{fixture} {req_id}:\n{result.stdout}"


def test_child_probe_rows_skip_without_a_child():
    """`conforming.py` announces no child: the probe phase sends nothing and the rows SKIP."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k="test_subagents")
    statuses = _table_statuses(result.stdout)
    skipped = (*_CHILD_PROBE_IDS, *(f"ACP-SUBAGENT-{n}" for n in (205, 206, 207)), "ACP-SUBAGENT-004")
    for req_id in skipped:
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("child_close_wrong_code.py", "ACP-SUBAGENT-018"),
        ("child_close_succeeds.py", "ACP-SUBAGENT-019"),
        ("child_delete_succeeds.py", "ACP-SUBAGENT-019"),
        ("lists_child_session.py", "ACP-LIST-004"),
        ("child_id_reused_for_new_session.py", "ACP-SUBAGENT-004"),
        ("late_child_state_mirror.py", "ACP-SUBAGENT-205"),
        ("child_idle_custom_stop_reason.py", "ACP-SUBAGENT-206"),
    ],
)
def test_child_probe_and_ordering_violators_fail_exactly_their_row(fixture, failing):
    """Each defect is announced, schema-valid and visible only to its own row: a `-32002` instead of
    `-32602` (018 judges only an error's code), a `session/close`/`session/delete` that succeeds (019
    judges only a success; the `delete` probe is sent because the fixture advertises it), a listed
    child, a child's ID reused by a later `session/new` (the probe phase's, so `ACP-SUBAGENT-001`..`009`
    still PASS) and mirrors held back until the child's `idle` (every state is mirrored in order, so
    `ACP-SUBAGENT-201` PASSes)."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {failing}, result.stdout
    assert statuses["ACP-SUBAGENT-201"] == "PASS", result.stdout


def test_child_idle_without_stop_reason_gives_subagent_206_nothing_to_judge():
    """The child's idle carries no `stopReason`: `ACP-SUBAGENT-207` FAILs it, and `-206` SKIPs
    instead of PASSing a value it did not judge."""
    result = _run_cli(FIXTURES_DIR_V2, "child_idle_without_stop_reason.py", protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-207"] == "FAIL", result.stdout
    assert statuses["ACP-SUBAGENT-206"] == "SKIPPED", result.stdout


def test_user_message_task_gives_subagent_012_nothing_to_judge():
    """The child's task came as a `user_message`: `ACP-SUBAGENT-011` FAILs it, and `-012` SKIPs
    instead of PASSing a child it did not judge."""
    result = _run_cli(FIXTURES_DIR_V2, "child_task_as_user_message.py", protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert statuses["ACP-SUBAGENT-011"] == "FAIL", result.stdout
    assert statuses["ACP-SUBAGENT-012"] == "SKIPPED", result.stdout


def test_incoming_task_without_a_sender_passes_subagent_012():
    """`child_task_without_sender.py` tells the child its task as an incoming `session_message`
    that omits `senderSessionId` (the agent has no evidence of the sender and does not assume the
    parent): the task is reported, so `ACP-SUBAGENT-012` PASSes and nothing FAILs."""
    result = _run_cli(FIXTURES_DIR_V2, "child_task_without_sender.py", protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-SUBAGENT-012"] == "PASS", result.stdout
    assert statuses["ACP-SUBAGENT-011"] == "PASS", result.stdout


def test_malformed_subagent_directories_fail_prompt_002_not_subagent_006():
    """A non-string `cwd` and a non-array `additionalDirectories` are schema defects: only
    `ACP-PROMPT-002` FAILs, and `ACP-SUBAGENT-006` judges the later well-typed values instead."""
    result = _run_cli(FIXTURES_DIR_V2, "malformed_subagent_directories.py", protocol_version=2, k=_SUBAGENT_K)
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-PROMPT-002"}, result.stdout
    assert statuses["ACP-SUBAGENT-006"] == "PASS", result.stdout


def test_session_message_rows_skip_when_they_judge_nothing():
    """A `session_message` that names no participant and no view leaves `ACP-SUBAGENT-007..009`
    nothing to judge: each SKIPs, none PASSes vacuously."""
    result = _run_cli(
        FIXTURES_DIR_V2, "session_message_without_participants.py", protocol_version=2, k=_SUBAGENT_K
    )
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-SUBAGENT-007", "ACP-SUBAGENT-008", "ACP-SUBAGENT-009"):
        assert statuses[req_id] == "SKIPPED", result.stdout
    assert statuses["ACP-SUBAGENT-001"] == "PASS", result.stdout
    assert statuses["ACP-PROMPT-002"] == "PASS", result.stdout


@pytest.mark.parametrize(
    "fixture",
    [
        "session_content_unknown_session.py",  # in a tool call's content
        "session_content_unknown_in_permission.py",  # only in a permission request's `subject.toolCall`
    ],
)
def test_session_content_unknown_session_fails_subagent_002_only(fixture):
    """A `session` content reference to a never-announced session is not child traffic: only
    `ACP-SUBAGENT-002` judges it, while `ACP-SUBAGENT-001` and `ACP-PROMPT-002` PASS."""
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SUBAGENT_K)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-SUBAGENT-002"}, result.stdout
    assert statuses["ACP-SUBAGENT-001"] == "PASS", result.stdout
    assert statuses["ACP-PROMPT-002"] == "PASS", result.stdout


def test_replays_subagent_history_passes_everything():
    """A child announced and replayed under its own `sessionId` on `replayFrom: start` (with its own
    `user_message` and `replay_complete`), plus a re-announcement and a live child chunk before every
    resume response, replay or not, is legal: same outcome as `conforming.py`, and the child replay
    rows `ACP-RESUME-223`/`-225`/`-226` PASS."""
    result = _run_cli(FIXTURES_DIR_V2, "replays_subagent_history.py", protocol_version=2)
    _assert_conforming_baseline(
        result,
        "replays_subagent_history.py",
        _SUBAGENT_EXERCISED_IDS | {"ACP-RESUME-223", "ACP-RESUME-225", "ACP-RESUME-226"},
    )


_SUBAGENT_ROW_IDS = {f"ACP-SUBAGENT-{n:03}" for n in (*range(1, 10), *range(11, 15))} | {
    "ACP-SUBAGENT-018",
    "ACP-SUBAGENT-019",
    "ACP-SUBAGENT-201",
    "ACP-SUBAGENT-205",
    "ACP-SUBAGENT-206",
    "ACP-SUBAGENT-207",
    "ACP-LIST-004",
}


def test_subagent_prompt_reaches_the_subagents_turn():
    """`--subagent-prompt __subagent__` is the text the subagents connection sends, so
    `exposes_subagent_on_request.py` exposes its child there and every subagent row PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "exposes_subagent_on_request.py",
        protocol_version=2,
        k="test_subagents",
        subagent_prompt="__subagent__",
    )
    statuses = _table_statuses(result.stdout)
    assert "FAIL" not in set(statuses.values()), result.stdout
    for req_id in _SUBAGENT_ROW_IDS:
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
    result = _run_cli(
        FIXTURES_DIR_V2,
        "exposes_subagent_on_request.py",
        protocol_version=2,
        k="test_subagents",
        **options,
    )
    statuses = _table_statuses(result.stdout)
    for req_id in _SUBAGENT_ROW_IDS:
        assert statuses[req_id] == "SKIPPED", f"{req_id}:\n{result.stdout}"
    assert "FAIL" not in set(statuses.values()), result.stdout
