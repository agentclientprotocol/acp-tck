#!/usr/bin/env python3
"""Non-conforming fixture: reports a tool call `in_progress` during the turn and ends the turn
without giving it a final status or listing it as background work. When foreground work ends,
its unfinished tool calls SHOULD get a final status (tool-calls.mdx:423): FAILs exactly
`ACP-PATCH-211`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class LeavesToolCallInProgressAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._tool_call_count += 1
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": f"tool-left-{self._tool_call_count:04d}",
                "title": "Reading a file",
                "status": "in_progress",
            },
        )
        return False


def main() -> None:
    LeavesToolCallInProgressAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
