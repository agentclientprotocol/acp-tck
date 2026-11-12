#!/usr/bin/env python3
"""Non-conforming fixture: sends a `tool_call_content_chunk` whose single `content` object has an
unrecognized `type` that does not begin with `_` (`"sorcery"`).

FAILs `ACP-ENUM-201` only: the schema's `ToolCallContent` `other` branch accepts any string
`type`, so `ACP-SCHEMA-001` does not cascade. Guards the chunk's `content` being one object, not
an array (`#/$defs/ToolCallContentChunk/properties/content`).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnprefixedChunkContentTypeAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_content_chunk",
                "toolCallId": "tool-chunk-1",
                "content": {"type": "sorcery"},
            },
        )
        return False  # fire-and-forget: finish the turn immediately, in the same call


def main() -> None:
    UnprefixedChunkContentTypeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
