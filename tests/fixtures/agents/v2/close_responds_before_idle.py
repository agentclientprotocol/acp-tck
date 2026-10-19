#!/usr/bin/env python3
"""Non-conforming fixture: `session/close` on a session with a still-hanging `__hang__` prompt
answers the close first and only then sends the cancelled idle for the work it cancelled.

Only observable with `--cancel-prompt __hang__`. FAILs exactly `ACP-CLOSE-203`: the turn still
ends `cancelled`, so `ACP-CLOSE-202`/`ACP-CANCEL-208` PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CloseRespondsBeforeIdleAgent(ConformingAgent):
    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        was_hanging = self._hanging_sessions.pop(session_id, None) is not None
        if session_id in self._sessions:
            self._closed_sessions[session_id] = self._sessions.pop(session_id)
        self._reply(msg_id, {})
        if was_hanging:
            self._finish_turn(session_id, "cancelled")


def main() -> None:
    CloseRespondsBeforeIdleAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
