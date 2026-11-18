#!/usr/bin/env python3
"""Non-conforming fixture: its `diff` content has a `changes[].path` that is relative.

FAILs `ACP-PATCH-213` (each `changes[].path` is an absolute native path). The diff is schema-valid
-- `AbsolutePath` is a bare string in the schema -- and carries no patch text.

`_send_rich_turn_updates` is overridden outright, so the other patch rows SKIP "no <variant>
observed" and nothing else FAILs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class RelativeDiffPathAgent(ConformingAgent):
    def _send_rich_turn_updates(self, session_id: Any) -> None:
        self._tool_call_count += 1
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": f"tool-{self._tool_call_count:04d}",
                "title": "Editing a file",
                "kind": "edit",
                "status": "completed",
                "content": [
                    {
                        "type": "diff",
                        "changes": [{"operation": "modify", "path": "src/a.txt", "fileType": "text"}],
                    }
                ],
            },
        )


def main() -> None:
    RelativeDiffPathAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
