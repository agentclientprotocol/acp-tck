#!/usr/bin/env python3
"""Non-conforming (ADVISORY-only) fixture: answers a request naming an unknown session with
`-32602` (Invalid params) instead of `-32002` with `data.sessionId`. Trips only ACP-ERROR-003.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from _base import ConformingAgent  # noqa: E402


class UnknownSessionWrongCodeAgent(ConformingAgent):
    def _unknown_session(self, msg_id: Any, session_id: Any) -> None:
        self._error(msg_id, -32602, f"Invalid params: unknown sessionId {session_id!r}")


def main() -> None:
    UnknownSessionWrongCodeAgent(agent_name="tck-fixture-unknown-session-wrong-code").run()


if __name__ == "__main__":
    main()
