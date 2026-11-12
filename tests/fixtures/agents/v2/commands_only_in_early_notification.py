#!/usr/bin/env python3
"""Non-conforming fixture: announces a command in an `available_commands_update` before the
`session/new` response and leaves `availableCommands` out of the response, so the client's list
is replaced with nothing (session-setup.mdx:103,108). FAILs `ACP-SESSION-208` and, since it also
notifies early, the ADVISORY `ACP-SESSION-207` -- the premise of 208 is that early notification.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CommandsOnlyInEarlyNotificationAgent(ConformingAgent):
    def _before_new_response(self, session_id: str) -> None:
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {
                    "sessionUpdate": "available_commands_update",
                    "availableCommands": [
                        {"type": "command", "name": "tck", "description": "A TCK command"}
                    ],
                },
            },
        )


def main() -> None:
    CommandsOnlyInEarlyNotificationAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
