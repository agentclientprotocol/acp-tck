#!/usr/bin/env python3
"""Non-conforming fixture: its `git_patch` text is wrapped in an email envelope (`From <sha>`, `Subject:`) as `git format-patch` writes it.

FAILs `ACP-PATCH-215` (the text begins with `diff --git `). The header paths are absolute and match
the `changes` entry, so `ACP-PATCH-214` PASSes.

`_send_rich_turn_updates` is overridden outright, so the other patch rows SKIP "no <variant>
observed" and nothing else FAILs.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class GitPatchEmailEnvelopeAgent(ConformingAgent):
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
                            "text": "From 0123456789abcdef Mon Sep 17 00:00:00 2001\nSubject: [PATCH] edit\n\n"
                            "diff --git /tmp/a.txt /tmp/a.txt\n--- /tmp/a.txt\n+++ /tmp/a.txt\n"
                            "@@ -1 +1 @@\n-old\n+new\n",
                        },
                    }
                ],
            },
        )


def main() -> None:
    GitPatchEmailEnvelopeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
