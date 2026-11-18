#!/usr/bin/env python3
"""Conforming fixture: `exposes_subagent.py`, except that the child's task arrives as an incoming
`session_message` that names no sender: the Agent has no evidence of who sent it, so it omits
`senderSessionId` and does not assume the parent (`subagents.mdx:265`). That still reports the task,
so `ACP-SUBAGENT-012` (ADVISORY) PASSes and nothing FAILs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildTaskWithoutSenderAgent(ExposesSubagentAgent):
    def _send_delegated_task(self, session_id: Any, child_id: str) -> None:
        self._send_update(
            child_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-task-in",
                "recipientSessionId": child_id,
                "content": [{"type": "text", "text": "please help"}],
            },
        )


def main() -> None:
    ChildTaskWithoutSenderAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
