#!/usr/bin/env python3
"""Non-conforming fixture: reports a tool call `completed`, then reopens it as `in_progress`
and completes it again. `completed` is final, and work that goes on after it belongs on a new
tool call (tool-calls.mdx:423; prompt-lifecycle.mdx:184): FAILs exactly `ACP-PATCH-210`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ToolCallReopensAfterFinalAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._tool_call_count += 1
        tool_call_id = f"tool-reopen-{self._tool_call_count:04d}"
        for fields in (
            {"title": "Reading a file", "status": "in_progress"},
            {"status": "completed"},
            {"status": "in_progress"},
            {"status": "completed"},
        ):
            self._send_update(
                session_id, {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id, **fields}
            )
        return False


def main() -> None:
    ToolCallReopensAfterFinalAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
