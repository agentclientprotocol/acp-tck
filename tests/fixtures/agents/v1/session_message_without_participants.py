#!/usr/bin/env python3
"""Fixture: `exposes_subagent.py`, except its only `session_message`s name no participant and no
view (both fields are optional). Nothing is there to judge, so `ACP-SUBAGENT-007..009` SKIP rather
than PASS. The child is never told its task as an incoming message from its parent, so
`ACP-SUBAGENT-012` (ADVISORY) FAILs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionMessageWithoutParticipantsAgent(ExposesSubagentAgent):
    def _send_session_messages(self, session_id, child_id):
        self._emit(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-anonymous",
                "content": [{"type": "text", "text": "please help"}],
            },
        )


def main() -> None:
    SessionMessageWithoutParticipantsAgent(agent_name="tck-fixture-session-message-without-participants").run()


if __name__ == "__main__":
    main()
