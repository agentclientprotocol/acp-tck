#!/usr/bin/env python3
"""Non-conforming fixture: replays history on `session/resume` with `replayFrom: start` but never
sends `replay_complete` (session-setup.mdx:379-380). Violates `ACP-RESUME-218` only; the rows that
need a `replay_complete` (`ACP-RESUME-220`, `-222`, `ACP-SUGGEST-004`) SKIP.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ResumeOmitsReplayCompleteAgent(ConformingAgent):
    def _send_replay_complete(self, session_id: Any) -> None:
        pass


def main() -> None:
    ResumeOmitsReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
