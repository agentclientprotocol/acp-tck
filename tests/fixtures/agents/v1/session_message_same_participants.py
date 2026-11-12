#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), plus a live
`session_message` on the parent that names the parent as both sender and recipient. The update is
schema-valid on a known session with known participants, so `ACP-SUBAGENT-001` passes, and the
outer session is one of the participants, so `ACP-SUBAGENT-008` passes: FAILs exactly
`ACP-SUBAGENT-007`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionMessageSameParticipantsAgent(ExposesSubagentAgent):
    def _send_session_messages(self, session_id, child_id):
        super()._send_session_messages(session_id, child_id)
        self._emit(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-self",
                "senderSessionId": session_id,
                "recipientSessionId": session_id,
                "content": [{"type": "text", "text": "note to self"}],
            },
        )


def main() -> None:
    SessionMessageSameParticipantsAgent(agent_name="tck-fixture-session-message-same-participants").run()


if __name__ == "__main__":
    main()
