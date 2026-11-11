#!/usr/bin/env python3
"""Non-conforming fixture: the first report of its tool call is a `tool_call_content_chunk`,
which creates the tool call without a title (tool-calls.mdx:198-200); only the
`tool_call_update` that follows carries one. The title SHOULD be on the first report
(tool-calls.mdx:41-43): FAILs exactly `ACP-PATCH-208`. The tool call still ends `completed`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ToolCallChunkFirstAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._tool_call_count += 1
        tool_call_id = f"tool-chunk-{self._tool_call_count:04d}"
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_content_chunk",
                "toolCallId": tool_call_id,
                "content": {"type": "content", "content": {"type": "text", "text": "partial"}},
            },
        )
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": tool_call_id,
                "title": "Reading a file",
                "status": "completed",
            },
        )
        return False


def main() -> None:
    ToolCallChunkFirstAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
