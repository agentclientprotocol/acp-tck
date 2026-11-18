#!/usr/bin/env python3
"""Non-conforming fixture: lists a `skill` command entry, in the `session/new` result and in an
`available_commands_update`, although the client never advertised
`capabilities.session.commands.skill` (slash-commands.mdx:171). It advertises
`session.prompt.skill`, so only ACP-CLIENTCAP-203 is violated.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

COMMANDS = [
    {"type": "command", "name": "tck", "description": "A TCK command"},
    {
        "type": "skill",
        "name": "pdf-processing",
        "description": "Extract text and tables from PDF files",
        "path": "/tmp/skills/pdf-processing/SKILL.md",
    },
]


class SkillsUnadvertisedAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_new_session(msg_id, params)
        if self._session_count:
            self._send_update(
                f"sess-{self._session_count:04d}",
                {"sessionUpdate": "available_commands_update", "availableCommands": COMMANDS},
            )


def main() -> None:
    SkillsUnadvertisedAgent(
        capabilities={"session": {"prompt": {"skill": {}}}},
        available_commands=COMMANDS,
        agent_name="tck-fixture-skills-unadvertised",
    ).run()


if __name__ == "__main__":
    main()
