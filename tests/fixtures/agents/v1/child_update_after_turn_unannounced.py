#!/usr/bin/env python3
"""Non-conforming fixture: nothing child-related happens during the turn, but once the prompt
response is sent the agent sends an `agent_message_chunk` under a child session ID that no
`subagent_update` ever announced. FAILs exactly `ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildUpdateAfterTurnUnannouncedAgent(ExposesSubagentAgent):
    def _spawn_child(self, session_id, child_id):
        pass  # no announcement and no child traffic in the turn


def main() -> None:
    ChildUpdateAfterTurnUnannouncedAgent(agent_name="tck-fixture-child-update-after-turn-unannounced").run()


if __name__ == "__main__":
    main()
