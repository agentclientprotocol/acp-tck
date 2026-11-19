#!/usr/bin/env python3
"""Non-conforming fixture: its `git_patch` header lines use Git's default `a/` and `b/` prefixes instead of the absolute `changes` path.

FAILs `ACP-PATCH-214` (every `git_patch` header path is absolute and matches a `changes` entry).
The patch text still starts with `diff --git `, so `ACP-PATCH-215` PASSes.

`_send_rich_turn_updates` is overridden outright, so the other patch rows SKIP "no <variant>
observed" and nothing else FAILs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class GitPatchAbPrefixAgent(ConformingAgent):
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
                        "changes": [{"operation": "modify", "path": "/tmp/a.txt", "fileType": "text"}],
                        "patch": {
                            "format": "git_patch",
                            "text": "diff --git a/tmp/a.txt b/tmp/a.txt\n--- a/tmp/a.txt\n+++ b/tmp/a.txt\n"
                            "@@ -1 +1 @@\n-old\n+new\n",
                        },
                    }
                ],
            },
        )


def main() -> None:
    GitPatchAbPrefixAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
