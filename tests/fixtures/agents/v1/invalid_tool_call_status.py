#!/usr/bin/env python3
"""Non-conforming fixture: `exposes_subagent.py`, except that every tool call it sends has an
invalid `status`, the spawn tool call that carries a `session` content item included (and, when no
child is exposed, a plain tool call per turn). The defect is in the tool call, not in the
`session` item, so only the rows that validate a turn's updates FAIL: exactly `ACP-PROMPT-002` and
`ACP-SCHEMA-001` (the basic exchange). `ACP-SUBAGENT-015` validates only the subagent-specific
parts and passes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from exposes_subagent import ExposesSubagentAgent  # noqa: E402


class InvalidToolCallStatusAgent(ExposesSubagentAgent):
    def _handle_prompt(self, msg_id, params):
        session_id = params.get("sessionId")
        if session_id in self._sessions and not self._exposes_subagents(session_id):
            self._emit(
                session_id,
                {
                    "sessionUpdate": "tool_call",
                    "toolCallId": f"{session_id}-tool",
                    "title": "Look around",
                    "kind": "other",
                    "status": "bogus",
                },
            )
        super()._handle_prompt(msg_id, params)

    def _send_session_reference(self, session_id, child_id):
        self._emit(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": f"{child_id}-spawn",
                "title": "Spawn helper",
                "kind": "other",
                "status": "bogus",
                "content": [{"type": "session", "sessionId": child_id}],
            },
        )


def main() -> None:
    InvalidToolCallStatusAgent(agent_name="tck-fixture-invalid-tool-call-status").run()


if __name__ == "__main__":
    main()
