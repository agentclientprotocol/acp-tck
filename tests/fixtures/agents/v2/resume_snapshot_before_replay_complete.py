#!/usr/bin/env python3
"""Non-conforming fixture: sends the current-state `state_update` snapshot before `replay_complete`
on a `session/resume` with `replayFrom: start`, so a non-history update sits in the replay window
(session-setup.mdx:384). The snapshot after it is repeated. Violates `ACP-RESUME-220` only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeSnapshotBeforeReplayCompleteAgent(ConformingAgent):
    def _send_replay_complete(self, session_id: Any) -> None:
        self._send_resume_snapshot(session_id)
        super()._send_replay_complete(session_id)


def main() -> None:
    ResumeSnapshotBeforeReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
