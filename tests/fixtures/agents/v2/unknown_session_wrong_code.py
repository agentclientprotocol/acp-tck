#!/usr/bin/env python3
"""Non-conforming fixture: answers `session/prompt` for a session that is not active (never
created, or closed) with `-32602` instead of `-32002` with `data.sessionId`.

FAILs exactly `ACP-ERROR-003`. `ACP-ERROR-004` is unaffected (resume still answers `-32002`).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnknownSessionWrongCodeAgent(ConformingAgent):
    def _unknown_session(self, msg_id: Any, session_id: Any) -> None:
        self._error(msg_id, -32602, f"Invalid params: unknown sessionId {session_id!r}")

    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            ConformingAgent._unknown_session(self, msg_id, session_id)
            return
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    UnknownSessionWrongCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
