"""End-to-end CLI tests for the rows of `src/tck/v1/conformance/test_client_capabilities.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import _output_fail_ids, _run_cli, _table_statuses


def test_calls_fs_unadvertised_fails_clientcap_001():
    """`calls_fs_unadvertised.py` calls `fs/read_text_file` on every prompt turn even though the
    TCK's mock client never advertised `fs` -- a MANDATORY (Req 29) FAIL that must flip the
    exit code. Scoped to `clientcap` since this fixture's `_handle_prompt` override only ever
    resolves a turn once the client has answered its one client-request, which is exactly what
    the clientcap tests' `run_prompt` calls do; other prompt tests would work too, but scoping
    keeps this self-test fast and focused.

    Also asserts ACP-CLIENTCAP-002/003 still PASS: the three ids are three separate tests
    specifically so that a single-capability violation like this one isn't mis-attributed to
    the other two."""
    result = _run_cli("calls_fs_unadvertised.py", k="clientcap")
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLIENTCAP-001") == "FAIL", result.stdout
    assert statuses.get("ACP-CLIENTCAP-002") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-003") == "PASS", result.stdout


def test_calls_terminal_unadvertised_fails_clientcap_002():
    """Same as above, for `terminal/create` (Req 30); asserts -001/-003 still PASS."""
    result = _run_cli("calls_terminal_unadvertised.py", k="clientcap")
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLIENTCAP-001") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-002") == "FAIL", result.stdout
    assert statuses.get("ACP-CLIENTCAP-003") == "PASS", result.stdout


def test_calls_elicitation_unadvertised_fails_clientcap_003():
    """Same as above, for `elicitation/create` (Req 32); asserts -001/-002 still PASS."""
    result = _run_cli("calls_elicitation_unadvertised.py", k="clientcap")
    assert result.returncode != 0, result.stdout + result.stderr

    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-CLIENTCAP-001") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-002") == "PASS", result.stdout
    assert statuses.get("ACP-CLIENTCAP-003") == "FAIL", result.stdout


def test_client_gated_update_fixtures_fail_only_their_own_clientcap_id():
    """One fixture per client-gated `session/update` kind; the compaction one only sends it
    during `session/load` replay, proving replay is covered."""
    for fixture, expected in (
        ("emits_notice_unadvertised.py", "ACP-CLIENTCAP-004"),
        ("replays_compaction_unadvertised.py", "ACP-CLIENTCAP-005"),
        ("emits_plan_update_unadvertised.py", "ACP-CLIENTCAP-006"),
        ("emits_subagent_update_unadvertised.py", "ACP-CLIENTCAP-007"),
        ("session_content_without_subagents.py", "ACP-CLIENTCAP-007"),
        ("emits_prompt_suggestions_unadvertised.py", "ACP-CLIENTCAP-008"),
        ("emits_cursor_unadvertised.py", "ACP-CLIENTCAP-009"),
    ):
        result = _run_cli(fixture)
        assert result.returncode != 0, f"{fixture}:\n{result.stdout}"
        assert _output_fail_ids(result.stdout) == {expected}, f"{fixture}:\n{result.stdout}"


def test_subagent_traffic_is_only_sent_to_a_client_that_advertised_subagents():
    """The default connections advertise no `subagents`: a fixture that sends child traffic only
    to a client that asked for it leaves `ACP-CLIENTCAP-007` and `ACP-PROMPT-002` PASSing, while
    `emits_subagent_update_unadvertised.py` (which sends it regardless) FAILs the former."""
    for fixture, expected in (("exposes_subagent.py", "PASS"), ("emits_subagent_update_unadvertised.py", "FAIL")):
        result = _run_cli(fixture, k="test_client_capabilities or test_prompt")
        assert _table_statuses(result.stdout)["ACP-CLIENTCAP-007"] == expected, result.stdout
        assert _table_statuses(result.stdout)["ACP-PROMPT-002"] == "PASS", result.stdout
