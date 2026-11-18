#!/usr/bin/env python3
"""Non-conforming fixture: sends a `skill` content block in an `agent_message_chunk` before each
turn's idle, although a skill reference appears only in user messages (content.mdx:252). FAILs
`ACP-PROMPT-220` only (an ADVISORY row).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SendsSkillInAgentMessageAgent(ConformingAgent):
    def _send_idle_update(self, session_id: Any, stop_reason: str | None) -> None:
        self._send_update(
            session_id,
            {
                "sessionUpdate": "agent_message_chunk",
                "messageId": "msg-tck-skill",
                "content": {"type": "skill", "name": "pdf-processing"},
            },
        )
        super()._send_idle_update(session_id, stop_reason)


def main() -> None:
    SendsSkillInAgentMessageAgent(
        capabilities={"session": {}}, agent_name="tck-fixture-sends-skill-in-agent-message"
    ).run()


if __name__ == "__main__":
    main()
