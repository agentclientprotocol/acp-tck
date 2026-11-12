#!/usr/bin/env python3
"""Non-conforming fixture: `replays_subagent_history.py`, except `session/load` also replays an
`agent_message_chunk` for a child whose announcement it never replays (and never sent in a turn).
That is child traffic naming an unannounced session, in the replay window: FAILs exactly
`ACP-SUBAGENT-001`, so the rows judge replay as well as live traffic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReplaysUnannouncedChildAgent(ExposesSubagentAgent):
    replay_on_load = True

    def _replayed_updates(self, logged):
        orphan = {
            "sessionUpdate": "agent_message_chunk",
            "content": {"type": "text", "text": "replayed output of a child nobody announced"},
        }
        return [*logged, ("orphan-child", orphan)]


def main() -> None:
    ReplaysUnannouncedChildAgent(
        capabilities={"loadSession": True}, agent_name="tck-fixture-replays-unannounced-child"
    ).run()


if __name__ == "__main__":
    main()
