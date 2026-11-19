"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_session_config.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_mode_update_uses_modeId_fails_modes_002_only():
    """`mode_update_uses_modeId.py` advertises `modes` and emits a `current_mode_update` with
    the docs-bug field name `modeId` instead of the schema-true `currentModeId` --
    ACP-MODES-001 (which never inspects a mode-update notification) still PASSes."""
    result = _run_cli("mode_update_uses_modeId.py", k="mode")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-MODES-001") == "PASS", result.stdout
    assert statuses.get("ACP-MODES-002") == "FAIL", result.stdout


def test_config_partial_list_fails_config_002_only():
    """`config_partial_list.py` advertises `configOptions` and answers `session/set_config_option`
    with only the changed option, not the complete list -- ACP-CONFIG-001 (which only checks
    `session/new`'s own configOptions) still PASSes."""
    result = _run_cli("config_partial_list.py", k="config")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CONFIG-001") == "PASS", result.stdout
    assert statuses.get("ACP-CONFIG-002") == "FAIL", result.stdout


def test_boolean_option_unadvertised_fails_config_003():
    """`boolean_option_unadvertised.py` advertises a `type: "boolean"` config option even to a
    client that never advertised `clientCapabilities.session.configOptions.boolean` -- a
    MANDATORY (Req 33) FAIL, which must flip the overall verdict."""
    result = _run_cli("boolean_option_unadvertised.py")
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CONFIG-003") == "FAIL", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_boolean_option_on_set_fails_config_003_only():
    """The boolean option is hidden from `session/new` but leaked by `set_config_option`."""
    result = _run_cli("boolean_option_on_set.py")
    assert result.returncode != 0
    assert _output_fail_ids(result.stdout) == {"ACP-CONFIG-003"}, result.stdout
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CONFIG-001") == "PASS", result.stdout
    assert statuses.get("ACP-CONFIG-002") == "PASS", result.stdout


def test_config_003_does_not_fail_on_an_unanswered_session_options():
    """`options_never_answers.py` never answers `session/options`; that is ACP-OPTIONS-001's
    finding, so the MANDATORY ACP-CONFIG-003 judges the payloads it got and PASSes."""
    result = _run_cli("options_never_answers.py", k="test_session_config")
    assert _output_fail_ids(result.stdout) == set(), result.stdout
    assert _table_statuses(result.stdout)["ACP-CONFIG-003"] == "PASS", result.stdout


def test_conforming_options_pass_non_vacuously_and_conforming_skips():
    """`conforming_full.py` advertises `options`, `list`, `loadSession` and persists sessions, so
    ACP-OPTIONS-001/002/003/009 PASS (009 reconnects from a fresh process) and ACP-CONFIG-003 stays
    PASS with `session/options` judged; `conforming.py` advertises nothing and SKIPs all four."""
    scope = "test_session_options or test_session_config"
    full = _table_statuses(_run_cli("conforming_full.py", k=scope).stdout)
    assert [full[f"ACP-OPTIONS-00{n}"] for n in (1, 2, 3, 9)] == ["PASS"] * 4, full
    assert full["ACP-CONFIG-003"] == "PASS", full
    plain = _table_statuses(_run_cli("conforming.py", k=scope).stdout)
    assert {plain[f"ACP-OPTIONS-00{n}"] for n in (1, 2, 3, 9)} == {"SKIPPED"}, plain
