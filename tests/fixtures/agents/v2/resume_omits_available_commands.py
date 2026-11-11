#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` carries `availableCommands` but `session/resume` of
that session leaves them out, so the client would drop the list it holds
(session-setup.mdx:108,333-335).

FAILs exactly `ACP-RESUME-210`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeOmitsAvailableCommandsAgent(ConformingAgent):
    def _resume_result(self) -> dict[str, Any]:
        return {}


def main() -> None:
    ResumeOmitsAvailableCommandsAgent(
        capabilities={"session": {}},
        available_commands=[{"type": "command", "name": "tck", "description": "A TCK command"}],
    ).run()


if __name__ == "__main__":
    main()
