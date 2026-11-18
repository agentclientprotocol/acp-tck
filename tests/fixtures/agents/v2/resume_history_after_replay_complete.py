#!/usr/bin/env python3
"""Non-conforming fixture: sends `replay_complete` first on a `session/resume` with
`replayFrom: start` and replays the history after it, still before the response
(session-setup.mdx:379: after the last replayed update). Violates `ACP-RESUME-218` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeHistoryAfterReplayCompleteAgent(ConformingAgent):
    def _replay_history(self, session_id: Any) -> None:
        super()._send_replay_complete(session_id)
        super()._replay_history(session_id)

    def _send_replay_complete(self, session_id: Any) -> None:
        pass


def main() -> None:
    ResumeHistoryAfterReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
