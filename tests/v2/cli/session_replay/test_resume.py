"""End-to-end CLI tests for the `session/resume` rows of `src/tck/v2/conformance/test_session_capabilities.py`:
each runs fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import pytest

from .._runner import FIXTURES_DIR_V2, _fails, _full_run, _resume_statuses, _run_cli, _table_statuses


def test_resume_snapshot_omits_background_fails_only_resume_217(tmp_path):
    """Live updates carry the list, the resume snapshot omits it. `ACP-RESUME-213` SKIPs (the
    snapshot lists nothing); `reports_background_work.py` PASSes `ACP-RESUME-217`."""
    statuses, _by_id, stdout = _full_run("resume_snapshot_omits_background.py", tmp_path)
    assert _fails(statuses) == {"ACP-RESUME-217"}, stdout
    assert statuses["ACP-RESUME-213"] == "SKIPPED", stdout


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("child_missing_replay_complete.py", "ACP-RESUME-223"),
        ("resume_child_traffic_unannounced.py", "ACP-RESUME-225"),
        ("replays_child_out_of_order.py", "ACP-RESUME-226"),
        ("replays_child_under_wrong_parent.py", "ACP-RESUME-226"),
    ],
)
def test_child_replay_defects_fail_their_row_only(fixture, failing):
    """`child_missing_replay_complete.py` ends no replayed child with its own `replay_complete`;
    `resume_child_traffic_unannounced.py` sends live child chunks after a resume without replay
    without announcing the child again. `replays_child_out_of_order.py` replays the child's two
    messages in reverse order, and `replays_child_under_wrong_parent.py` replays the child's
    nested child under the resumed session. Each FAILs its row, and the other child replay rows
    PASS."""
    statuses, stdout = _resume_statuses(fixture)
    assert _fails(statuses) == {failing}, stdout
    for req_id in {"ACP-RESUME-223", "ACP-RESUME-225", "ACP-RESUME-226"} - {failing}:
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"


def test_replays_unannounced_child_fails_resume_209_only():
    result = _run_cli(FIXTURES_DIR_V2, "replays_unannounced_child.py", protocol_version=2)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-RESUME-209"}, result.stdout
    assert statuses["ACP-RESUME-002"] == "PASS", result.stdout


def test_replays_child_before_announce_fails_resume_209_only():
    """The child was announced on an earlier turn, but not within the resume exchange."""
    result = _run_cli(FIXTURES_DIR_V2, "replays_child_before_announce.py", protocol_version=2)
    assert result.returncode != 0
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-RESUME-209"}, result.stdout


def test_resume_replays_when_not_asked_fails_resume_002_only():
    """`resume_replays_when_not_asked.py` replays the session's full retained history on every
    `session/resume`, even when `replayFrom` is omitted/`null` -- FAILs exactly `ACP-RESUME-002` within its `-k` scope
    (the "MUST NOT replay when not asked" rule). `ACP-RESUME-001` (resume itself still succeeds)
    and `ACP-RESUME-202`/`204`..`209` (the replay-`{"type": "start"}` scenarios, the snapshot and
    cursor checks, answered identically to `conforming_full.py`) are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_replays_when_not_asked.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-002"}, result.stdout
    for req_id in (
        "ACP-RESUME-001",
        "ACP-RESUME-202",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
    ):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_responds_before_replay_fails_resume_202_only():
    """`resume_responds_before_replay.py` answers `session/resume` before replaying stored
    history (reversed order vs. the spec's requirement) -- FAILs exactly `ACP-RESUME-202` within its `-k` scope.
    `ACP-RESUME-204`'s own test reads only up to the response before checking replayed
    `messageId`s, so with the replay now arriving *after* the response it never observes any
    replayed update at all and legitimately SKIPs rather than PASSing or FAILing.
    `ACP-RESUME-001`/`002`/`205`..`209` are unaffected: the state snapshot still precedes the
    response."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_responds_before_replay.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-202"}, result.stdout
    assert statuses.get("ACP-RESUME-204") == "SKIPPED", result.stdout
    for req_id in (
        "ACP-RESUME-001",
        "ACP-RESUME-002",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
    ):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_replay_missing_message_id_fails_resume_204_and_209_only():
    """`resume_replay_missing_message_id.py` replays correctly (before responding, only when
    asked) but strips `messageId` from every replayed `session/update` -- FAILs exactly
    `ACP-RESUME-204` and `ACP-RESUME-209` (a message update without `messageId` is
    schema-invalid). `ACP-RESUME-001`/`002`/`202`/`205`..`208` are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_replay_missing_message_id.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-204", "ACP-RESUME-209"}, result.stdout
    for req_id in (
        "ACP-RESUME-001",
        "ACP-RESUME-202",
        "ACP-RESUME-002",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
    ):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_always_errors_all_resume_rows_skip_together():
    """`resume_always_errors.py` advertises `capabilities.session: {}` but always errors on
    `session/resume` with a plain `-32603`, never `-32601` (Method not found, which
    `obtain_resumable_session` treats as a hard FAIL). All three of
    `obtain_resumable_session`'s routes (create-then-resume, close-then-resume, list-then-resume)
    end in the same `session/resume` call, so all three are exhausted identically here, and
    every test that routes through it -- `ACP-RESUME-001/002/202/204..209` and `ACP-ADDDIRS-202` -- must
    SKIP together with the same "no resumable session obtainable" reason, never hard-FAIL:
    `ACP-RESUME-002/202/204..209` must call `obtain_resumable_session` first rather than building their
    own session directly (`_session_with_history`), or they would hard-FAIL on this fixture's
    `session/resume` error, producing a false NOT CONFORMANT for an agent the TCK itself admits
    it could not obtain a resumable session from."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_always_errors.py",
        protocol_version=2,
        k="session_capabilities",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    # `ACP-RESUME-216` (ADVISORY) FAILs any error on resuming an active session, where the other
    # resume rows SKIP on one.
    assert fails == {"ACP-RESUME-216"}, f"expected only ACP-RESUME-216, got {fails}: {result.stdout}"
    for req_id in (
        "ACP-RESUME-001",
        "ACP-RESUME-202",
        "ACP-RESUME-002",
        "ACP-RESUME-204",
        "ACP-RESUME-205",
        "ACP-RESUME-206",
        "ACP-RESUME-207",
        "ACP-RESUME-208",
        "ACP-RESUME-209",
        "ACP-RESUME-212",
        "ACP-RESUME-213",
        "ACP-RESUME-214",
        "ACP-ADDDIRS-202",
    ):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"


def test_resume_no_state_snapshot_fails_resume_206_only():
    """`resume_no_state_snapshot.py` never sends the current-state `state_update` before
    answering `session/resume` -- FAILs exactly `ACP-RESUME-206` within its `-k` scope."""
    result = _run_cli(
        FIXTURES_DIR_V2, "resume_no_state_snapshot.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-206"}, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_replays_state_updates_fails_resume_212_and_220():
    """`resume_replays_state_updates.py` records and replays every `state_update`, so a replayed
    `running` precedes the snapshot (`ACP-RESUME-212`) and, being no history, sits before
    `replay_complete` (`ACP-RESUME-220`)."""
    statuses, stdout = _resume_statuses("resume_replays_state_updates.py")
    assert _fails(statuses) == {"ACP-RESUME-212", "ACP-RESUME-220"}, stdout


_REPLAY_COMPLETE_IDS = {f"ACP-RESUME-{n}" for n in range(218, 223)}


def test_conforming_agents_pass_replay_complete_rows():
    """The fixture base ends every replay with one `replay_complete` before the session info and
    the snapshot, so `ACP-RESUME-218..221` PASS non-vacuously. No agent request arrives during a
    resume, so `ACP-RESUME-222` SKIPs."""
    for fixture in ("conforming.py", "conforming_full.py"):
        statuses, stdout = _resume_statuses(fixture, cancel_prompt="__hang__")
        assert _fails(statuses) == set(), f"{fixture}:\n{stdout}"
        assert {statuses[i] for i in _REPLAY_COMPLETE_IDS - {"ACP-RESUME-222"}} == {"PASS"}, stdout
        assert statuses["ACP-RESUME-222"] == "SKIPPED", stdout


def test_resume_205_judges_every_chunk_kind(monkeypatch):
    """`replays_entity_chunks.py` replays session-message, tool-call-content, terminal-output and
    compaction-summary chunks, each after its emptied whole-entity update: nothing FAILs.
    `replays_unprimed_entity_chunks.py` drops the opener of one kind at a time (and of all of them
    at once): only `ACP-RESUME-205` FAILs, and it names the kind."""
    statuses, stdout = _resume_statuses("replays_entity_chunks.py")
    assert _fails(statuses) == set() and statuses["ACP-RESUME-205"] == "PASS", stdout
    for kind in ("", "session_message_chunk", "tool_call_content_chunk", "terminal_output_chunk", "compaction_summary_chunk"):
        monkeypatch.setenv("TCK_FIXTURE_UNPRIMED_CHUNK", kind)
        statuses, stdout = _resume_statuses("replays_unprimed_entity_chunks.py")
        assert _fails(statuses) == {"ACP-RESUME-205"}, f"{kind or 'all kinds'}:\n{stdout}"
        assert (kind or "session_message_chunk") in stdout, stdout


@pytest.mark.parametrize(
    ("fixture", "failing"),
    [
        ("resume_omits_replay_complete.py", {"ACP-RESUME-218"}),
        ("resume_replay_complete_twice.py", {"ACP-RESUME-218"}),
        ("resume_history_after_replay_complete.py", {"ACP-RESUME-218"}),
        ("replay_complete_without_replay.py", {"ACP-RESUME-219"}),
        ("resume_snapshot_before_replay_complete.py", {"ACP-RESUME-220"}),
        ("resume_notice_before_replay_complete.py", {"ACP-RESUME-220"}),
        ("rejected_cursor_sends_replay_complete.py", {"ACP-RESUME-221"}),
        ("rejected_cursor_replays_history.py", {"ACP-RESUME-221"}),
        ("requests_before_replay_complete.py", {"ACP-RESUME-222"}),
    ],
)
def test_replay_complete_defect_fixtures_fail_only_their_rows(fixture, failing):
    """Each fixture has one defect and FAILs exactly the row it names. Without a
    `replay_complete` (`resume_omits_replay_complete.py`) the rows that need one SKIP."""
    statuses, stdout = _resume_statuses(fixture)
    assert _fails(statuses) == failing, stdout
    for req_id in _REPLAY_COMPLETE_IDS - failing:
        assert statuses[req_id] in {"PASS", "SKIPPED"}, f"{req_id}:\n{stdout}"
    if fixture == "resume_omits_replay_complete.py":
        assert statuses["ACP-RESUME-220"] == "SKIPPED", stdout


def test_resume_no_session_info_fails_resume_214_only():
    statuses, stdout = _resume_statuses("resume_no_session_info.py")
    assert _fails(statuses) == {"ACP-RESUME-214"}, stdout


def test_resume_omits_config_options_fails_resume_210_only():
    """The omitted list leaves `ACP-CONFIG-203` nothing to validate, so it SKIPs."""
    statuses, stdout = _resume_statuses("resume_omits_config_options.py")
    assert _fails(statuses) == {"ACP-RESUME-210"}, stdout


def test_resume_omits_available_commands_fails_resume_210_only():
    statuses, stdout = _resume_statuses("resume_omits_available_commands.py")
    assert _fails(statuses) == {"ACP-RESUME-210"}, stdout


def test_resume_rejects_unprompted_active_session_fails_resume_216_only():
    """Resume works for a prompted or closed session, so every other row runs; only the resume of
    a just-created session errors, and `ACP-RESUME-210`'s version of it has nothing to judge."""
    statuses, stdout = _resume_statuses("resume_rejects_unprompted_active_session.py")
    assert _fails(statuses) == {"ACP-RESUME-216"}, stdout


def test_resume_lists_background_work_passes_resume_213():
    """The positive control: the snapshot lists an unfinished background tool call and a
    `tool_call_update` announces it first, so `ACP-RESUME-213` PASSes, not SKIPs."""
    statuses, stdout = _resume_statuses("resume_lists_background_work.py")
    assert _fails(statuses) == set(), stdout
    assert statuses["ACP-RESUME-213"] == "PASS", stdout


def test_resume_lists_background_subagent_passes_resume_224():
    """The positive control: the snapshot lists a background child, and a `subagent_update` for it
    follows `replay_complete` (with the child's own `replay_complete`, since it is announced during
    the request): `ACP-RESUME-224` PASSes, as do `-213` and `-223`."""
    statuses, stdout = _resume_statuses("resume_lists_background_subagent.py")
    assert _fails(statuses) == set(), stdout
    for req_id in ("ACP-RESUME-213", "ACP-RESUME-223", "ACP-RESUME-224"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"


def test_resume_background_child_announced_in_replay_fails_resume_224_only():
    """The child's only `subagent_update` of a replay resume precedes `replay_complete`, so it is
    history; the resume without replay still announces it (`ACP-RESUME-213` PASSes)."""
    statuses, stdout = _resume_statuses("resume_background_child_announced_in_replay.py")
    assert _fails(statuses) == {"ACP-RESUME-224"}, stdout
    assert statuses["ACP-RESUME-213"] == "PASS", stdout


def test_resume_background_without_updates_fails_resume_213_only():
    statuses, stdout = _resume_statuses("resume_background_without_updates.py")
    assert _fails(statuses) == {"ACP-RESUME-213"}, stdout


def test_resume_ignores_unknown_cursor_fails_resume_207_only():
    """`resume_ignores_unknown_cursor.py` resumes without replay on an unsupported cursor type
    instead of rejecting it -- FAILs exactly `ACP-RESUME-207` within its `-k` scope; malformed values are still
    rejected, so `ACP-RESUME-208` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_ignores_unknown_cursor.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-207"}, result.stdout
    assert statuses.get("ACP-RESUME-208") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_accepts_malformed_cursor_fails_resume_208_only():
    """`resume_accepts_malformed_cursor.py` treats a malformed `replayFrom` as omitted -- FAILs
    exactly `ACP-RESUME-208`; unsupported well-formed cursors are still rejected, so
    `ACP-RESUME-207` PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_accepts_malformed_cursor.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-RESUME-208"}, result.stdout
    assert statuses.get("ACP-RESUME-207") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_sends_notice_passes_resume_202_and_init_204():
    """`resume_sends_notice.py` sends a live `notice` update right after `session/resume` and
    advertises `providers`. The draft allows both, so
    `ACP-RESUME-202` and `ACP-INIT-204` PASS and nothing FAILs."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_sends_notice.py",
        protocol_version=2,
        k="session_capabilities or initialize",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert not fails, result.stdout
    assert statuses.get("ACP-RESUME-202") == "PASS", result.stdout
    assert statuses.get("ACP-INIT-204") == "PASS", result.stdout
