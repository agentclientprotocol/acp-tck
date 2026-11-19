"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_session_capabilities.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_asks_permission_closable_agent_passes_close_002():
    """`asks_permission_closable.py` combines `asks_permission.py`'s mid-turn
    `session/request_permission` with `sessionCapabilities.close` support: `session/close` on
    an in-flight, permission-pending prompt must resolve it as cancelled. `run_prompt`'s
    dispatcher (which answers any agent -> client request while waiting for the prompt's own
    response) is what makes this PASS deterministically, instead of deadlocking on the
    unanswered permission request.

    Uses a longer `--timeout` than this module's default (`_run_cli`'s `timeout="1"`) because the
    fixture deliberately delays its permission request past `run_prompt`'s short post-update peek
    window to keep the close-vs-permission race deterministic (see the fixture's docstring).
    Scoped to `close`: every prompt turn against this fixture pays that same deliberate delay,
    so an unscoped run against the full suite costs 30+s just from that, for no attribution
    benefit over the `session_capabilities`-only subset."""
    result = _run_cli(
        "asks_permission_closable.py", timeout="5", k="close", cancel_prompt="__hang__"
    )
    assert result.returncode != 0  # `-k`-scoped: MANDATORY ids are NOT_TESTED, verdict non-zero

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLOSE-002") == "PASS", f"expected PASS:\n{result.stdout}"
    assert statuses.get("ACP-CLOSE-001") == "PASS", f"expected PASS:\n{result.stdout}"


def test_close_not_idempotent_fails_close_003_advisory_only():
    """`close_not_idempotent.py` answers a second close, and a close of a never-created id, with
    `-32002` instead of the empty result -- an ADVISORY FAIL, so the run stays CONFORMANT."""
    result = _run_cli("close_not_idempotent.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert _output_fail_ids(result.stdout) == {"ACP-CLOSE-003"}, result.stdout
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLOSE-001") == "PASS", result.stdout
    assert statuses.get("ACP-ERROR-003") == "PASS", result.stdout


def test_delete_keeps_listing_fails_delete_003_only():
    result = _run_cli("delete_keeps_listing.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-DELETE-003"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-DELETE-001", "ACP-DELETE-002", "ACP-LIST-001", "ACP-LIST-002"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_list_ignores_bad_cursor_fails_list_003_advisory_only():
    """`list_ignores_bad_cursor.py` answers a never-issued cursor with a result instead of
    `-32602` -- an ADVISORY FAIL, so the run stays CONFORMANT."""
    result = _run_cli("list_ignores_bad_cursor.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout
    assert _output_fail_ids(result.stdout) == {"ACP-LIST-003"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-LIST-001", "ACP-LIST-002"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_archive_without_list_fails_archive_001_only():
    """`archive_without_list.py` advertises `archive` but not `list`: ACP-ARCHIVE-001 FAILs, the
    archive tests that also need `list` SKIP, and ACP-ARCHIVE-005 (archive/unarchive only) PASSes."""
    result = _run_cli("archive_without_list.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-001"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-004", "ACP-ARCHIVE-006"):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}:\n{result.stdout}"
    assert statuses.get("ACP-ARCHIVE-005") == "PASS", result.stdout


def test_archive_omits_archived_flag_fails_archive_002_only():
    result = _run_cli("archive_omits_archived_flag.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-002"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-001", "ACP-ARCHIVE-003", "ACP-ARCHIVE-004", "ACP-ARCHIVE-005", "ACP-ARCHIVE-006"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_archive_still_listed_fails_archive_003_only():
    result = _run_cli("archive_still_listed.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-003"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-001", "ACP-ARCHIVE-002", "ACP-ARCHIVE-004", "ACP-ARCHIVE-005", "ACP-ARCHIVE-006"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_archive_filter_falling_back_fails_archive_004_only():
    result = _run_cli("archive_filter_falls_back.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-004"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-001", "ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-005", "ACP-ARCHIVE-006"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_archive_rejecting_include_and_only_fails_the_views_that_need_them():
    """`archive_rejects_include_and_only.py` answers `-32602` for `include`/`only`: ACP-ARCHIVE-002
    (lists `only`), -003 (`only`) and -006 (`include`) FAIL, citing the Draft RFD's MUST."""
    result = _run_cli("archive_rejects_include_and_only.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-006"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-001", "ACP-ARCHIVE-004", "ACP-ARCHIVE-005"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_archive_agent_listing_nothing_skips_the_view_comparisons_not_passes_them():
    """`archive_lists_nothing_unprompted.py` never lists a fresh session, so ACP-ARCHIVE-002, -003
    and -006 SKIP (the last used to PASS vacuously)."""
    result = _run_cli("archive_lists_nothing_unprompted.py")
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-006"):
        assert statuses.get(req_id) == "SKIPPED", f"{req_id}:\n{result.stdout}"


def test_archive_unknown_succeeding_fails_archive_005_only():
    result = _run_cli("archive_unknown_succeeds.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-005"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-ARCHIVE-001", "ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-004", "ACP-ARCHIVE-006"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_delete_archiving_instead_fails_archive_006_only():
    """`delete_archives_instead.py` hides a deleted session from the default view only, so
    ACP-DELETE-003 PASSes while ACP-ARCHIVE-006 FAILs."""
    result = _run_cli("delete_archives_instead.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-ARCHIVE-006"}, result.stdout
    statuses = _table_statuses(result.stdout)
    for req_id in ("ACP-DELETE-003", "ACP-ARCHIVE-001", "ACP-ARCHIVE-002", "ACP-ARCHIVE-003", "ACP-ARCHIVE-004", "ACP-ARCHIVE-005"):
        assert statuses.get(req_id) == "PASS", f"{req_id}:\n{result.stdout}"


def test_delete_answering_not_found_still_runs_the_list_check():
    """`delete_answers_not_found.py` answers `session/delete` for a closed (or never-created)
    session with `-32002`: only the ADVISORY ACP-DELETE-002 FAILs. ACP-DELETE-001 and -003 treat
    the `-32002` after the TCK's close as a successful delete and PASS (the latter on the list
    check), so the run stays CONFORMANT."""
    result = _run_cli("delete_answers_not_found.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _output_fail_ids(result.stdout) == {"ACP-DELETE-002"}, result.stdout
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-DELETE-001") == "PASS", result.stdout
    assert statuses.get("ACP-DELETE-003") == "PASS", result.stdout


def test_refusing_to_delete_an_active_session_skips_delete_001_and_003():
    """Deleting an active session is implementation-defined; without `close` to end it first,
    an error SKIPs instead of failing a conforming agent."""
    result = _run_cli("refuses_deleting_active_session.py")
    assert result.returncode == 0, result.stdout + result.stderr
    statuses = _table_statuses(result.stdout)
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    assert statuses.get("ACP-DELETE-001") == "SKIPPED", result.stdout
    assert statuses.get("ACP-DELETE-003") == "SKIPPED", result.stdout
    assert statuses.get("ACP-DELETE-002") == "PASS", result.stdout
    assert "deleting an active session is implementation-defined" in result.stdout, result.stdout


def test_system_prompt_lenient_fails_sysprompt_002_and_003():
    result = _run_cli("system_prompt_lenient.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-SYSPROMPT-002", "ACP-SYSPROMPT-003"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-SYSPROMPT-001") == "PASS", result.stdout


def test_system_prompt_rejected_fails_sysprompt_001_only():
    result = _run_cli("system_prompt_rejected.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-SYSPROMPT-001"}, result.stdout


def test_system_prompt_load_ignoring_content_fails_sysprompt_003_only():
    """`session/load` loads the session despite a non-text `systemPrompt` block."""
    result = _run_cli("system_prompt_load_ignores_content.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-SYSPROMPT-003"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-SYSPROMPT-002") == "PASS", result.stdout


def test_system_prompt_resume_ignoring_mode_fails_sysprompt_002_only():
    """`session/resume` resumes the session despite an unsupported `systemPrompt` mode."""
    result = _run_cli("system_prompt_resume_ignores_mode.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-SYSPROMPT-002"}, result.stdout
    assert _table_statuses(result.stdout).get("ACP-SYSPROMPT-003") == "PASS", result.stdout


def test_system_prompt_probes_skip_when_agent_cannot_restore_sessions(tmp_path):
    """The load/resume probes need the agent to load the session without a `systemPrompt`
    first; one that only keeps sessions in memory SKIPs them instead of passing vacuously."""
    report_path = tmp_path / "report.json"
    result = _run_cli(
        "system_prompt_no_restore.py",
        k="system_prompt and (load or resume)",
        report_json=str(report_path),
    )
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    report = json.loads(report_path.read_text())
    by_id = {r["id"]: r for r in report["requirements"]}
    for req_id in ("ACP-SYSPROMPT-002", "ACP-SYSPROMPT-003"):
        tests = by_id[req_id]["tests"]
        assert len(tests) == 2, tests
        for test in tests:
            assert test["status"] == "SKIPPED", test
            assert "cannot judge" in test["message"], test
