#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` of a session the agent never created succeeds and
creates it, instead of `-32002` with `data.sessionId`.

FAILs exactly `ACP-ERROR-004` (its `session/resume` probe). Everything else about resume is the conforming baseline.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeAcceptsUnknownSessionAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        if session_id not in self._sessions and session_id not in self._closed_sessions:
            self._closed_sessions[session_id] = params.get("cwd", "")
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    ResumeAcceptsUnknownSessionAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
