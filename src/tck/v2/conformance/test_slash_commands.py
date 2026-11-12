"""Advertised slash commands (ACP-COMMANDS-201).

There is no `availableCommands` capability marker -- support is *inferred* from the agent
advertising any command, so `Requirement.capability` is the documentation-only
`"inferred:availableCommands"` string and the test SKIPs itself when no command is observed
(same encoding as `test_session_config.py`, hence the same `v2_only_agent` connection).

Only the command items are schema-validated (against `AvailableCommand`), never the message that
carries them: a violation elsewhere in `session/new`'s result is the whole-result rows' to report.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from tck.common.harness import Direction
from tck.v2.validation import validate_def_value

from ._helpers import drain_quiet, iter_messages, new_session_result, quiet_period, v2_only_agent


@pytest.mark.requirement("ACP-COMMANDS-201")
async def test_advertised_commands_are_typed_unique_and_whitespace_free(agent_launch, tmp_path):
    """ACP-COMMANDS-201. Reads `session/new`'s `availableCommands` plus whatever
    `available_commands_update` the agent pushes right after setup (a quiet drain). A leading `/`
    in a name is not judged: the spec says "without the leading `/`" with no RFC keyword."""
    async with v2_only_agent(agent_launch, require_session=True) as agent:
        start = len(agent.transcript)
        result = await new_session_result(agent, tmp_path, timeout=agent_launch.default_timeout)
        session_id = result["sessionId"]
        await drain_quiet(agent, quiet_period(agent_launch.default_timeout))

        lists: list[tuple[str, Any]] = [("session/new availableCommands", result.get("availableCommands"))]
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

        observed = [(label, commands) for label, commands in lists if isinstance(commands, list) and commands]
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
