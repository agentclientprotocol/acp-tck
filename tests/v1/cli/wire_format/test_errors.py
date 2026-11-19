"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_errors.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _fail_ids, _run_cli, _table_statuses


def test_unknown_session_wrong_code_fails_error_003_advisory_only():
    """`unknown_session_wrong_code.py` answers a prompt for an unknown session with `-32602`
    instead of `-32002` + `data.sessionId` -- ADVISORY, so the verdict stays CONFORMANT."""
    result = _run_cli("unknown_session_wrong_code.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-003"}, result.stdout


def test_load_upserts_unknown_session_fails_error_004_advisory_only():
    """`load_upserts_unknown_session.py` advertises `loadSession` and `resume` but creates the
    session on `session/load`/`session/resume` of an unknown id instead of answering `-32002`."""
    result = _run_cli("load_upserts_unknown_session.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-004"}, result.stdout
    assert statuses["ACP-ERROR-003"] == "PASS", result.stdout


def test_set_unknown_session_accepts_fails_error_004_advisory_only():
    """`set_unknown_session_accepts.py` advertises modes and a select config option but answers
    `session/set_mode`/`session/set_config_option` for an unknown session with a success."""
    result = _run_cli("set_unknown_session_accepts.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-004"}, result.stdout
    assert statuses["ACP-ERROR-003"] == "PASS", result.stdout
    assert statuses["ACP-ERROR-007"] == "PASS", result.stdout


def test_serves_before_initialize_fails_error_005_advisory_only():
    """`serves_before_initialize.py` serves a `session/new` that arrives before `initialize`
    instead of answering `-32600`."""
    result = _run_cli("serves_before_initialize.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-005"}, result.stdout


def test_implements_unadvertised_list_fails_error_006_advisory_only():
    """`implements_unadvertised_list.py` answers `session/list` without advertising
    `sessionCapabilities.list`; its other unadvertised gated methods still get `-32601`."""
    result = _run_cli("implements_unadvertised_list.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-006"}, result.stdout


def test_auth_required_probe_does_not_hide_an_earlier_error_006_failure():
    """`unadvertised_load_then_list_auth_required.py` serves unadvertised `session/load`, then
    answers unadvertised `session/list` with `-32000`: the `-32000` SKIP must not discard the
    problem already found."""
    result = _run_cli("unadvertised_load_then_list_auth_required.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _fail_ids(_table_statuses(result.stdout)) == {"ACP-ERROR-006"}, result.stdout


def test_set_unknown_value_accepts_fails_error_007_advisory_only():
    """`set_mode_unknown_accepts.py` / `set_config_option_unknown_accepts.py` accept a
    `session/set_mode` / `session/set_config_option` naming a mode, config option or value they
    never offered, instead of `-32602`. Each advertises only one of the two surfaces."""
    for fixture in ("set_mode_unknown_accepts.py", "set_config_option_unknown_accepts.py"):
        result = _run_cli(fixture)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

        statuses = _table_statuses(result.stdout)
        assert _fail_ids(statuses) == {"ACP-ERROR-007"}, f"{fixture}: {result.stdout}"


def test_legacy_server_error_code_fails_error_008_and_jsonrpc_004_advisory_only():
    """`legacy_server_error_code.py` answers an unrecognised method with `-32001`, a code in the
    reserved range that ACP does not define -- also not the `-32601` ACP-JSONRPC-004 wants."""
    result = _run_cli("legacy_server_error_code.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: CONFORMANT" in result.stdout, result.stdout

    statuses = _table_statuses(result.stdout)
    assert _fail_ids(statuses) == {"ACP-ERROR-008", "ACP-JSONRPC-004"}, result.stdout
