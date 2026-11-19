"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_client_capabilities.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails_for, _run_cli, _table_statuses


def test_calls_elicitation_unadvertised_fails_clientcap_003_only():
    result = _run_cli(
        FIXTURES_DIR_V2, "calls_elicitation_unadvertised.py", protocol_version=2, k="client_capabilities"
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLIENTCAP-003"}, result.stdout
    assert statuses.get("ACP-CLIENTCAP-202") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_sends_undefined_client_notification_fails_clientcap_202_only():
    """`run_prompt`'s driver records agent -> client *requests and notifications* alike on
    `PromptTurn.client_requests_seen`, so a notification using an undefined method name cannot
    silently escape `ACP-CLIENTCAP-202`'s check -- its own text claims "request/notification"
    coverage. `sends_undefined_client_notification.py` fires
    exactly that -- a notification, no `id`, method name `made_up/notify` -- and nothing else."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "sends_undefined_client_notification.py",
        protocol_version=2,
        k="client_capabilities",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLIENTCAP-202"}, result.stdout
    assert statuses.get("ACP-CLIENTCAP-003") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_gated_content_unadvertised_fixtures_fail_only_their_own_clientcap_id():
    """`suggests_unadvertised.py` sends a prompt suggestion and `skills_unadvertised.py` lists a
    skill entry to clients that advertised neither `session.promptSuggestions` nor
    `session.commands.skill`; each FAILs exactly its own gate row, the other gate and the
    elicitation/method rows PASS."""
    for fixture, expected, other in (
        ("suggests_unadvertised.py", "ACP-CLIENTCAP-008", "ACP-CLIENTCAP-203"),
        ("skills_unadvertised.py", "ACP-CLIENTCAP-203", "ACP-CLIENTCAP-008"),
    ):
        result = _run_cli(FIXTURES_DIR_V2, fixture, protocol_version=2, k="client_capabilities")
        assert result.returncode != 0, f"{fixture}:\n{result.stdout}"
        statuses = _table_statuses(result.stdout)
        fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
        assert fails == {expected}, f"{fixture}:\n{result.stdout}"
        for req_id in (other, "ACP-CLIENTCAP-003", "ACP-CLIENTCAP-202"):
            assert statuses.get(req_id) == "PASS", f"{fixture} {req_id}:\n{result.stdout}"


def test_calls_fs_unadvertised_fails_clientcap_202_only():
    """`fs/read_text_file` is not a known v2 agent->client method at all (`fs/*`/`terminal/*`
    were removed from v2), so it also cascades into `ACP-SCHEMA-001`'s general "every agent
    message validates against the schema" check -- the same documented
    defect-cascades-into-schema-validation pattern as `ACP-INIT-204` (see
    `tck.v2.requirements`'s module docstring), not a separate bug."""
    result = _run_cli(
        FIXTURES_DIR_V2,
        "calls_fs_unadvertised.py",
        protocol_version=2,
        k="client_capabilities or initialize",
    )
    assert result.returncode != 0

    statuses = _table_statuses(result.stdout)
    fails = {req_id for req_id, status in statuses.items() if status == "FAIL"}
    assert fails == {"ACP-CLIENTCAP-202", "ACP-SCHEMA-001"}, result.stdout
    assert statuses.get("ACP-CLIENTCAP-003") == "PASS", result.stdout
    assert "VERDICT: NOT CONFORMANT" in result.stdout, result.stdout


def test_skill_fixtures_leave_the_client_capability_gate_clean():
    """The two fixtures above list a skill only to a client advertising `commands.skill`, so
    ACP-CLIENTCAP-203 PASSes for both."""
    for fixture in ("skills_without_prompt_skill.py", "skill_duplicates_command_name.py"):
        fails, statuses, out = _fails_for(fixture, "client_capabilities")
        assert not fails, f"{fixture}:\n{out}"
        assert statuses.get("ACP-CLIENTCAP-203") == "PASS", f"{fixture}:\n{out}"
