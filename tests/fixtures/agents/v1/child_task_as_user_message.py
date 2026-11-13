#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), except the
delegated task reaches the child as a `user_message_chunk` in its own transcript, before its
output, instead of an incoming `session_message` (the parent still reports the outgoing view).
FAILs exactly `ACP-SUBAGENT-011` (an ADVISORY row: the verdict is unchanged); `ACP-SUBAGENT-012`
leaves a task reported as a user message to `-011`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class ChildTaskAsUserMessageAgent(ExposesSubagentAgent):
    def _send_delegated_task(self, session_id, child_id):
        self._emit(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-task-out",
                "senderSessionId": session_id,
                "recipientSessionId": child_id,
                "content": [{"type": "text", "text": "please help"}],
            },
        )
        self._emit(
            child_id,
            {
                "sessionUpdate": "user_message_chunk",
                "content": {"type": "text", "text": "please help"},
            },
        )


def main() -> None:
    ChildTaskAsUserMessageAgent(agent_name="tck-fixture-child-task-as-user-message").run()


if __name__ == "__main__":
    main()
