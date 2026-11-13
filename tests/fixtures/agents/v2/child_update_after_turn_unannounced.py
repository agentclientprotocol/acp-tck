#!/usr/bin/env python3
"""Non-conforming fixture: nothing child-related happens during the turn, but once the parent's
turn has ended the agent sends an `agent_message_chunk` under a child session ID that no
`subagent_update` ever announced. Outside `ACP-PROMPT-002`'s turn window, so FAILs exactly
`ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildUpdateAfterTurnUnannouncedAgent(ExposesSubagentAgent):
    def _mid_turn_action(self, session_id):
        self._child_count += 1
        self._turn_child = f"{session_id}-child-{self._child_count}"
        return False  # no announcement and no child traffic in the turn


def main() -> None:
    ChildUpdateAfterTurnUnannouncedAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
