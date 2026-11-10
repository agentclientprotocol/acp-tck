#!/usr/bin/env python3
"""Non-conforming fixture: sends a `tool_call` whose content carries a `{"type": "session"}`
item on every prompt turn although the client never advertised `clientCapabilities.subagents`.
The item names the agent's own session, so only the capability gate is violated. Violates
ACP-CLIENTCAP-007 only.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _emits_update import EmitsUpdateAgent  # noqa: E402


class SessionContentAgent(EmitsUpdateAgent):
    def _build_update(self, session_id: str) -> dict[str, Any]:
        return {
            "sessionUpdate": "tool_call",
            "toolCallId": "tool-1",
            "title": "Delegate",
            "content": [{"type": "session", "sessionId": session_id}],
        }


def main() -> None:
    SessionContentAgent(agent_name="tck-fixture-session-content-without-subagents").run()


if __name__ == "__main__":
    main()
