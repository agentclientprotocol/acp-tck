#!/usr/bin/env python3
"""Non-conforming fixture: `session/new` rejects a relative `cwd` with `-32600` (Invalid Request)
instead of `-32602` (session-setup.mdx:524). The rejection itself is right, so `ACP-SESSION-204`
PASSes. FAILs exactly `ACP-SESSION-209` (ADVISORY).
"""

import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class NewRelativeCwdWrongCodeAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        cwd = params.get("cwd")
        if isinstance(cwd, str) and not os.path.isabs(cwd):
            self._error(msg_id, -32600, "Invalid request: cwd must be an absolute path")
            return
        super()._handle_new_session(msg_id, params)


def main() -> None:
    NewRelativeCwdWrongCodeAgent(capabilities={"session": {}}).run()


if __name__ == "__main__":
    main()
