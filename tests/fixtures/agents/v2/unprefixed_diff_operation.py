#!/usr/bin/env python3
"""Non-conforming fixture: sends a `tool_call_update` with `diff` content whose change `operation`
is an unrecognized value that does not begin with `_` (`"teleport"`).

FAILs `ACP-ENUM-201` only: `DiffChange`'s `other` branch requires just a string `operation`, so
`ACP-SCHEMA-001` does not cascade (`tool-calls.mdx:685-686`).
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnprefixedDiffOperationAgent(ConformingAgent):
    def _mid_turn_action(self, session_id: Any) -> bool:
        self._send_update(
            session_id,
            {
                "sessionUpdate": "tool_call_update",
                "toolCallId": "tool-diff-1",
                "title": "Editing a file",
                "content": [
                    {"type": "diff", "changes": [{"operation": "teleport", "path": "/tmp/a.txt"}]}
                ],
            },
        )
        return False  # fire-and-forget: finish the turn immediately, in the same call


def main() -> None:
    UnprefixedDiffOperationAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
