#!/usr/bin/env python3
"""Non-conforming fixture: `replays_subagent_history.py`, except that `session/load` replays the
child's history (its updates and `session_message` views) without re-sending the `subagent_update`
announcements. The turn did announce the child, but a client loading the session on a fresh
connection has not seen that: within the load only an announcement made in the load counts, so
the replayed child traffic names an unannounced session. FAILs exactly `ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReplaysChildWithoutAnnouncementAgent(ExposesSubagentAgent):
    replay_on_load = True

    def _replayed_updates(self, logged):
        return [(target, update) for target, update in logged if update["sessionUpdate"] != "subagent_update"]


def main() -> None:
    ReplaysChildWithoutAnnouncementAgent(
        capabilities={"loadSession": True}, agent_name="tck-fixture-replays-child-without-announcement"
    ).run()


if __name__ == "__main__":
    main()
