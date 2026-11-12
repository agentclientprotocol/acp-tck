#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`'s child per turn (announced live), but
`session/resume` with `replayFrom: start` replays each child's history *before* the parent history
holding that child's `subagent_update`. Announcements made on an earlier turn do not count: a
client resuming on a fresh connection has not seen them. FAILs exactly `ACP-RESUME-209`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReplaysChildBeforeAnnounceAgent(ExposesSubagentAgent):
    def _replay_history(self, session_id: Any) -> None:
        for number in range(1, self._child_count + 1):
            super()._replay_history(f"{session_id}-child-{number}")
        super()._replay_history(session_id)


def main() -> None:
    ReplaysChildBeforeAnnounceAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
