#!/usr/bin/env python3
"""Non-conforming fixture: for a client that advertised `capabilities.session.commands.skill`, lists
a `skill` entry named like a `command` entry, although names must be unique within the list,
across commands and skills (slash-commands.mdx:186-188). Each type alone is valid and the default
connection sees no skill, so only ACP-COMMANDS-201 (on its skill connection) is violated. It
advertises `session.prompt.skill`, so ACP-COMMANDS-202 passes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        capabilities={"session": {"prompt": {"skill": {}}}},
        available_commands=[{"type": "command", "name": "tck", "description": "A TCK command"}],
        skill_commands=[{"type": "skill", "name": "tck", "description": "A TCK skill"}],
        agent_name="tck-fixture-skill-duplicates-command-name",
    ).run()


if __name__ == "__main__":
    main()
