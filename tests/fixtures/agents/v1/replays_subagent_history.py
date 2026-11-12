#!/usr/bin/env python3
"""Conforming fixture: `exposes_subagent.py`'s child per turn, and `session/load` replays that
child's updates before its response, announcements first and in their original order (never the
recorded requests), after the usual history. It advertises `loadSession`, so the subagent
connection includes the replay. Must PASS everything `exposes_subagent.py` does, which is every
`ACP-SUBAGENT-*` row, and the `ACP-LOAD-*` rows on the default connection (no `subagents`, so no
child traffic there).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ReplaysSubagentHistoryAgent(ExposesSubagentAgent):
    replay_on_load = True


def main() -> None:
    ReplaysSubagentHistoryAgent(
        capabilities={"loadSession": True}, agent_name="tck-fixture-replays-subagent-history"
    ).run()


if __name__ == "__main__":
    main()
