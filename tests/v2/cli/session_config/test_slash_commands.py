"""End-to-end CLI tests for the rows of `src/tck/v2/conformance/test_slash_commands.py`: each runs
fixture agents through `acp-tck` and checks the summary table."""

from __future__ import annotations

from .._runner import FIXTURES_DIR_V2, _fails_for, _run_cli, _table_statuses


_COMMANDS_K = "slash_commands"


def test_commands_name_with_whitespace_fails_commands_201_only():
    fails, _statuses, out = _fails_for("commands_name_with_whitespace.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert "whitespace" in out, out


def test_commands_duplicate_names_fails_commands_201_only():
    fails, _statuses, out = _fails_for("commands_duplicate_names.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert "not unique" in out, out


def test_commands_untyped_in_update_fails_commands_201():
    fails, _statuses, out = _fails_for("commands_untyped_in_update.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert "AvailableCommand" in out, out


def test_conforming_full_passes_commands_201_and_202():
    """`conforming_full.py` lists one skill, but only to a client advertising `session.commands.skill`
    (and advertises `session.prompt.skill`), so COMMANDS-201 and -202 both PASS non-vacuously."""
    result = _run_cli(
        FIXTURES_DIR_V2, "conforming_full.py", protocol_version=2, k=_COMMANDS_K
    )
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-COMMANDS-201") == "PASS", result.stdout
    assert statuses.get("ACP-COMMANDS-202") == "PASS", result.stdout


def test_commands_202_skips_for_an_agent_that_lists_no_skill():
    """`conforming.py` lists no commands at all, so -201 and -202 both SKIP."""
    result = _run_cli(FIXTURES_DIR_V2, "conforming.py", protocol_version=2, k=_COMMANDS_K)
    statuses = _table_statuses(result.stdout)
    assert statuses.get("ACP-COMMANDS-201") == "SKIPPED", result.stdout
    assert statuses.get("ACP-COMMANDS-202") == "SKIPPED", result.stdout


def test_skills_without_prompt_skill_fails_commands_202_only():
    """`skills_without_prompt_skill.py` lists a skill to a client that advertised `commands.skill`
    and advertises no `session.prompt.skill`; it lists none to any other client, so
    ACP-CLIENTCAP-203 is not in scope here and COMMANDS-201 PASSes."""
    fails, statuses, out = _fails_for("skills_without_prompt_skill.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-202"}, out
    assert statuses.get("ACP-COMMANDS-201") == "PASS", out
    assert "prompt.skill" in out, out


def test_skill_duplicating_a_command_name_fails_commands_201_only():
    """Only the `commands.skill` connection sees the skill, whose name repeats a command's."""
    fails, statuses, out = _fails_for("skill_duplicates_command_name.py", _COMMANDS_K)
    assert fails == {"ACP-COMMANDS-201"}, out
    assert statuses.get("ACP-COMMANDS-202") == "PASS", out
    assert "not unique" in out, out
