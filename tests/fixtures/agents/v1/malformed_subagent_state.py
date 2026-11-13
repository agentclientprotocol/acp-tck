#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except the child's work state snapshot on the
parent's `subagent_update` has no `state` discriminator (`{"stopReason": "end_turn"}`), which the
v1 `StateUpdate` schema rejects. The child is announced and nothing else is wrong: FAILs exactly
`ACP-SUBAGENT-015`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class MalformedSubagentStateAgent(ExposesSubagentAgent):
    def _send_child_state(self, session_id, child_id, state):
        if state.get("state") == "idle":
            state = {"stopReason": state["stopReason"]}
        super()._send_child_state(session_id, child_id, state)


def main() -> None:
    MalformedSubagentStateAgent(agent_name="tck-fixture-malformed-subagent-state").run()


if __name__ == "__main__":
    main()
