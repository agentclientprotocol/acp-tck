#!/usr/bin/env python3
"""Non-conforming fixture: sends a `session/request_permission` request for the session before
`replay_complete` on a `session/resume` with `replayFrom: start`, instead of after it
(session-setup.mdx:388). The request is not answered by the TCK and nothing waits for it.
Violates `ACP-RESUME-222` (ADVISORY) only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RequestsBeforeReplayCompleteAgent(ConformingAgent):
    def _send_replay_complete(self, session_id: Any) -> None:
        self._write(
            {
                "jsonrpc": "2.0",
                "id": "perm-resume-1",
                "method": "session/request_permission",
                "params": {
                    "sessionId": session_id,
                    "title": "Allow this action?",
                    "options": [{"optionId": "allow", "name": "Allow", "kind": "allow_once"}],
                },
            }
        )
        super()._send_replay_complete(session_id)


def main() -> None:
    RequestsBeforeReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
