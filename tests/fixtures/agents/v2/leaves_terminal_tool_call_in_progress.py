#!/usr/bin/env python3
"""Non-conforming fixture: reports a command's tool call `in_progress` with a `terminal` content
item and ends the turn without giving it a final status, but no `background` list names the
terminal (the agent reports none), so the tool call is not live work. When foreground work ends,
its unfinished tool calls SHOULD get a final status (tool-calls.mdx:423): FAILs exactly
`ACP-PATCH-211`. The negative control for the terminal-reference exemption that
`references_background_terminal.py` exercises.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class LeavesTerminalToolCallInProgressAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._terminal_count += 1
        terminal_id = f"term-left-{self._terminal_count:04d}"
        self._tool_call_count += 1
        self._send_update(
            session_id,
            {"sessionUpdate": "terminal_update", "terminalId": terminal_id, "command": "npm run dev"},
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": f"tool-left-{self._tool_call_count:04d}",
                "title": "Run the dev server",
                "kind": "execute",
                "status": "in_progress",
                "content": [{"type": "terminal", "terminalId": terminal_id}],
            },
        )
        return False


def main() -> None:
    LeavesTerminalToolCallInProgressAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
