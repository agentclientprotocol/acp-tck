#!/usr/bin/env python3
"""Non-conforming fixture: sends a live `notice` before `replay_complete` on a `session/resume`
with `replayFrom: start`, instead of holding it until after (session-setup.mdx:384). Violates
`ACP-RESUME-220` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeNoticeBeforeReplayCompleteAgent(ConformingAgent):
    def _send_replay_complete(self, session_id: Any) -> None:
        self._notify(
            "session/update",
            {
                "sessionId": session_id,
                "update": {"sessionUpdate": "notice", "severity": "info", "title": "Session resumed"},
            },
        )
        super()._send_replay_complete(session_id)


def main() -> None:
    ResumeNoticeBeforeReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
