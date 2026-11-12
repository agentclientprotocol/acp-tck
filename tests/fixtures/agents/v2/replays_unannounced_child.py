#!/usr/bin/env python3
"""Non-conforming fixture: `session/resume` with `replayFrom: start` replays the session's history
and then history for a child session that was never announced by a `subagent_update`. FAILs
exactly `ACP-RESUME-209`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ReplaysUnannouncedChildAgent(ConformingAgent):
    def _replay_history(self, session_id: Any) -> None:
        super()._replay_history(session_id)
        self._notify(
            "session/update",
            {
                "sessionId": f"{session_id}-orphan-child",
                "update": {
                    "sessionUpdate": "agent_message",
                    "messageId": f"{session_id}-orphan-msg",
                    "content": [{"type": "text", "text": "replayed child output"}],
                },
            },
        )


def main() -> None:
    ReplaysUnannouncedChildAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
