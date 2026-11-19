"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_initial_config.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

import json

from .._runner import FIXTURES_DIR_V2, _fails, _recorded, _run_cli, _table_statuses


def test_initial_config_defect_fixtures_fail_only_their_own_rows():
    """Each fixture advertises `session.options` with a select and a boolean option and breaks one
    initial-`configOptions` rule. The `options_fork_*` ones also advertise `fork` and break the rule
    only on `session/fork` (`options_fork_notice_before_response.py` sends its early `notice` only
    for a fork with entries). Everything else PASSes or SKIPs. The run is scoped with `-k`, so its
    verdict is not asserted."""
    ids = [f"ACP-OPTIONS-{n:03}" for n in (4, 5, 6, 7, 8, 10, 11, 201)]
    for fixture, expected in (
        ("options_accepts_malformed.py", {"ACP-OPTIONS-004"}),
        ("options_accepts_duplicate.py", {"ACP-OPTIONS-005"}),
        ("options_rejects_unknown_entry.py", {"ACP-OPTIONS-006"}),
        ("options_notifies_initial.py", {"ACP-OPTIONS-007"}),
        ("options_notice_before_response.py", {"ACP-OPTIONS-008"}),
        ("options_fork_notice_before_response.py", {"ACP-OPTIONS-008"}),
        ("options_response_hides_values.py", {"ACP-OPTIONS-011"}),
        ("options_ignores_unsupported_type.py", set()),
        ("options_fork_accepts_malformed.py", {"ACP-OPTIONS-004"}),
        ("options_fork_accepts_duplicate.py", {"ACP-OPTIONS-005"}),
        ("options_fork_rejects_unknown_entry.py", {"ACP-OPTIONS-006"}),
    ):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_initial_config")
        statuses = _table_statuses(result.stdout)
        fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
        assert fails == expected, f"{fixture}:\n{result.stdout}"
        for req_id in set(ids) - expected:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"


def test_duplicate_probe_uses_a_real_boolean_option_when_there_is_no_select():
    """`options_only_boolean.py` lists only a boolean option and ignores unknown ids before looking
    for duplicates. ACP-OPTIONS-005 duplicates the real boolean option rather than a synthetic id,
    so the agent's `-32602` is judged and the row PASSes."""
    result = _run_cli(FIXTURES_DIR_V2, "options_only_boolean.py", protocol_version=2, k="test_initial_config")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-OPTIONS-005"] == "PASS", result.stdout


def test_early_updates_not_caused_by_initial_entries_pass_options_008():
    """`options_idle_before_response.py` sends the initial idle `state_update` before the response
    only when the request carries entries (session-setup.mdx:100-103 allow it on either side);
    `options_usage_overtakes_response.py` sends a `usage_update` just after a plain `session/new`
    response and before one with entries. Neither is caused by the entries, so ACP-OPTIONS-008
    PASSes and nothing FAILs."""
    for fixture in ("options_idle_before_response.py", "options_usage_overtakes_response.py"):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="test_initial_config")
        statuses = _table_statuses(result.stdout)
        assert _fails(statuses) == set(), f"{fixture}:\n{result.stdout}"
        assert statuses["ACP-OPTIONS-008"] == "PASS", f"{fixture}:\n{result.stdout}"


def test_a_fork_that_always_fails_fails_only_the_fork_row():
    """`options_fork_always_fails.py` advertises `fork` but every `session/fork` fails with
    `-32603`. Only ACP-FORK-201 FAILs: the initial-config rows leave the fork out and PASS on
    `session/new`."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "options_fork_always_fails.py",
        protocol_version=2,
        k="test_initial_config or test_fork_session_returns_a_new_session",
    )
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == {"ACP-FORK-201"}, result.stdout
    for n in (4, 5, 6, 8):
        assert statuses[f"ACP-OPTIONS-{n:03}"] == "PASS", result.stdout


def test_conforming_initial_config_passes_non_vacuously_and_conforming_skips(tmp_path):
    """`conforming_full.py` applies initial entries, ignores inapplicable ones and reports the real
    values, so every ACP-OPTIONS row of the initial-value family PASSes (010 and 201 record and PASS);
    `conforming.py` advertises no `options` and SKIPs them all. ACP-OPTIONS-201 records `rejected with
    -32602` for the fixture that rejects an unsupported value `type` and `ignored` for the one that
    ignores it."""
    ids = [f"ACP-OPTIONS-{n:03}" for n in (4, 5, 6, 7, 8, 10, 11, 201)]
    report_path = tmp_path / "full.json"
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k="test_initial_config",
        report_json=str(report_path),
    )
    full = _table_statuses(result.stdout)
    assert {full[i] for i in ids} == {"PASS"}, full
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    assert _recorded(by_id, "ACP-OPTIONS-201")["acp_tck_options_unsupported_type_outcome"] == "rejected with -32602"
    assert _recorded(by_id, "ACP-OPTIONS-010")["acp_tck_initial_value_applied"] == "True"
    report_path = tmp_path / "ignores.json"
    _run_cli(
        FIXTURES_DIR_V2, "options_ignores_unsupported_type.py", protocol_version=2, k="test_initial_config",
        report_json=str(report_path),
    )
    by_id = {req["id"]: req for req in json.loads(report_path.read_text())["requirements"]}
    assert _recorded(by_id, "ACP-OPTIONS-201")["acp_tck_options_unsupported_type_outcome"] == "ignored"
    plain = _table_statuses(_run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k="test_initial_config").stdout)
    assert {plain[i] for i in ids} == {"SKIPPED"}, plain
