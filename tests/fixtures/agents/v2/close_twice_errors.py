#!/usr/bin/env python3
"""Non-conforming fixture: `session/close` of a session that is not active -- already closed, or
never created -- answers `-32002` instead of the empty result (session-setup.mdx:407-410).
FAILs exactly `ACP-CLOSE-207` (ADVISORY): clients tolerate `-32002`, but the agent SHOULD succeed.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class CloseTwiceErrorsAgent(ConformingAgent):
    def _handle_close_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions:
            self._unknown_session(msg_id, session_id)
            return
        super()._handle_close_session(msg_id, params)


def main() -> None:
    CloseTwiceErrorsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
