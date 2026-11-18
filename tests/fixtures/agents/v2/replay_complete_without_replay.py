#!/usr/bin/env python3
"""Non-conforming fixture: sends `replay_complete` for a `session/new` (right before its response)
and for a `session/resume` without a replay cursor, `replayFrom` omitted or `null`
(session-setup.mdx:381). Violates `ACP-RESUME-219` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ReplayCompleteWithoutReplayAgent(ConformingAgent):
    @staticmethod
    def _ends_replay(replay_from: Any) -> bool:
        return True

    def _before_new_response(self, session_id: Any) -> None:
        super()._before_new_response(session_id)
        self._send_replay_complete(session_id)


def main() -> None:
    ReplayCompleteWithoutReplayAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
