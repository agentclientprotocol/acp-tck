"""Advertised slash commands and skills (ACP-COMMANDS-201, ACP-COMMANDS-202).

There is no `availableCommands` capability marker -- support is *inferred* from the agent
advertising any command, so `Requirement.capability` is the documentation-only
`"inferred:availableCommands"` string and the test SKIPs itself when no command is observed
(same encoding as `test_session_config.py`, hence the same `v2_only_agent` connection). Skills
(`type: "skill"` entries, unstable) are inferred the same way (`"inferred:skills"`): the agent
shows it uses them by listing one, and only to a client that advertised
`capabilities.session.commands.skill`, so these rows also run on a connection that does.

Only the command items are schema-validated (against `AvailableCommand`), never the message that
carries them: a violation elsewhere in `session/new`'s result is the whole-result rows' to report.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from tck.common.harness import Direction
from tck.common.plugin import capability_is_supported
from tck.v2.validation import validate_def_value

from ._helpers import drain_quiet, iter_messages, new_session_result, quiet_period, v2_only_agent

_SKILL_CLIENT = {"session": {"commands": {"skill": {}}}}


async def _command_lists(
    agent_launch, tmp_path, capabilities: dict[str, Any] | None
) -> tuple[dict[str, Any], list[tuple[str, list[Any]]]]:
    """On a fresh connection advertising `capabilities`, read `session/new`'s `availableCommands`,
    a `session/options` result's (when `session.options` is advertised; advisory and possibly
    partial, but typed and unique all the same) plus whatever `available_commands_update` the
    agent pushes right after setup (a quiet drain). Returns the `initialize` result and the
    non-empty lists as `(label, entries)`."""
    async with v2_only_agent(
        agent_launch, capabilities=capabilities, require_session=True, yield_result=True
    ) as (agent, init_result):
        timeout = agent_launch.default_timeout
        start = len(agent.transcript)
        result = await new_session_result(agent, tmp_path, timeout=timeout)
        session_id = result["sessionId"]
        lists: list[tuple[str, Any]] = [("session/new availableCommands", result.get("availableCommands"))]
        if capability_is_supported(init_result, "capabilities.session.options"):
            req_id = await agent.send_request("session/options", {"cwd": str(tmp_path)})
            entry = await agent.wait_for_response(req_id, timeout=timeout)
            options_result = entry.parsed.get("result") if isinstance(entry.parsed, dict) else None
            if isinstance(options_result, dict):
                lists.append(("session/options availableCommands", options_result.get("availableCommands")))
        await drain_quiet(agent, quiet_period(timeout))

        for entry in agent.transcript[start:]:
            if entry.direction is not Direction.RECEIVED:
                continue
            for message in iter_messages(entry):
                params = message.get("params")
                update = params.get("update") if isinstance(params, dict) else None
                if (
                    message.get("method") == "session/update"
                    and isinstance(params, dict)
                    and params.get("sessionId") == session_id
                    and isinstance(update, dict)
                    and update.get("sessionUpdate") == "available_commands_update"
                ):
                    lists.append(("available_commands_update", update.get("availableCommands")))
    return init_result, [(label, commands) for label, commands in lists if isinstance(commands, list) and commands]


@pytest.mark.requirement("ACP-COMMANDS-201")
async def test_advertised_commands_are_typed_unique_and_whitespace_free(agent_launch, tmp_path):
    """ACP-COMMANDS-201. Judges the lists of two connections: the default one and one that
    advertises `session.commands.skill: {}`, the only one where a `skill` entry may appear and so
    the only one that exercises "unique across commands and skills". A leading `/` in a name is
    not judged: the spec says "without the leading `/`" with no RFC keyword."""
    observed: list[tuple[str, list[Any]]] = []
    for label, capabilities in (("default connection", None), ("commands.skill connection", _SKILL_CLIENT)):
        _, lists = await _command_lists(agent_launch, tmp_path, capabilities)
        observed.extend((f"{label}, {name}", commands) for name, commands in lists)
    if not observed:
        pytest.skip("no availableCommands advertised")

    problems: list[str] = []
    for label, commands in observed:
        seen: set[str] = set()
        for command in commands:
            issues = validate_def_value("AvailableCommand", command)
            if issues:
                problems.append(f"{label}: command {command!r} is not a valid AvailableCommand: {issues!r}")
                continue
            name = command["name"]
            if re.search(r"\s", name):
                problems.append(f"{label}: command name {name!r} contains whitespace")
            if name in seen:
                problems.append(f"{label}: command name {name!r} is not unique within the list")
            seen.add(name)
    assert not problems, "; ".join(problems)


@pytest.mark.requirement("ACP-COMMANDS-202")
async def test_an_agent_listing_skills_advertises_prompt_skill(agent_launch, tmp_path):
    """ACP-COMMANDS-202. On a connection that advertises `session.commands.skill: {}`, an agent
    that lists a `skill` entry carries `capabilities.session.prompt.skill` as an object
    (slash-commands.mdx:173; initialization.mdx:417-418). The row checks the agent's own marker,
    so it cannot be gated on it: `inferred:skills` is documentation-only and the test SKIPs when no
    skill entry is seen."""
    init_result, lists = await _command_lists(agent_launch, tmp_path, _SKILL_CLIENT)
    skills = [
        (label, entry)
        for label, commands in lists
        for entry in commands
        if isinstance(entry, dict) and entry.get("type") == "skill"
    ]
    if not skills:
        pytest.skip("no skill entry listed -- the agent does not use skills")
    session = (init_result.get("capabilities") or {}).get("session")
    prompt = session.get("prompt") if isinstance(session, dict) else None
    advertised = isinstance(prompt, dict) and isinstance(prompt.get("skill"), dict)
    assert advertised, (
        f"the agent listed skill entries ({skills[0][0]}: {skills[0][1]!r}) but advertises no "
        f"capabilities.session.prompt.skill object (prompt: {prompt!r})"
    )
