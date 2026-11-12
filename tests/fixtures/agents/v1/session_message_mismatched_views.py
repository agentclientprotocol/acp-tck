#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py` (the child is announced first), plus a second
message from the parent to the child in both views whose references disagree: the outgoing view's
`recipientMessageId` names the incoming view, but the incoming view's `senderMessageId` names
some other message. Each view is on a participant's own transcript with known, different
participants and is schema-valid, so `ACP-SUBAGENT-001`, `-007` and `-008` pass: FAILs exactly
`ACP-SUBAGENT-009`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class SessionMessageMismatchedViewsAgent(ExposesSubagentAgent):
    def _send_session_messages(self, session_id, child_id):
        super()._send_session_messages(session_id, child_id)
        self._send_session_message_pair(
            session_id,
            child_id,
            f"{child_id}-follow-up-out",
            f"{child_id}-follow-up-in",
            incoming_sender_message_id=f"{child_id}-some-other-message",
        )


def main() -> None:
    SessionMessageMismatchedViewsAgent(agent_name="tck-fixture-session-message-mismatched-views").run()


if __name__ == "__main__":
    main()
