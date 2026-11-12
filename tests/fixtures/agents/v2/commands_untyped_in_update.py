#!/usr/bin/env python3
"""Non-conforming fixture: right after the `session/new` response, an
`available_commands_update` carries a command without the required `type` discriminator
(slash-commands.mdx:110; `AvailableCommand` requires `type`). The setup response itself is
conforming. FAILs `ACP-COMMANDS-201`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402

class CommandsUntypedInUpdateAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_new_session(msg_id, params)
        if self._session_count:
            self._send_update(
                f"sess-{self._session_count:04d}",
                {
                    "sessionUpdate": "available_commands_update",
                    "availableCommands": [{"name": "tck", "description": "No type"}],
                },
            )


def main() -> None:
    CommandsUntypedInUpdateAgent(
        capabilities={"session": {}},
        available_commands=[{"type": "command", "name": "tck", "description": "A TCK command"}],
    ).run()

if __name__ == "__main__":
    main()
