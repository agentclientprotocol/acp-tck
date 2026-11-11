#!/usr/bin/env python3
"""Non-conforming fixture: sends a `session/request_permission` request naming the new session
before the `session/new` response, when the client cannot yet show it (session-setup.mdx:103).
FAILs exactly `ACP-SESSION-206` (ADVISORY). The request is never awaited.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class PermissionBeforeNewResponseAgent(ConformingAgent):
    def _before_new_response(self, session_id: str) -> None:
        self._write(
            {
                "jsonrpc": "2.0",
                "id": "early-perm-1",
                "method": "session/request_permission",
                "params": {
                    "sessionId": session_id,
                    "title": "Allow this action?",
                    "options": [{"optionId": "allow-once", "name": "Allow", "kind": "allow_once"}],
                },
            }
        )


def main() -> None:
    PermissionBeforeNewResponseAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
