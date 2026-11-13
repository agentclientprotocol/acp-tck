#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), plus a live
`session_message` on the parent whose `recipientSessionId` names a session that no
`subagent_update` ever announced. The update itself is on the prompted session and schema-valid,
so `ACP-PROMPT-002` passes: FAILs exactly `ACP-SUBAGENT-001`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionMessageUnknownParticipantAgent(ExposesSubagentAgent):
    def _send_session_messages(self, session_id, child_id):
        super()._send_session_messages(session_id, child_id)
        self._send_update(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-ghost",
                "recipientSessionId": f"{child_id}-never-announced",
                "content": [{"type": "text", "text": "psst"}],
            },
        )


def main() -> None:
    SessionMessageUnknownParticipantAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
