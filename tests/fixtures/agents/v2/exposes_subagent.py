#!/usr/bin/env python3
"""Conforming fixture: during each turn it announces a child session with `subagent_update` on
the prompted session, then streams the child's own `running` -> `agent_message_chunk` ->
`idle(end_turn)` under the child's `sessionId`, then finishes the parent turn normally. Child
traffic is legal once announced, and the child's idle must not end the parent's turn: must PASS
`ACP-PROMPT-203/205` and `ACP-STATE-201..205` like `conforming.py`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ExposesSubagentAgent(ConformingAgent):
    announce_child = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._child_count = 0

    def _mid_turn_action(self, session_id: Any) -> bool:
        self._child_count += 1
        child_id = f"{session_id}-child-{self._child_count}"
        if self.announce_child:
            self._send_update(
                session_id,
                {"sessionUpdate": "subagent_update", "sessionId": child_id, "title": "helper"},
            )
        self._send_update(child_id, {"sessionUpdate": "state_update", "state": "running"})
        self._send_update(
            child_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": f"{child_id}-msg",
                "content": {"type": "text", "text": "child output"},
            },
        )
        self._send_update(
            child_id, {"sessionUpdate": "state_update", "state": "idle", "stopReason": "end_turn"}
        )
        return False


def main() -> None:
    ExposesSubagentAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
