"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_session_options.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_options_defect_fixtures_fail_only_their_own_row():
    """Each fixture advertises `sessionCapabilities.options` (and `list`/`loadSession` where its row
    needs them) and breaks one `session/options` rule. ACP-OPTIONS-001 FAILs only for a method that
    errors; the others SKIP on that prerequisite, never pass vacuously. The run is scoped with
    `-k`, so its verdict is not asserted."""
    ids = [f"ACP-OPTIONS-00{n}" for n in (1, 2, 3, 9)]
    for fixture, expected in (
        ("options_method_errors.py", {"ACP-OPTIONS-001"}),
        ("options_creates_session.py", {"ACP-OPTIONS-002"}),
        ("options_accepts_unknown_session.py", {"ACP-OPTIONS-003"}),
        ("options_connects_mcp.py", {"ACP-OPTIONS-009"}),
        ("boolean_option_on_options.py", {"ACP-CONFIG-003"}),
    ):
        result = _run_cli(fixture, k="test_session_options or test_session_config")
        assert _output_fail_ids(result.stdout) == expected, f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        for req_id in set(ids) - expected:
            assert statuses[req_id] in ("PASS", "SKIPPED"), f"{fixture} {req_id}:\n{result.stdout}"
    errors = _table_statuses(_run_cli("options_method_errors.py", k="test_session_options").stdout)
    assert [errors[f"ACP-OPTIONS-00{n}"] for n in (1, 2, 3, 9)] == ["FAIL", "SKIPPED", "SKIPPED", "SKIPPED"], errors


def test_options_session_id_probe_runs_on_a_fork_only_agent():
    """`options_fork_accepts_malformed.py` advertises `fork` but neither `loadSession` nor `resume`,
    which is enough for the client to send `session/options` a `sessionId`: ACP-OPTIONS-003 probes
    it and PASSes instead of SKIPping."""
    statuses = _table_statuses(_run_cli("options_fork_accepts_malformed.py", k="test_session_options").stdout)
    assert statuses["ACP-OPTIONS-003"] == "PASS", statuses
