"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_session_config.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails_for, _run_cli, _table_statuses


def test_conforming_options_pass_non_vacuously_and_conforming_skips():
    """`conforming_full.py` advertises `options` and `mcp.stdio`, so ACP-OPTIONS-001/002/003/009 PASS
    (009 reconnects on one connection), and ACP-CONFIG-001/210, ACP-COMMANDS-201 and ACP-CLIENTCAP-203
    stay PASS with the `session/options` result judged; `conforming.py` advertises nothing and SKIPs
    the four ACP-OPTIONS rows."""
    scope = "test_session_options or test_session_config or test_slash_commands or test_client_capabilities"
    full = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=scope).stdout)
    assert [full[f"ACP-OPTIONS-00{n}"] for n in (1, 2, 3, 9)] == ["PASS"] * 4, full
    for req_id in ("ACP-CONFIG-001", "ACP-CONFIG-210", "ACP-COMMANDS-201", "ACP-CLIENTCAP-203"):
        assert full[req_id] == "PASS", full
    plain = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k=scope).stdout)
    assert {plain[f"ACP-OPTIONS-00{n}"] for n in (1, 2, 3, 9)} == {"SKIPPED"}, plain


def test_config_set_omits_changed_option_fails_config_002_only():
    """`config_set_omits_changed_option.py` advertises two independent `configOptions` entries
    but `session/set_config_option` replies with a list missing the option it just changed --
    FAILs exactly `ACP-CONFIG-002` within its `-k` scope. `ACP-CONFIG-001`/`201`/`203`/`206` are unaffected."""
    result = _run_cli(
        FIXTURES_DIR_V2, "config_set_omits_changed_option.py", protocol_version=2, k="session_config"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CONFIG-002"}, result.stdout
    for req_id in ("ACP-CONFIG-201", "ACP-CONFIG-203", "ACP-CONFIG-001", "ACP-CONFIG-206"):
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


_CONFIG_K = "session_config"
_CONFIG_RULE_IDS = {
    f"ACP-CONFIG-{n}" for n in ("001", "002", "201", "203", "206", "207", "208", "209", "210", "211", "212")
}


def _config_fixture_run(fixture: str, k: str = _CONFIG_K) -> tuple[set[str], dict[str, str], str]:
    fails, statuses, out = _fails_for(fixture, k)
    return fails, statuses, out


def test_config_set_unknown_id_accepted_fails_config_207_only():
    """The fixture answers an unadvertised `configId` with success (FAILs exactly
    `ACP-CONFIG-207` within `-k session_config`); it has one option, so `ACP-CONFIG-209` has
    nothing to observe through and SKIPs."""
    fails, statuses, out = _config_fixture_run("config_set_unknown_id_accepted.py")
    assert fails == {"ACP-CONFIG-207"}, out
    assert statuses.get("ACP-CONFIG-208") == "PASS", out
    assert statuses.get("ACP-CONFIG-209") == "SKIPPED", out


def test_config_set_invalid_value_wrong_code_fails_config_208_only():
    """One option only, so `ACP-CONFIG-209` has nothing to observe through and SKIPs rather
    than passing vacuously."""
    fails, statuses, out = _config_fixture_run("config_set_invalid_value_wrong_code.py")
    assert fails == {"ACP-CONFIG-208"}, out
    assert statuses.get("ACP-CONFIG-207") == "PASS", out
    assert statuses.get("ACP-CONFIG-209") == "SKIPPED", out


def test_config_set_invalid_value_mutates_fails_config_209_only():
    fails, statuses, out = _config_fixture_run("config_set_invalid_value_mutates.py")
    assert fails == {"ACP-CONFIG-209"}, out
    assert statuses.get("ACP-CONFIG-207") == "PASS", out
    assert statuses.get("ACP-CONFIG-208") == "PASS", out


def test_config_duplicate_select_values_fails_config_210_only():
    fails, statuses, out = _config_fixture_run("config_duplicate_select_values.py")
    assert fails == {"ACP-CONFIG-210"}, out
    assert statuses.get("ACP-CONFIG-201") == "PASS", out
    assert statuses.get("ACP-CONFIG-001") == "PASS", out


def test_config_set_no_update_notification_fails_config_211_only():
    """No update at all, so there is nothing for `ACP-CONFIG-212` to order: it SKIPs."""
    fails, statuses, out = _config_fixture_run("config_set_no_update_notification.py")
    assert fails == {"ACP-CONFIG-211"}, out
    assert statuses.get("ACP-CONFIG-212") == "SKIPPED", out


def test_config_update_after_response_fails_config_212_only():
    fails, statuses, out = _config_fixture_run("config_update_after_response.py")
    assert fails == {"ACP-CONFIG-212"}, out
    assert statuses.get("ACP-CONFIG-211") == "PASS", out


def test_conforming_full_passes_every_config_rule():
    """`conforming_full.py` advertises a select and a boolean option, so every config rule PASSes."""
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=_CONFIG_K
    )
    statuses = _table_statuses(result.stdout)
    for req_id in _CONFIG_RULE_IDS:
        assert statuses.get(req_id) == "PASS", f"{req_id}: {result.stdout}"
