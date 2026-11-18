#!/usr/bin/env python3
"""Non-conforming fixture: `replays_subagent_history.py`, except a replayed child gets no
`replay_complete` of its own: only the resumed session's replay ends with one. Each session has its
own `replay_complete` (session-setup.mdx:414). FAILs exactly `ACP-RESUME-223` within its `-k`
scope.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from replays_subagent_history import ReplaysSubagentHistoryAgent  # noqa: E402


class ChildMissingReplayCompleteAgent(ReplaysSubagentHistoryAgent):
    def _send_child_replay_complete(self, child_id: str) -> None:
        pass


def main() -> None:
    ChildMissingReplayCompleteAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
