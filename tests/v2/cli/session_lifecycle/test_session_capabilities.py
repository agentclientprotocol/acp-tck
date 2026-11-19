"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_session_capabilities.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._runner import (
    FIXTURES_DIR_V2,
    _fails,
    _fails_for,
    _full_run,
    _recorded,
    _resume_statuses,
    _run_cli,
    _table_statuses,
)
from ._helpers import _SETUP_K


def test_keeps_background_work_passes_fork_206_and_records_the_cancel(tmp_path):
    """The positive control for the fork row: the source session's work is still listed at fork
    time and the fork's snapshots do not list it. Run with a `__hang__` cancel prompt, its
    `session/cancel` leaves that listed work running, so `ACP-INFO-BACKGROUND-202` records it."""
    statuses, by_id, stdout = _full_run(
        "keeps_background_work.py", tmp_path, cancel_prompt="__hang__"
    )
    assert _fails(statuses) == set(), stdout
    for req_id in ("ACP-FORK-206", "ACP-RESUME-213", "ACP-RESUME-217", "ACP-INFO-BACKGROUND-202"):
        assert statuses[req_id] == "PASS", f"{req_id}:\n{stdout}"
    recorded = _recorded(by_id, "ACP-INFO-BACKGROUND-202")
    assert "tool-bg-" in recorded["acp_tck_background_listed_at_cancel"], recorded
    assert recorded["acp_tck_background_finalized_after_cancel"] == "[]", recorded
    assert "tool-bg-" in recorded["acp_tck_background_listed_at_idle"], recorded


def test_fork_copies_background_work_fails_only_fork_206(tmp_path):
    statuses, _by_id, stdout = _full_run("fork_copies_background_work.py", tmp_path)
    assert _fails(statuses) == {"ACP-FORK-206"}, stdout


def test_fork_206_judges_snapshots_received_before_the_fork_turn_times_out():
    """`fork_copies_background_work_and_hangs.py` copies the source's list into the fork's
    `running` snapshot and never ends the fork's turn. `ACP-FORK-206` FAILs on the snapshot it
    received (it does not SKIP on the timeout), next to `ACP-FORK-202`."""
    fails, _statuses, stdout = _fails_for("fork_copies_background_work_and_hangs.py", "fork")
    assert fails == {"ACP-FORK-202", "ACP-FORK-206"}, stdout


def test_resume_lists_foreign_session_is_never_resumed():
    """`resume_lists_foreign_session.py` lists only a session under a foreign `cwd` (ignoring the
    `cwd` filter -- FAILs `ACP-LIST-002`/`203`) and resumes only that session. The list route
    must skip it, so no route succeeds and every resume-dependent row SKIPs; resuming it would
    PASS them instead, and the TCK would then prompt into the operator's session."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_lists_foreign_session.py",
        protocol_version=2,
        k="session_capabilities",
    )

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-002", "ACP-LIST-203", "ACP-RESUME-216"}, result.stdout
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
    ):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"
    assert "session/list has no session created in the TCK's own cwd" in result.stdout


def test_list_errors_when_empty_fails_list_002_only():
    """`list_errors_when_empty.py` errors instead of returning `{"sessions": []}` whenever the
    (possibly `cwd`-filtered) result set would be empty -- FAILs exactly `ACP-LIST-002` within its `-k` scope.
    `ACP-LIST-001`/`203`/`204` are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_errors_when_empty.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-002"}, result.stdout
    for req_id in ("ACP-LIST-001", "ACP-LIST-203", "ACP-LIST-204"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_close_responds_before_idle_fails_close_203_and_206_only():
    """`close_responds_before_idle.py` answers `session/close` before sending the cancelled idle
    for the work it cancelled -- FAILs `ACP-CLOSE-203`, and `ACP-CLOSE-206` too, since that idle
    is a `session/update` after the close response. The turn still ends `cancelled`, so
    `ACP-CLOSE-002`/`ACP-CANCEL-208` PASS."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "close_responds_before_idle.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="cancel or session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLOSE-203", "ACP-CLOSE-206"}, result.stdout
    for req_id in ("ACP-CLOSE-001", "ACP-CLOSE-002", "ACP-CANCEL-208"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_returns_source_id_fails_fork_201_only():
    """`fork_returns_source_id.py` answers `session/fork` with the source session's own id --
    FAILs `ACP-FORK-201` and `ACP-FORK-204` (which also needs a new id); `ACP-FORK-202` SKIPs (no
    forked session to prompt)."""
    result = _run_cli(FIXTURES_DIR_V2, "fork_returns_source_id.py", protocol_version=2, k="fork")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-201", "ACP-FORK-204"}, result.stdout
    assert statuses.get("ACP-FORK-202") == "SKIPPED", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_session_not_active_fails_fork_202_only():
    """`fork_session_not_active.py` returns a fresh forked id but rejects prompts on it --
    FAILs exactly `ACP-FORK-202` within its `-k` scope."""
    result = _run_cli(FIXTURES_DIR_V2, "fork_session_not_active.py", protocol_version=2, k="fork")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-202"}, result.stdout
    assert statuses.get("ACP-FORK-201") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_rejects_append_fails_sysprompt_001_only():
    """`system_prompt_rejects_append.py` advertises `session.systemPrompt` but rejects an
    `append` prompt -- FAILs exactly `ACP-SYSPROMPT-001` within its `-k` scope; `override` is not advertised, so
    `ACP-SYSPROMPT-202` SKIPs."""
    result = _run_cli(
        FIXTURES_DIR_V2, "system_prompt_rejects_append.py", protocol_version=2, k="system_prompt"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-001"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-202") == "SKIPPED", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_rejects_override_fails_sysprompt_202_only():
    """`system_prompt_rejects_override.py` advertises `session.systemPrompt.mode.override` but
    rejects an `override` prompt -- FAILs exactly `ACP-SYSPROMPT-202` within its `-k` scope."""
    result = _run_cli(
        FIXTURES_DIR_V2, "system_prompt_rejects_override.py", protocol_version=2, k="system_prompt"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-202"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-001") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def _sysprompt_test_statuses(report_path) -> dict[str, str]:
    """`{test function name: status}` for every test bound to an `ACP-SYSPROMPT-002/003` row."""
    report = json.loads(report_path.read_text())
    return {
        test["nodeid"].rsplit("::", 1)[-1]: test["status"]
        for req in report["requirements"]
        if req["id"] in ("ACP-SYSPROMPT-002", "ACP-SYSPROMPT-003")
        for test in req["tests"]
    }


def test_system_prompt_accepts_unsupported_mode_fails_sysprompt_002_only(tmp_path):
    """`system_prompt_accepts_unsupported_mode.py` applies an unsupported `systemPrompt.mode`
    instead of returning an error -- FAILs exactly `ACP-SYSPROMPT-002` within its `-k` scope, on both `session/new` and
    `session/resume`; `ACP-SYSPROMPT-003` PASSes."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "system_prompt_accepts_unsupported_mode.py",
        protocol_version=2,
        k="system_prompt",
        report_json=str(report_path),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-002"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-003") == "PASS", result.stdout
    assert _sysprompt_test_statuses(report_path) == {
        "test_new_session_with_unsupported_system_prompt_mode_errors": "FAIL",
        "test_resume_with_unsupported_system_prompt_mode_errors": "FAIL",
        "test_new_session_with_non_text_system_prompt_content_errors": "PASS",
        "test_resume_with_non_text_system_prompt_content_errors": "PASS",
    }
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_resume_accepts_non_text_fails_sysprompt_003_only(tmp_path):
    """`system_prompt_resume_accepts_non_text.py` refuses a non-text `systemPrompt` block on
    `session/new` but resumes the session anyway -- FAILs exactly `ACP-SYSPROMPT-003` within its `-k` scope, through its
    `session/resume` probe only; `ACP-SYSPROMPT-002` PASSes."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "system_prompt_resume_accepts_non_text.py",
        protocol_version=2,
        k="system_prompt",
        report_json=str(report_path),
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-SYSPROMPT-003"}, result.stdout
    assert statuses.get("ACP-SYSPROMPT-002") == "PASS", result.stdout
    assert _sysprompt_test_statuses(report_path) == {
        "test_new_session_with_unsupported_system_prompt_mode_errors": "PASS",
        "test_resume_with_unsupported_system_prompt_mode_errors": "PASS",
        "test_new_session_with_non_text_system_prompt_content_errors": "PASS",
        "test_resume_with_non_text_system_prompt_content_errors": "FAIL",
    }
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_system_prompt_without_persistence_skips_the_resume_probes(tmp_path):
    """`system_prompt_no_persistence.py` refuses unsupported prompts but cannot resume a session
    on a fresh process, so the resume probes SKIP ("cannot judge") instead of passing vacuously
    on the `-32002` it would answer anyway. No FAIL."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "system_prompt_no_persistence.py",
        protocol_version=2,
        k="system_prompt",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == set(), result.stdout
    assert _sysprompt_test_statuses(report_path) == {
        "test_new_session_with_unsupported_system_prompt_mode_errors": "PASS",
        "test_resume_with_unsupported_system_prompt_mode_errors": "SKIPPED",
        "test_new_session_with_non_text_system_prompt_content_errors": "PASS",
        "test_resume_with_non_text_system_prompt_content_errors": "SKIPPED",
    }
    report = json.loads(report_path.read_text())
    messages = [
        test["message"]
        for req in report["requirements"]
        if req["id"] in ("ACP-SYSPROMPT-002", "ACP-SYSPROMPT-003")
        for test in req["tests"]
        if test["status"] == "SKIPPED"
    ]
    assert messages and all("cannot judge" in message for message in messages), messages


def test_advertises_delete_but_errors_fails_delete_001_002_and_003():
    """`advertises_delete_but_errors.py` advertises `capabilities.session.delete` but always
    errors on `session/delete` -- FAILs `ACP-DELETE-001` (delete itself must succeed) and
    `ACP-DELETE-003` (cascades: the deleted session can't be observed gone). The ADVISORY
    `ACP-DELETE-002` also FAILs (the same underlying probe). `-32603` is not the tolerated
    `-32002`, so `ACP-DELETE-205` SKIPs (its prerequisite, a successful delete, is missing) and
    `ACP-DELETE-204` SKIPs on the race gate or the missing delete result."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "advertises_delete_but_errors.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-DELETE-001", "ACP-DELETE-003", "ACP-DELETE-002"}, result.stdout
    for req_id in ("ACP-DELETE-204", "ACP-DELETE-205"):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_list_matches_subdirectories_fails_list_203_only():
    """`list_matches_subdirectories.py` matches the `cwd` filter by prefix, so the subdirectory
    session `ACP-LIST-203` creates comes back under the parent filter -- FAILs exactly
    `ACP-LIST-203`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "list_matches_subdirectories.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-203"}, result.stdout
    assert statuses.get("ACP-LIST-002") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_list_accepts_relative_cwd_fails_list_205_only():
    """`list_accepts_relative_cwd.py` accepts a relative `cwd` filter instead of rejecting it --
    FAILs exactly `ACP-LIST-205` within its `-k` scope; `ACP-LIST-207` SKIPs (nothing was
    rejected, so no code to judge)."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_accepts_relative_cwd.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-205"}, result.stdout
    assert statuses.get("ACP-LIST-003") == "PASS", result.stdout
    assert statuses.get("ACP-LIST-207") == "SKIPPED", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_set_title_no_info_update_fails_list_208_only():
    """`set_title_no_info_update.py` advertises `session.title` and stores the title, but sends no
    `session_info_update` for it: the ADVISORY `ACP-LIST-208` FAILs alone within
    `-k session_capabilities`. `conforming_full.py` sends it and PASSes (its full run)."""
    statuses, stdout = _resume_statuses("set_title_no_info_update.py")
    assert _fails(statuses) == {"ACP-LIST-208"}, stdout
    assert statuses.get("ACP-LIST-209") == "SKIPPED", stdout  # no update to order


def test_set_title_info_update_after_response_fails_list_209_only():
    """`set_title_info_update_after_response.py` sends the `session_info_update` after the
    `session/set_title` response: the ADVISORY `ACP-LIST-209` FAILs alone and `ACP-LIST-208`
    PASSes, since the update arrives within the quiet drain."""
    statuses, stdout = _resume_statuses("set_title_info_update_after_response.py")
    assert _fails(statuses) == {"ACP-LIST-209"}, stdout
    assert statuses.get("ACP-LIST-208") == "PASS", stdout


def test_list_relative_cwd_wrong_code_fails_list_207_advisory_only():
    """`list_relative_cwd_wrong_code.py` rejects a relative `cwd` filter with `-32600`:
    `ACP-LIST-205` PASSes and the ADVISORY `ACP-LIST-207` FAILs (alone, within
    `-k session_capabilities`)."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_relative_cwd_wrong_code.py", protocol_version=2, k="session_capabilities"
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-207"}, result.stdout
    assert statuses.get("ACP-LIST-205") == "PASS", result.stdout


def test_list_ignores_invalid_cursor_fails_list_003_only():
    """`list_ignores_invalid_cursor.py` returns the first page for a never-issued cursor
    instead of `-32602` -- FAILs exactly `ACP-LIST-003` within its `-k` scope."""
    result = _run_cli(
        FIXTURES_DIR_V2, "list_ignores_invalid_cursor.py", protocol_version=2, k="session_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-LIST-003"}, result.stdout
    assert statuses.get("ACP-LIST-205") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_delete_does_not_cancel_active_fails_delete_204_only():
    """`delete_does_not_cancel_active.py` deletes a session but leaves its hanging `__hang__`
    turn running, so `ACP-DELETE-204` (run with `--cancel-prompt __hang__`) times out waiting
    for the cancelled idle -- FAILs exactly `ACP-DELETE-204` within its `-k` scope. Deleting an idle session
    (`ACP-DELETE-001`) is unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "delete_does_not_cancel_active.py",
        protocol_version=2,
        cancel_prompt="__hang__",
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-DELETE-204"}, result.stdout
    for req_id in ("ACP-DELETE-001", "ACP-DELETE-003", "ACP-DELETE-205"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_resume_after_delete_succeeds_fails_delete_205_only():
    """`resume_after_delete_succeeds.py` still resumes a deleted session instead of `-32002` --
    FAILs exactly `ACP-DELETE-205` within its `-k` scope; the session does leave `session/list`
    (`ACP-DELETE-003` PASSes)."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "resume_after_delete_succeeds.py",
        protocol_version=2,
        k="session_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-DELETE-205"}, result.stdout
    assert statuses.get("ACP-DELETE-003") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


_ARCHIVE_IDS = (
    "ACP-ARCHIVE-002",
    "ACP-ARCHIVE-003",
    "ACP-ARCHIVE-004",
    "ACP-ARCHIVE-005",
    "ACP-ARCHIVE-006",
    "ACP-ARCHIVE-201",
)


def _archive_run(fixture: str, *, expected_fails: set[str], expected_skips: set[str] = frozenset()):
    """Run `fixture` against the session-capability rows with `--cancel-prompt __hang__` (so
    `ACP-ARCHIVE-201` is exercised), assert the exact FAIL set, that the other archive ids PASS
    except `expected_skips`, and return `(statuses, stdout)`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        fixture,
        protocol_version=2,
        cancel_prompt="__hang__",
        k="session_capabilities",
    )
    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == expected_fails, result.stdout
    for req_id in _ARCHIVE_IDS:
        if req_id in expected_fails:
            continue
        expected = "SKIPPED" if req_id in expected_skips else "PASS"
        assert statuses.get(req_id) == expected, f"{req_id}: {result.stdout}"
    if expected_fails:  # a `-k`-scoped run is NOT CONFORMANT regardless (unbound MANDATORY ids)
        assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout
    return statuses, result.stdout


def test_conforming_full_passes_every_archive_row():
    """`conforming_full.py` advertises `archive` and `delete` and lists fresh sessions, so every
    archive row PASSes (`ACP-ARCHIVE-201` with `--cancel-prompt __hang__`)."""
    _archive_run("conforming_full.py", expected_fails=set())


def test_archive_omits_archived_flag_fails_archive_002_only():
    _archive_run("archive_omits_archived_flag.py", expected_fails={"ACP-ARCHIVE-002"})


def test_archive_still_listed_fails_archive_003_only():
    _archive_run("archive_still_listed.py", expected_fails={"ACP-ARCHIVE-003"})


def test_archive_rejecting_include_and_only_fails_the_views_that_need_them():
    """`archive_rejects_include_and_only.py` answers `-32602` for `include`/`only`:
    `ACP-ARCHIVE-002` (its `only` check), `-003` and `-006` each need one of those views."""
    _statuses, out = _archive_run(
        "archive_rejects_include_and_only.py",
        expected_fails={"ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-006"},
    )
    assert "docs/rfds/session-archive.mdx:112" in out, out


def test_archive_filter_falling_back_fails_archive_004_only():
    _archive_run("archive_filter_falls_back.py", expected_fails={"ACP-ARCHIVE-004"})


def test_archive_unknown_succeeding_fails_archive_005_only():
    _archive_run("archive_unknown_succeeds.py", expected_fails={"ACP-ARCHIVE-005"})


def test_archive_unknown_wrong_code_fails_archive_005_only():
    """`archive_unknown_wrong_code.py` fails an unknown session with `-32602`: an error, but not
    the `-32002` the docs name."""
    _statuses, out = _archive_run("archive_unknown_wrong_code.py", expected_fails={"ACP-ARCHIVE-005"})
    assert "expected code -32002" in out, out


def test_gated_by_auth_archive_skips_archive_005_instead_of_failing():
    """`gated_by_auth_archive.py` answers `-32000` to everything session-related until login.
    `ACP-ARCHIVE-005` creates a session first, so it SKIPs `AUTH-GATED:` rather than FAILing on
    `-32000` (within `-k session_capabilities`; the run is blocked by auth)."""
    fails, statuses, out = _fails_for("gated_by_auth_archive.py", "session_capabilities")
    assert fails == set(), out
    assert statuses.get("ACP-ARCHIVE-005") == "SKIPPED", out
    assert "auth-gated" in out.lower(), out


def test_archive_not_idempotent_fails_archive_005_only():
    _archive_run("archive_not_idempotent.py", expected_fails={"ACP-ARCHIVE-005"})


def test_archive_not_cancelling_fails_archive_201_only():
    """`archive_does_not_cancel.py` archives without cancelling a hanging `__hang__` turn, so the
    cancelled idle never arrives and the TCK's wait times out."""
    _archive_run("archive_does_not_cancel.py", expected_fails={"ACP-ARCHIVE-201"})


def test_delete_archiving_instead_fails_archive_006_only():
    """`delete_archives_instead.py` hides a deleted session from the default view only, so
    `ACP-DELETE-003` and `-205` still PASS."""
    statuses, _out = _archive_run("delete_archives_instead.py", expected_fails={"ACP-ARCHIVE-006"})
    assert statuses.get("ACP-DELETE-003") == "PASS", statuses
    assert statuses.get("ACP-DELETE-205") == "PASS", statuses


def test_archive_agent_listing_nothing_skips_the_view_comparisons_not_passes_them():
    """`archive_lists_nothing_unprompted.py` never lists a fresh session, so `ACP-ARCHIVE-002`,
    `-003` and `-006` SKIP rather than PASS vacuously; the rest still PASS."""
    _archive_run(
        "archive_lists_nothing_unprompted.py",
        expected_fails=set(),
        expected_skips={"ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-006"},
    )


def test_fork_unknown_source_invalid_params_fails_fork_203_only():
    """`fork_unknown_source_invalid_params.py` answers a fork of an unknown source with `-32602`
    instead of `-32002` -- FAILs exactly `ACP-FORK-203` within its `-k` scope."""
    result = _run_cli(
        FIXTURES_DIR_V2, "fork_unknown_source_invalid_params.py", protocol_version=2, k="fork"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-203"}, result.stdout
    for req_id in ("ACP-FORK-201", "ACP-FORK-202", "ACP-FORK-204"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_omitting_config_options_fails_fork_205_only():
    """`fork_omits_config_options.py` carries `configOptions` on `session/new` but drops it from
    the `session/fork` response -- FAILs exactly `ACP-FORK-205` within `-k fork`."""
    fixture = "fork_omits_config_options.py"
    result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="fork")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-205"}, result.stdout
    for req_id in ("ACP-FORK-201", "ACP-FORK-202"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_fork_requires_active_source_fails_fork_204_only():
    """`fork_requires_active_source.py` forks only active sessions and answers a closed (still
    listed) source with `-32002` -- FAILs exactly `ACP-FORK-204` within its `-k` scope."""
    result = _run_cli(
        FIXTURES_DIR_V2, "fork_requires_active_source.py", protocol_version=2, k="fork"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-FORK-204"}, result.stdout
    assert statuses.get("ACP-FORK-203") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_adddirs_accepts_relative_fails_adddirs_203_only():
    fails, statuses, out = _fails_for("adddirs_accepts_relative.py", _SETUP_K)
    assert fails == {"ACP-ADDDIRS-203"}, out
    assert statuses.get("ACP-ADDDIRS-001") == "PASS", out
    assert statuses.get("ACP-ADDDIRS-202") == "PASS", out


def test_rejects_unadvertised_dirs_fails_adddirs_204_only():
    """The agent advertises no `additionalDirectories` but rejects `session/new` carrying it:
    only the ADVISORY `ACP-ADDDIRS-204` FAILs; the capability-gated rows SKIP."""
    fails, statuses, out = _fails_for("rejects_unadvertised_dirs.py", _SETUP_K)
    assert fails == {"ACP-ADDDIRS-204"}, out
    for req_id in ("ACP-ADDDIRS-001", "ACP-ADDDIRS-202", "ACP-ADDDIRS-203"):
        assert statuses.get(req_id) == "SKIPPED", out


def test_conforming_passes_adddirs_204_and_advertising_agent_skips_it():
    fails, statuses, out = _fails_for("conforming.py", _SETUP_K)
    assert fails == set(), out
    assert statuses.get("ACP-ADDDIRS-204") == "PASS", out
    _, statuses, out = _fails_for("adddirs_accepts_relative.py", _SETUP_K)
    assert statuses.get("ACP-ADDDIRS-204") == "SKIPPED", out


def test_mcp_unsupported_transport_fixtures_fail_mcp_203_only():
    """One fixture per probe: `sse` accepted, a `_`-prefixed custom type accepted, or an `acp`
    declaration accepted by an agent that does not advertise `capabilities.session.mcp.acp`."""
    for fixture in (
        "accepts_sse_mcp.py",
        "accepts_custom_mcp_transport.py",
        "accepts_unadvertised_acp_mcp.py",
    ):
        fails, _statuses, out = _fails_for(fixture, _SETUP_K)
        assert fails == {"ACP-MCP-203"}, f"{fixture}:\n{out}"


def test_accepts_duplicate_mcp_names_fails_mcp_204_advisory_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "accepts_duplicate_mcp_names.py", protocol_version=2, k=_SETUP_K
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-MCP-204"}, result.stdout
    assert statuses.get("ACP-MCP-203") == "PASS", result.stdout


def test_updates_after_close_fails_close_206_only():
    fails, statuses, out = _fails_for("updates_after_close.py", "session_capabilities")
    assert fails == {"ACP-CLOSE-206"}, out
    assert statuses.get("ACP-CLOSE-001") == "PASS", out


def test_close_twice_errors_fails_close_003_advisory_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "close_twice_errors.py", protocol_version=2, k="session_capabilities"
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-CLOSE-003"}, result.stdout
    assert statuses.get("ACP-CLOSE-001") == "PASS", result.stdout


def test_closes_before_prompt_passes_close_204_with_not_active_outcome(tmp_path):
    """`closes_before_prompt.py` answers a prompt sent just before a close `-32002`, since it
    processed the close first. A legal outcome: `ACP-CLOSE-204` PASSes and records `not_active`."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        FIXTURES_DIR_V2,
        "closes_before_prompt.py",
        protocol_version=2,
        k="test_prompt_pending_at_close_is_answered",
        cancel_prompt="__close_first__",
        report_json=str(report_path),
    )
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLOSE-204") == "PASS", result.stdout
    assert _fails(statuses) == set(), result.stdout
    by_id = {r["id"]: r for r in json.loads(report_path.read_text())["requirements"]}
    assert "not_active" in json.dumps(by_id["ACP-CLOSE-204"]), by_id["ACP-CLOSE-204"]


def test_leaks_mcp_credentials_fixtures_fail_session_006_advisory_only():
    """One fixture per leak channel: env values in `_meta` (stdout), stderr, the stub's command
    line, and header values in `_meta`. The other MCP rows still PASS."""
    for fixture in (
        "leaks_mcp_env_meta.py",
        "leaks_mcp_env_stderr.py",
        "leaks_mcp_env_argv.py",
        "leaks_mcp_header_meta.py",
    ):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=_SETUP_K)
        statuses = _table_statuses(result.stdout)
        assert _fails(statuses) == {"ACP-SESSION-006"}, f"{fixture}:\n{result.stdout}"
        for req_id in ("ACP-MCP-201", "ACP-MCP-202", "ACP-MCP-203", "ACP-MCP-204"):
            assert statuses.get(req_id) == "PASS", f"{fixture} {req_id}:\n{result.stdout}"
