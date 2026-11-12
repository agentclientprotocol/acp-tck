#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child and its nested child are announced
first), plus a live `session_message` from the parent to the child that is sent on the nested
child, a session that is neither participant. Every session named is announced and the update is
schema-valid, so `ACP-SUBAGENT-001` passes, and the participants differ, so `ACP-SUBAGENT-007`
passes: FAILs exactly `ACP-SUBAGENT-008`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionMessageForeignOuterSessionAgent(ExposesSubagentAgent):
    def _send_session_messages(self, session_id, child_id):
        super()._send_session_messages(session_id, child_id)
        self._emit(
            f"{child_id}-nested",  # announced by `_announce_nested_child`
            {
                "sessionUpdate": "session_message",
                "messageId": f"{child_id}-foreign",
                "senderSessionId": session_id,
                "recipientSessionId": child_id,
                "content": [{"type": "text", "text": "wrong transcript"}],
            },
        )


def main() -> None:
    SessionMessageForeignOuterSessionAgent(agent_name="tck-fixture-session-message-foreign-outer-session").run()


if __name__ == "__main__":
    main()
