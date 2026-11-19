#!/usr/bin/env python3
"""Non-conforming fixture: lists a `skill` command entry to a client that advertised
`capabilities.session.commands.skill`, but advertises no `capabilities.session.prompt.skill`
itself (slash-commands.mdx:173; initialization.mdx:417-418). It sends no skill to any other
client, so only ACP-COMMANDS-202 is violated.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


def main() -> None:
    ConformingAgent(
        capabilities={"session": {}},
        available_commands=[{"type": "command", "name": "tck", "description": "A TCK command"}],
        skill_commands=[
            {
                "type": "skill",
                "name": "pdf-processing",
                "description": "Extract text and tables from PDF files",
                "path": "/tmp/skills/pdf-processing/SKILL.md",
            }
        ],
        agent_name="tck-fixture-skills-without-prompt-skill",
    ).run()


if __name__ == "__main__":
    main()
