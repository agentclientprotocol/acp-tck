#!/usr/bin/env python3
"""Non-conforming fixture: its tool call advertises `capabilities.cancel` while `in_progress`,
then reports `completed` without clearing `capabilities`, so the final tool call still
advertises `cancel` (a nullable patch: omitted leaves it unchanged). The agent SHOULD stop
advertising `cancel` once the tool call is final (tool-calls.mdx:440): FAILs exactly
`ACP-PATCH-212`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class AdvertisesCancelAfterFinalAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._tool_call_count += 1
        tool_call_id = f"tool-cancel-{self._tool_call_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Running a watcher",
                "status": "in_progress",
                "capabilities": {"cancel": {}},
            },
        )
        self._send_update(
            session_id,
            {"sessionUpdate": "tool_call_update", "toolCallId": tool_call_id, "status": "completed"},
        )
        return False


def main() -> None:
    AdvertisesCancelAfterFinalAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
