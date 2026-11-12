#!/usr/bin/env python3
"""Non-conforming fixture: sends one more `session/update` for the session after its successful
`session/close` response (session-setup.mdx:395). FAILs exactly `ACP-CLOSE-206`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UpdatesAfterCloseAgent(ConformingAgent):
    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        super()._handle_close_session(msg_id, params)
        self._notify(
            "session/update",
            {
                "sessionId": params.get("sessionId"),
                "update": {"sessionUpdate": "available_commands_update", "availableCommands": []},
            },
        )


def main() -> None:
    UpdatesAfterCloseAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
