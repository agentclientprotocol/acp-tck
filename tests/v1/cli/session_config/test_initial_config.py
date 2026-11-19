"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_initial_config.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_initial_config_defect_fixtures_fail_only_their_own_rows():
    """Each fixture advertises `sessionCapabilities.options` with a select and a boolean option and
    breaks one initial-`configOptions` rule. The `options_fork_*` ones also advertise `fork` and
    break the rule only on `session/fork`. Everything else PASSes or SKIPs. The run is scoped with
    `-k`, so its verdict is not asserted."""
    ids = [f"ACP-OPTIONS-{n:03}" for n in (4, 5, 6, 7, 8, 10, 11)]
    for fixture, expected in (
        ("options_accepts_malformed.py", {"ACP-OPTIONS-004"}),
        ("options_accepts_duplicate.py", {"ACP-OPTIONS-005"}),
        ("options_rejects_unknown_entry.py", {"ACP-OPTIONS-006"}),
        ("options_notifies_initial.py", {"ACP-OPTIONS-007"}),
        ("options_announces_mode.py", {"ACP-OPTIONS-008"}),
        ("options_response_hides_values.py", {"ACP-OPTIONS-011"}),
        ("options_fork_accepts_malformed.py", {"ACP-OPTIONS-004"}),
        ("options_fork_accepts_duplicate.py", {"ACP-OPTIONS-005"}),
        ("options_fork_rejects_unknown_entry.py", {"ACP-OPTIONS-006"}),
        ("options_fork_announces_mode.py", {"ACP-OPTIONS-008"}),
    ):
        result = _run_cli(fixture, k="test_initial_config")
        assert _output_fail_ids(result.stdout) == expected, f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        for req_id in set(ids) - expected:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"


def test_initial_config_rows_leave_out_what_the_entries_did_not_cause():
    """`options_commands_overtake_response.py` sends an `available_commands_update` just after a
    plain `session/new` response and before one with entries: the same request without entries
    sends that kind too, so ACP-OPTIONS-008 PASSes. `options_fork_always_fails.py` advertises
    `fork` but every `session/fork` fails with `-32603`: the rows leave the fork out and PASS on
    `session/new`."""
    for fixture, rows in (
        ("options_commands_overtake_response.py", (8,)),
        ("options_fork_always_fails.py", (4, 5, 6, 8)),
    ):
        result = _run_cli(fixture, k="test_initial_config")
        assert _output_fail_ids(result.stdout) == set(), f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        for n in rows:
            assert statuses[f"ACP-OPTIONS-{n:03}"] == "PASS", f"{fixture}:\n{result.stdout}"


def test_conforming_initial_config_passes_non_vacuously_and_conforming_skips():
    """`conforming_full.py` applies initial entries, ignores inapplicable ones and reports the real
    values, so every ACP-OPTIONS row of the initial-value family PASSes (010 records and PASSes);
    `conforming.py` advertises no `options` and SKIPs them all."""
    ids = [f"ACP-OPTIONS-{n:03}" for n in (4, 5, 6, 7, 8, 10, 11)]
    full = _table_statuses(_run_cli("conforming_full.py", k="test_initial_config").stdout)
    assert {full[i] for i in ids} == {"PASS"}, full
    plain = _table_statuses(_run_cli("conforming.py", k="test_initial_config").stdout)
    assert {plain[i] for i in ids} == {"SKIPPED"}, plain
