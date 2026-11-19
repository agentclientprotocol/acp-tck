#!/usr/bin/env python3
"""Non-conforming fixture: sends `replay_complete` twice on a `session/resume` with
`replayFrom: start`, back to back (session-setup.mdx:379). Violates `ACP-RESUME-218` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeReplayCompleteTwiceAgent(ConformingAgent):
    def _send_replay_complete(self, session_id: Any) -> None:
        super()._send_replay_complete(session_id)
        super()._send_replay_complete(session_id)


def main() -> None:
    ResumeReplayCompleteTwiceAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
