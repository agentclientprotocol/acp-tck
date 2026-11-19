#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` with `loadSession`, whose `session/load` replays no
child history, and whose child sends one more `agent_message_chunk` right after the load response.
The turn announced the child, but the rule applies again on every load (a client loading on a fresh
connection has not seen that announcement) and nothing was announced during this load. FAILs
exactly `ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildTrafficAfterLoadUnannouncedAgent(ExposesSubagentAgent):
    traffic_after_load = True


def main() -> None:
    ChildTrafficAfterLoadUnannouncedAgent(
        capabilities={"loadSession": True}, agent_name="tck-fixture-child-traffic-after-load-unannounced"
    ).run()


if __name__ == "__main__":
    main()
