#!/usr/bin/env python3
"""Non-conforming fixture: `session/list` rejects a relative `cwd` filter with `-32600` (Invalid
Request) instead of `-32602` (session-list.mdx:64-65). The rejection itself is right, so
`ACP-LIST-205` PASSes. FAILs exactly `ACP-LIST-207` (ADVISORY).
"""

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class ListRelativeCwdWrongCodeAgent(ConformingAgent):
    def _handle_list_sessions(self, msg_id: Any, params: dict[str, Any]) -> None:
        cwd = params.get("cwd")
        if isinstance(cwd, str) and not os.path.isabs(cwd):
            self._error(msg_id, -32600, "Invalid request: cwd filter must be absolute")
            return
        super()._handle_list_sessions(msg_id, params)


def main() -> None:
    ListRelativeCwdWrongCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
