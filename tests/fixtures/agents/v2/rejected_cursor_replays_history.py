#!/usr/bin/env python3
"""Non-conforming fixture: rejects an unsupported or malformed `replayFrom` with `-32602` but replays
the session's history first, without `replay_complete` (session-setup.mdx:406: a rejected cursor
replays nothing). Violates `ACP-RESUME-221` only; `ACP-RESUME-207`/`208` still PASS.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RejectedCursorReplaysHistoryAgent(ConformingAgent):
    def _handle_resume_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        session_id = params.get("sessionId")
        known = session_id in self._sessions or session_id in self._closed_sessions
        if known and self._replay_from_rejection(params.get("replayFrom")) is not None:
            self._replay_history(session_id)
        super()._handle_resume_session(msg_id, params)


def main() -> None:
    RejectedCursorReplaysHistoryAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
