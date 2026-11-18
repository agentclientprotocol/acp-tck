#!/usr/bin/env python3
"""Non-conforming fixture: `replays_subagent_history.py`, except a resume does not re-announce its
children before their live chunks. With a replay the replayed `subagent_update` still announces
each child, but without one the live chunk carries a child announced only before the resume: the
announcement rule applies again on every resume (subagents.mdx:469). FAILs exactly
`ACP-RESUME-225` within its `-k` scope.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from replays_subagent_history import ReplaysSubagentHistoryAgent  # noqa: E402


class ResumeChildTrafficUnannouncedAgent(ReplaysSubagentHistoryAgent):
    def _reannounce_child(self, session_id: Any, child_id: str) -> None:
        pass


def main() -> None:
    ResumeChildTrafficUnannouncedAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
