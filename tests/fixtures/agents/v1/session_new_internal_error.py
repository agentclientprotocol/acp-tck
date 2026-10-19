#!/usr/bin/env python3
"""Non-conforming fixture: advertises no `authMethods` and answers every `session/new` with
`-32603` (Internal error). Fails ACP-SESSION-001, but not ACP-AUTH-005, which only judges
`-32000`.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class SessionNewInternalErrorAgent(ConformingAgent):
    def _handle_new_session(self, msg_id: Any, params: dict[str, Any]) -> None:
        self._error(msg_id, -32603, "Internal error")


def main() -> None:
    SessionNewInternalErrorAgent().run()


if __name__ == "__main__":
    main()
