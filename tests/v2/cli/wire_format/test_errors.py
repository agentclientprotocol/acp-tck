"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_errors.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails_for, _run_cli, _table_statuses


def test_answers_unadvertised_options_fails_error_006_only():
    """`answers_unadvertised_options.py` serves `session/options` without advertising `session.options`
    -- MANDATORY, so the verdict is NOT CONFORMANT. The `ACP-OPTIONS-*` rows SKIP."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_unadvertised_options.py", protocol_version=2, k=_ERROR_K)
    statuses = _table_statuses(result.stdout)
    fails = {r for r, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-ERROR-006"}, result.stdout
    assert "session/options" in result.stdout, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_answers_unadvertised_archive_fails_error_006_only():
    """`answers_unadvertised_archive.py` serves `session/archive`/`session/unarchive` without
    advertising `session.archive` -- MANDATORY, so the verdict is NOT CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_unadvertised_archive.py", protocol_version=2, k=_ERROR_K)
    statuses = _table_statuses(result.stdout)
    fails = {r for r, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-ERROR-006"}, result.stdout
    assert "session/archive" in result.stdout, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


_ERROR_K = "test_errors or resume_unknown_session"


def test_unknown_session_wrong_code_fails_error_003_only():
    """`unknown_session_wrong_code.py` answers a prompt for a never-created or closed session with
    `-32602`; resume still answers `-32002`, so `ACP-ERROR-004` PASSes."""
    fails, statuses, out = _fails_for("unknown_session_wrong_code.py", _ERROR_K)
    assert fails == {"ACP-ERROR-003"}, out
    assert statuses.get("ACP-ERROR-004") == "PASS", out
    assert statuses.get("ACP-ERROR-006") == "PASS", out


def test_unknown_session_no_data_fails_error_003_and_004():
    """`unknown_session_no_data.py` answers `-32002` without `data.sessionId`; the two rows share
    one assertion, so both FAIL."""
    fails, _statuses, out = _fails_for("unknown_session_no_data.py", _ERROR_K)
    assert fails == {"ACP-ERROR-003", "ACP-ERROR-004"}, out


def test_resume_accepts_unknown_session_fails_error_004_only():
    fails, statuses, out = _fails_for("resume_accepts_unknown_session.py", _ERROR_K)
    assert fails == {"ACP-ERROR-004"}, out
    assert statuses.get("ACP-ERROR-003") == "PASS", out


def test_set_config_option_accepts_unknown_session_fails_error_004_only():
    """With `configOptions` advertised, the `set_config_option` probe runs and FAILs `ACP-ERROR-004`
    while `ACP-ERROR-003`'s two `session/prompt` probes PASS (the fixture's prompt handler is
    conforming)."""
    fails, statuses, out = _fails_for("set_config_option_accepts_unknown_session.py", _ERROR_K)
    assert fails == {"ACP-ERROR-004"}, out
    assert statuses.get("ACP-ERROR-003") == "PASS", out
    assert "session/set_config_option" in out, out


def test_answers_unadvertised_delete_fails_error_006_only():
    """`answers_unadvertised_delete.py` serves `session/delete` without advertising
    `session.delete` -- MANDATORY, so the verdict is NOT CONFORMANT."""
    result = _run_cli(FIXTURES_DIR_V2, "answers_unadvertised_delete.py", protocol_version=2, k=_ERROR_K)
    statuses = _table_statuses(result.stdout)
    fails = {r for r, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-ERROR-006"}, result.stdout
    assert "session/delete" in result.stdout, result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_reserved_range_custom_code_fails_error_008_only():
    fails, statuses, out = _fails_for("reserved_range_custom_code.py", _ERROR_K)
    assert fails == {"ACP-ERROR-008"}, out
    assert "-32050" in out, out


def test_parse_error_wrong_code_fails_error_204_only():
    fails, _statuses, out = _fails_for("parse_error_wrong_code.py", "test_errors or test_informational")
    assert fails == {"ACP-ERROR-204"}, out
    assert "expected code -32700" in out, out


def test_parse_error_non_null_id_fails_error_204_only():
    fails, _statuses, out = _fails_for("parse_error_non_null_id.py", "test_errors or test_informational")
    assert fails == {"ACP-ERROR-204"}, out
    assert "expected id null" in out, out


def test_no_session_capability_agent_passes_unadvertised_probes():
    """`no_session_capability.py` answers every `session/*` method with `-32601`, so
    `ACP-ERROR-006` PASSes with the whole `session/*` baseline unadvertised; the session-scoped
    rows SKIP."""
    fails, statuses, out = _fails_for("no_session_capability.py", _ERROR_K)
    assert fails == set(), out
    assert statuses.get("ACP-ERROR-006") == "PASS", out
    assert statuses.get("ACP-ERROR-003") == "SKIPPED", out
    assert statuses.get("ACP-ERROR-004") == "SKIPPED", out
