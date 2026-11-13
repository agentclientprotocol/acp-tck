#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), except the parent
streams a follow-up message to the child by sending a `session_message_chunk` first and the
`session_message` upsert naming its participants only afterwards. Both are schema-valid and name
announced sessions, so FAILs exactly `ACP-SUBAGENT-013` (an ADVISORY row: the verdict is
unchanged).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionMessageChunkBeforeParticipantsAgent(ExposesSubagentAgent):
    def _send_streamed_follow_up(self, session_id, child_id):
        message_id = f"{child_id}-follow-up-stream"
        self._send_session_message_chunk(session_id, message_id)
        self._send_update(
            session_id,
            {
                "sessionUpdate": "session_message",
                "messageId": message_id,
                "senderSessionId": session_id,
                "recipientSessionId": child_id,
            },
        )


def main() -> None:
    SessionMessageChunkBeforeParticipantsAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
