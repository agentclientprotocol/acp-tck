"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_session_options.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails, _run_cli, _table_statuses


def test_options_defect_fixtures_fail_only_their_own_row():
    """Each fixture advertises `session.options` (and `mcp.stdio` where its row needs it) and breaks one
    `session/options` rule. ACP-OPTIONS-001 FAILs only for a method that errors; the others SKIP on that
    prerequisite, never pass vacuously. The run is scoped with `-k`, so its verdict is not asserted."""
    ids = [f"ACP-OPTIONS-00{n}" for n in (1, 2, 3, 9)]
    scope = "test_session_options or test_session_config or test_slash_commands or test_client_capabilities"
    for fixture, expected in (
        ("options_method_errors.py", {"ACP-OPTIONS-001"}),
        ("options_creates_session.py", {"ACP-OPTIONS-002"}),
        ("options_resumes_session.py", {"ACP-OPTIONS-002"}),
        ("options_accepts_unknown_session.py", {"ACP-OPTIONS-003"}),
        ("options_connects_mcp.py", {"ACP-OPTIONS-009"}),
        ("options_undeclared_current_value.py", {"ACP-CONFIG-001"}),
        ("options_duplicate_select_values.py", {"ACP-CONFIG-210"}),
        ("options_duplicate_commands.py", {"ACP-COMMANDS-201"}),
        ("options_sends_skill.py", {"ACP-CLIENTCAP-203"}),
    ):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k=scope)
        statuses = _table_statuses(result.stdout)
        fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
        assert fails == expected, f"{fixture}:\n{result.stdout}"
        for req_id in set(ids) - expected:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"
    errors = _table_statuses(
        _run_cli(FIXTURES_DIR_V2, "options_method_errors.py", protocol_version=2, k="test_session_options").stdout
    )
    assert [errors[f"ACP-OPTIONS-00{n}"] for n in (1, 2, 3, 9)] == ["FAIL", "SKIPPED", "SKIPPED", "SKIPPED"], errors


def test_late_setup_traffic_is_not_blamed_on_session_options():
    """`options_late_setup_traffic.py` sends `available_commands_update` from a timer shortly after
    `session/new` and lists its closed session only from the second `session/list` on. ACP-OPTIONS-002
    waits out the setup traffic and does not count the TCK's own session, so it PASSes."""
    result = _run_cli(FIXTURES_DIR_V2, "options_late_setup_traffic.py", protocol_version=2, k="test_session_options")
    statuses = _table_statuses(result.stdout)
    assert _fails(statuses) == set(), result.stdout
    assert statuses["ACP-OPTIONS-002"] == "PASS", result.stdout
